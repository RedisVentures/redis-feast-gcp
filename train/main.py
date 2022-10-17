

import logging
import pandas as pd
import warnings
warnings.filterwarnings('ignore')

from feast import FeatureStore
from datetime import timedelta
from sklearn.metrics import mean_absolute_error
from sklearn.preprocessing import OrdinalEncoder
from xgboost import XGBRegressor
from sklearn.pipeline import make_pipeline
from sklearn.compose import (
    make_column_transformer,
    make_column_selector
)
from sklearn.preprocessing import OrdinalEncoder

from feature_store.repo import config
from feature_store.utils import (
    ModelRepo,
    DataFetcher,
    file
)

# Setup logger
logging.basicConfig(
    filename="info.log",
    level=logging.INFO,
    format="%(asctime)s:%(levelname)7s:%(filename)25s"
    ":%(lineno)3s %(funcName)30s(): %(message)s",
)
logging.getLogger().addHandler(logging.StreamHandler())


def train_test_split(
    data: pd.DataFrame,
    n: int,
    timestamp_col: str,
    by: str = "week"
):
    """
    Split a timeseries dataset into train/test sets by date.

    Args:
        data (pd.DataFrame): _description_
        n (int): _description_
        timestamp_col (str): _description_
        by (str, optional): _description_. Defaults to "week".

    Raises:
        ValueError: If "by" arg is not one of "week" or "day".
    """
    if by == "week":
        delta = timedelta(weeks=n)
    elif by == "day":
        delta == timedelta(days=n)
    else:
        raise ValueError("'by' must be one of 'week' or day'")
    # Split the data
    split_point = data[timestamp_col].max() - delta
    train = data[data[timestamp_col] <= split_point]
    test = data[data[timestamp_col] > split_point]
    train.drop(timestamp_col, axis=1, inplace=True)
    test.drop(timestamp_col, axis=1, inplace=True)
    logging.info(f"Training Results: {len(train)} samples in the training set")
    return train, test

def xgboost_train(train: pd.DataFrame):
    """
    Train an XGBoost model along with an Ordinal Encoder and wrap
    into a Pipeline object.

    Args:
        train (pd.DataFrame): Training DataFrame.

    Returns:
        model: The trained pipeline model.
    """
    # split into input and output columns
    trainX, trainy = train.iloc[:, :-1], train.iloc[:, -1]

    # make model
    ordinal_encoder = make_column_transformer(
        (
            OrdinalEncoder(dtype=int),
            make_column_selector(pattern="state"),
        ),
        remainder="passthrough",
    )
    model = make_pipeline(
        ordinal_encoder,
        XGBRegressor(
            random_state=42,
            objective="count:poisson",
            tree_method="hist",
            enable_categorical=True,
            n_estimators=250,
            max_depth=4
        )
    )
    model.fit(trainX, trainy)
    return model

def train_validate(
    data: pd.DataFrame,
    n_test_weeks: int,
    timestamp_column: str
):
    """
    Train model on data subset and validate on a holdout set.

    Args:
        data (pd.DataFrame): Historical training data to train the model.
        n_test_weeks (int): Number of weeks of data to use for testing.
        timestamp_column (str): DataFrame column name that contains the timestamp.
    """
    # split dataset by week
    train, test = train_test_split(
        data=data,
        n=n_test_weeks,
        timestamp_col=timestamp_column
    )
    testX, testy = test.iloc[:, :-1], test.iloc[:, -1]
    # train
    model = xgboost_train(train)
    # predict
    predictions = model.predict(testX)
    error = mean_absolute_error(testy, predictions)
    return error, testy.to_numpy(), predictions, model

def train(data_fetcher: DataFetcher):
    """
    Train the vaccine demand forecast model using training data served
    from Feast offline store.
    """
    logging.info("Fetching training data")
    timestamp_column = "event_timestamp"
    ds = data_fetcher.get_training_data(
        entity_query=f"""
            select
                state,
                date as {timestamp_column}
            from
                {config.BIGQUERY_DATASET_NAME}.{config.WEEKLY_VACCINATIONS_TABLE}
        """
    )

    # Clean up any nulls and sort
    ds.dropna(inplace=True)
    ds.sort_values([timestamp_column, 'state'], axis=0, inplace=True)

    # Create initial model
    mae, y, yhat, model = train_validate(ds, 1, timestamp_column)

    # Report error
    logging.info(f"Training Results: Number of Samples in Test Set -- {len(yhat)}")
    logging.info(f"Training Results: Mean Absolute Error (MAE) -- {mae}")

    # Train final model
    model = xgboost_train(ds.drop(timestamp_column, axis=1))
    return model

def main():
    # Init feature store and data fetcher
    logging.info("Loading feature store and data fetcher")
    repo_config = file.fetch_pkl_frm_gcs(
        remote_filename=config.REPO_CONFIG,
        bucket_name=config.BUCKET_NAME
    )
    fs = FeatureStore(config=repo_config)
    data_fetcher = DataFetcher(fs)

    # Train
    model = train(data_fetcher)

    # Save model
    model_repo = ModelRepo.from_config(config)
    new_version = model_repo.save_version(model)

    logging.info(f"Saved model version {new_version}")
    logging.info("Done")


if __name__ == "__main__":
    main()