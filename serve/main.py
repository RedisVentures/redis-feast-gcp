import os
import ray
import typing as t
import pandas as pd

from datetime import (
    datetime,
    timedelta
)
from fastapi import FastAPI
from feast import FeatureStore
from pydantic import BaseModel
from ray import serve

from feature_store.repo import config
from feature_store.utils import (
    ModelRepo,
    DataFetcher,
    file
)


REMOTE_RAY = os.environ.get("RAY_ADDRESS", None)
if REMOTE_RAY:
    # ray.init(address='auto', namespace="serve")
    # option when using Redis to double as a Ray Cluster metadata
    # store for High Availability (HA) clusters
    ray.init(address='auto', namespace="serve", _redis_password="hello")


app = FastAPI()
serve.start(detached=True)


class PredictionRequest(BaseModel):
    """Vaccine Demand Prediction Request"""
    state: str


@serve.deployment
@serve.ingress(app)
class VaccineDemand:

    def __init__(self):
        """
        Vaccine Demand Model. Forecast the next week's vaccine doses
        administered by US state.
        """
        self._fs = self._load_store()
        self._model = self._load_model()
        self._data_fetcher = DataFetcher(self._fs)

    def _load_store() -> FeatureStore:
        repo_config = file.fetch_pkl_frm_gcs(
            remote_filename=config.REPO_CONFIG,
            bucket_name=config.BUCKET_NAME
        )
        return FeatureStore(config=repo_config)

    def _load_model():
        model_repo = ModelRepo.from_config(config)
        return model_repo.fetch_latest()

    @app.get("/demand")
    def predict(self, request: PredictionRequest):
        features = self._data_fetcher.get_online_data({"state": request.state})
        return self._predict(features)

    @app.get("/demand/offline")
    def offline_predict(self, request: PredictionRequest):
        entity_df = pd.DataFrame.from_dict(
            {
                "state": [request.state],
                "event_timestamp": [datetime.now() - timedelta(days=2)]
            }
        )
        # Fetch from BigQuery
        features = self._data_fetcher.get_training_data(entity_df=entity_df)
        return self._predict(features)

    def _predict(self, features):
        # Feed to the model
        res = self._model.predict(features)
        # Return
        return res[0]


# Deploy
VaccineDemand.options(
    ray_actor_options={
        "runtime_env": {
            "pip": ["feast", "xgboost", "pandas", "scikit-learn", "redis"]
        }
    }
).deploy()