from datetime import datetime
from feature_store.repo import (
    config,
    features
)
from feature_store.utils import (
    logger,
    storage
)


if __name__ == '__main__':
    # Setup logger
    logging = logger.get_logger()

    # Create FeatureStore
    logging.info("Fetching feature store")
    store = storage.get_feature_store(
        config_path=config.REPO_CONFIG,
        bucket_name=config.BUCKET_NAME
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
