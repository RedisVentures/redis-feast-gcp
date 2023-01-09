import pandas as pd

from feast import FeatureStore
from typing import Optional


class DataFetcher:
    X_cols = [
        'lag_1_vaccine_interest',
        'lag_2_vaccine_interest',
        'lag_1_vaccine_intent',
        'lag_2_vaccine_intent',
        'lag_1_vaccine_safety',
        'lag_2_vaccine_safety',
        'lag_1_weekly_vaccinations_count',
        'lag_2_weekly_vaccinations_count'
    ]

    y_col = ['weekly_vaccinations_count']

    def __init__(self, fs: FeatureStore):
        """
        DataFetcher is a generic helper class to abstract the fetching of
        data from the offline and online ML feature sources a la Feast.

        Args:
            fs (FeatureStore): Feast FeatureStore object.
        """
        self._fs = fs
        self.serving_feature_svc = self._fs.get_feature_service("serving_features")
        self.training_feature_svc = self._fs.get_feature_service("training_features")

    def get_online_data(self, **entities) -> pd.DataFrame:
        """
        Fetch ML Features from the online data source.

        Returns:
            pd.DataFrame: DataFrame consisting of the serving feature set.
        """
        try:
            features = self._fs.get_online_features(
                features=self.serving_feature_svc,
                entity_rows=[entities]
            ).to_df()
            return features[self.X_cols]
        except Exception as why:
            print(why)

    def get_training_data(
        self,
        entity_df: Optional[pd.DataFrame] = None,
        entity_query: Optional[str] = None
    ) -> pd.DataFrame:
        """
        Fetch point-in-time correct ML Features from the
        offline data source.

        Args:
            entity_df (pd.DataFrame, optional): DataFrame consisting of entities to include in training set. Default to None.
            entity_query (str, optional): Query string to create entity df from offline data source. Default to None.

        Returns:
            pd.DataFrame: DataFrame consisting of historical training data.
        """
        try:
            if entity_df:
                return self._fs.get_historical_features(
                    features=self.training_feature_svc,
                    entity_df=entity_df
                ).to_df()
            if entity_query:
                # Otherwise query the offline source of record
                return self._fs.get_historical_features(
                    features=self.training_feature_svc,
                    entity_df=entity_query
                ).to_df()
        except Exception as why:
            print(why)
