from feature_store.repo import config
from feature_store.utils import logger, storage


if __name__ == "__main__":
    # Setup logging
    logging = logger.get_logger()

    # Create FeatureStore
    logging.info("Fetching feature store")
    store = storage.get_feature_store(
        config_path=config.REPO_CONFIG, bucket_name=config.BUCKET_NAME
    )

    # Teardown
    logging.info("Tearing down feature store")
    store.teardown()

    logging.info("Done")
