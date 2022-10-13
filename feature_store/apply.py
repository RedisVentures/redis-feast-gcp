from datetime import datetime
from repo import features
from repo import config

from feast import FeatureStore


if __name__ == '__main__':

    # Fetch repo config from storage
    repo_config = config.load_repo_config()

    # Create FeatureStore
    store = FeatureStore(config=repo_config)

    # Apply
    print("Applying feature store objects")
    store.apply([
        features.state,
        features.weekly_vaccinations_fv,
        features.vaccine_search_trends_fv,
        features.serving_features,
        features.training_features
    ])

    # Materialize?
    print("Materializing features")
    store.materialize_incremental(datetime.now())
