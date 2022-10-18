from feast import FeatureStore
from feature_store.repo import config
from feature_store.utils import (
    file,
    logger
)


if __name__ == '__main__':
    # Setup logging
    logging = logger.get_logger()

    # Fetch repo config from storage
    logging.info("Fetching repo config from cloud storage")
    repo_config = file.fetch_pkl_frm_gcs(
        remote_filename=config.REPO_CONFIG,
        bucket_name=config.BUCKET_NAME
    )

    # Create FeatureStore
    store = FeatureStore(config=repo_config)

    # Teardown
    logging.info("Tearing down feature store")
    store.teardown()

    logging.info("Done")