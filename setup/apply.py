from datetime import datetime
from feast import FeatureStore
from feature_store.repo import (
    config,
    features
)
from feature_store.utils import (
    file,
    logger
)


if __name__ == '__main__':
    # Setup logger
    logging = logger.get_logger()

    # Create FeatureStore
    logging.info("Fetching repo config from cloud storage")
    store = FeatureStore(
        config=file.fetch_pkl_frm_gcs(
            remote_filename=config.REPO_CONFIG,
            bucket_name=config.BUCKET_NAME
        )
    )

    # Apply
    logging.info("Applying feature store objects")
    store.apply([
        features.state,
        features.weekly_vaccinations_fv,
        features.vaccine_search_trends_fv,
        features.serving_features,
        features.training_features
    ])

    # Materialize?
    logging.info("Materializing features")
    store.materialize_incremental(datetime.now())

    logging.info("Done")
