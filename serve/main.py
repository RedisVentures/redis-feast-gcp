import os
import ray
import pandas as pd

from datetime import (
    datetime,
    timedelta
)
from fastapi import FastAPI
from pydantic import BaseModel
from ray import serve

from feature_store.repo import (
    config,
    features
)
from feature_store.utils import (
    ModelRepo,
    DataFetcher,
    logger
)


REMOTE_RAY = os.environ.get("RAY_ADDRESS", None)
if REMOTE_RAY:
    # ray.init(address='auto', namespace="serve")
    # option when using Redis to double as a Ray Cluster metadata
    # store for High Availability (HA) clusters
    ray.init(address='auto', namespace="serve", _redis_password="hello")


app = FastAPI()
serve.start()

# Setup logger
logging = logger.get_logger()

logging.info("HERE")

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
        self._fs = features.get_feature_store()
        self._model = self._load_model()
        self._data_fetcher = DataFetcher(self._fs)

    def _load_model():
        logging.info("Fetching model from Redis storage")
        model_repo = ModelRepo.from_config(config)
        return model_repo.fetch_latest()

    @app.get("/predict")
    def predict(self, request: PredictionRequest):
        logging.info(f"Predicting vaccine demand for {request.state}")
        features = self._data_fetcher.get_online_data({"state": request.state})
        return self._predict(features)

    @app.get("/predict/offline")
    def predict_offline(self, request: PredictionRequest):
        logging.info(f"Predicting vaccine demand for {request.state} with offline data")
        features = self._data_fetcher.get_training_data(
            entity_df=pd.DataFrame.from_dict(
            {
                "state": [request.state],
                "event_timestamp": [datetime.now() - timedelta(days=2)]
            }
        ))
        return self._predict(features)

    def _predict(self, features: pd.DataFrame):
        """
        Perform prediction over the input feature set.

        Args:
            features (pd.DataFrame): DataFrame of ML features pulled from the feature store.
        """
        res = self._model.predict(features)
        return res[0]


# Deploy
VaccineDemand.options(
    ray_actor_options={
        "runtime_env": {
            "pip": ["feast", "xgboost==1.6.2", "pandas", "scikit-learn==1.1.2", "redis"]
        }
    }
).deploy()