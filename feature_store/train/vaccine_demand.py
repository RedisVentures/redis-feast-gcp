import pickle

from repo import config
from google.cloud import storage
from datetime import (
    datetime,
    timedelta
)
from feast import (
    RepoConfig,
    FeatureStore
)


class VaccineDemand:

    def __init__(
        self,
        repo_config: RepoConfig,
        feature_service: str,
        model_path: str,
        cols: list
    ):
        self._store = FeatureStore(config=repo_config)
        self.serving_features = self._store.get_feature_service(feature_service)
        self.cols = cols
        self._read_model(str(model_path))

    def _read_model(self, model_path: str):
        # TODO - load model from cloud storage?
        with open(str(model_path), "rb") as f:
            self._model = pickle.load(f)

    def online_predict(self, state: str):
        # Lookup from Redis
        features = self._store.get_online_features(
            features=self.serving_features,
            entity_rows=[{"state": state}]
        ).to_df()
        return self._predict(features[self.cols])

    def offline_predict(self, state: str):
        entity_df = pd.DataFrame.from_dict(
            {
                "state": [state],
                "event_timestamp": [datetime.now() - timedelta(days=2)]
            }
        )
        # Fetch from BigQuery
        features = self._store.get_historical_features(
            entity_df=entity_df,
            features=self.serving_features
        ).to_df()
        return self._predict(features[self.cols])

    def _predict(self, features):
        # Feed to the model
        res = self._model.predict(features)
        # Return
        return res[0]