

import pandas as pd
import tempfile
import shutil
import warnings
warnings.filterwarnings('ignore')

from datetime import timedelta
from xgboost import XGBRegressor
from feature_store.repo import config
from feature_store.utils import (
    TritonGCSModelRepo,
    DataFetcher,
    logger,
    storage
)


# Setup logger
logging = logger.get_logger()

def model_config() -> str:
    # TODO - make these more configurable?
    return f"""name: "{config.MODEL_NAME}"
backend: "fil"
max_batch_size: 8192
input [
 {{
    name: "input__0"
    data_type: TYPE_FP32
    dims: [ 9 ]
  }}
]
output [
 {{
    name: "output__0"
    data_type: TYPE_FP32
    dims: [ 1 ]
  }}
]
instance_group [{{ kind: KIND_CPU }}]
parameters [
  {{
    key: "model_type"
    value: {{ string_value: "xgboost_json" }}
  }},
  {{
    key: "output_class"
    value: {{ string_value: "false" }}
  }},
  {{
    key: "storage_type"
    value: {{ string_value: "AUTO" }}
  }},
  {{
    key: "use_experimental_optimizations"
    value: {{ string_value: "true" }}
  }}
]

dynamic_batching {{
  max_queue_delay_microseconds: 100
}}"""

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
    train.drop(columns=[timestamp_col, "state"], axis=1, inplace=True)
    test.drop(columns=[timestamp_col, "state"], axis=1, inplace=True)
    logging.info(f"Training Results: {len(train)} samples in the training set")
    return train, test

def xgboost_train(train: pd.DataFrame, test: pd.DataFrame = None):
    """
    Train an XGBoost model along with an Ordinal Encoder and wrap
    into a Pipeline object.

    Args:
        train (pd.DataFrame): Training DataFrame.

    Returns:
        model: The trained pipeline model.
    """
    print(train.head())
    print(train.columns)
    # split into input and output columns
    trainX, trainy = train.iloc[:, :-1], train.iloc[:, -1]

    # make xgboost regressor model
    model = XGBRegressor(
        random_state=42,
        objective="count:poisson",
        tree_method="hist",
        n_estimators=250,
        max_depth=4
    )
    if test:
        testX, testy = test.iloc[:, :-1], test.iloc[:, -1]
        return model.fit(
            trainX,
            trainy,
            eval_set=[(testX, testy)]
        )
    return model.fit(trainX, trainy)

def train(data_fetcher: DataFetcher):
    """
    Train the vaccine demand forecast model using training data served
    from Feast offline store.
    """
    logging.info("Fetching training data")
    timestamp_column = "event_timestamp"
    n_test_weeks = 1
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

    # Train/Test split for validation
    train, test = train_test_split(
        data=ds,
        n=n_test_weeks,
        timestamp_col=timestamp_column
    )

    # Train initial model
    model = xgboost_train(train, test)
    logging.info(f"Initial model training complete. Validation loss observed.")

    # Train final model
    model = xgboost_train(ds.drop(columns=[timestamp_column, "state"], axis=1))
    logging.info("Final model trained.")
    return model

def main():
    # Init feature store and data fetcher
    logging.info("Loading feature store and data fetcher")

    # Create FeatureStore
    logging.info("Fetching feature store")
    store = storage.get_feature_store(
        config_path=config.REPO_CONFIG,
        bucket_name=config.BUCKET_NAME
    )
    data_fetcher = DataFetcher(store)

    # Setup model repo
    model_repo = TritonGCSModelRepo(
        bucket_name=config.BUCKET_NAME,
        model_name=config.MODEL_NAME,
        model_filename=config.MODEL_FILENAME
    )

    # Train
    model = train(data_fetcher)
    tmp_dir = tempfile.mkdtemp()
    tmp_model_path = f"{tmp_dir}/xgboost.model"
    model.save_model(tmp_model_path)

    # Save model
    new_version = model_repo.save_version(model_path=tmp_model_path)
    shutil.rmtree(tmp_dir)
    logging.info("Done")


if __name__ == "__main__":
    main()