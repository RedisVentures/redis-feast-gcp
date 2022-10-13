import pandas as pd

from feast import FeatureStore

from typing import Optional
from repo.config import (
    BIGQUERY_DATASET_NAME,
    WEEKLY_VACCINATIONS_TABLE
)


class DataFetcher(object):
    serving_features = "serving_vaccine_features"
    training_features = "training_vaccine_features"

    def __init__(self, fs: FeatureStore):
        """
        DataFetcher is a generic helper class to abstract the fetching of
        data from the offline and online ML feature sources a la Feast.

        Args:
            fs (FeatureStore): Feast FeatureStore object.
        """
        self._fs = fs
        self.serving_feature_svc = self._fs.get_feature_service(self.serving_features)
        self.training_feature_svc = self._fs.get_feature_service(self.training_features)

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
            assert not features.isnull().sum(axis=0)
            return features
        except Exception as why:
            print(why)

    def get_training_data(
        self,
        entity_df: Optional[pd.DataFrame] = None
    ) -> pd.DataFrame:
        """
        Fetch point-in-time correct ML Features from the
        offline data source.

        Returns:
            pd.DataFrame: DataFrame consisting of historical training data.
        """
        try:
            if entity_df:
                return self._fs.get_historical_features(
                    features=self.training_feature_svc,
                    entity_df=entity_df
                ).to_df()
            else:
                # Otherwise query the offline source of record
                return self._fs.get_historical_features(
                    features=self.training_feature_svc,
                    entity_df=f"""
                        select
                            state,
                            date as event_timestamp
                        from
                            {BIGQUERY_DATASET_NAME}.{WEEKLY_VACCINATIONS_TABLE}
                    """
                ).to_df()
        except Exception as why:
            print(why)
