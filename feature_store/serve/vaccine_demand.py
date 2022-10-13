import pandas as pd
from utils import DataFetcher
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
        model,
        repo_config: RepoConfig,
        cols: list
    ):
        self._store = FeatureStore(config=repo_config)
        self._data_fetcher = DataFetcher(self._store)
        self._model = model
        self.cols = cols

    def online_predict(self, state: str):
        features = self._data_fetcher.get_online_data(state=state)
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
