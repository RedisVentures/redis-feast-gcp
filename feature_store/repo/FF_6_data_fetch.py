import pandas as pd

import featureform as ff

from typing import Optional

from feature_store.repo import FF_0_config as config


class DataFetcher:
    X_cols = [
        "lag_1_vaccine_interest",
        "lag_2_vaccine_interest",
        "lag_1_vaccine_intent",
        "lag_2_vaccine_intent",
        "lag_1_vaccine_safety",
        "lag_2_vaccine_safety",
        "lag_1_weekly_vaccinations_count",
        "lag_2_weekly_vaccinations_count",
    ]

    y_col = ["weekly_vaccinations_count"]

    # TODO: Replace with Featureform get functions
    def __init__(self, ff):
        serving = ff.ServingClient(host=f"{config.FEATUREFORM_HOST}")

    # TODO: Make this actually work
    def get_online_data(self, **entities) -> pd.DataFrame:
        dataset = serving.training_set("fraud_training", "default")
        return dataset

    # TODO: Make this actually work
    def get_training_data(self) -> pd.DataFrame:
        dataset = serving.training_set("fraud_training", "default")
        return dataset
