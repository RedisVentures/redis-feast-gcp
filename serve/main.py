import uvicorn
import pandas as pd

from datetime import (
    datetime,
    timedelta
)
from fastapi import FastAPI
from pydantic import BaseModel

from feature_store.repo import config
from feature_store.utils import (
    ModelRepo,
    DataFetcher,
    logger,
    storage
)


fs = storage.get_feature_store(
    config_path=config.REPO_CONFIG,
    bucket_name=config.BUCKET_NAME
)
data_fetcher = DataFetcher(fs)
logging = logger.get_logger()
app = FastAPI()


class PredictionRequest(BaseModel):
    """Vaccine Demand Prediction Request"""
    state: str


def load_model():
    logging.info("Fetching model from Redis storage")
    model_repo = ModelRepo.from_config(config)
    return model_repo.fetch_latest()

model = load_model()

@app.get("/predict")
def predict(request: PredictionRequest):
    logging.info(f"Predicting vaccine demand for {request.state}")
    features = data_fetcher.get_online_data(state=request.state)
    return _predict(features)

@app.get("/predict/offline")
def predict_offline(request: PredictionRequest):
    logging.info(f"Predicting vaccine demand for {request.state} with offline data")
    features = data_fetcher.get_training_data(
        entity_df=pd.DataFrame.from_dict(
        {
            "state": [request.state],
            "event_timestamp": [datetime.now() - timedelta(days=2)]
        }
    ))
    return _predict(features)

def _predict(features: pd.DataFrame):
    """
    Perform prediction over the input feature set.

    Args:
        features (pd.DataFrame): DataFrame of ML features pulled from the feature store.
    """
    print(features, flush=True)
    res = model.predict(features)
    return {"result": int(res[0])}


if __name__ == "__main__":

    server_attr = {
        "host": "0.0.0.0",
        "reload": True,
        "port": 8000,
        "workers": 1
    }

    uvicorn.run("main:app", **server_attr)