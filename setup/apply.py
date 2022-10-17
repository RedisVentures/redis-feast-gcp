from datetime import datetime
from feast import FeatureStore
from repo import (
    config,
    features
)
from utils import file


if __name__ == '__main__':

    # Fetch repo config from storage
    repo_config = file.fetch_pkl_frm_gcs(
        remote_filename=config.REPO_CONFIG,
        bucket_name=config.BUCKET_NAME
    )

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
