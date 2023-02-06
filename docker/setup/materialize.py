from datetime import datetime
from google.cloud import bigquery
from feature_store.repo import (
    config,
    features
)
from feature_store.utils import (
    logger,
    storage
)

def materialize_features(logging):
    """
    Incrementally materialize ML features from offline store to online store
    using Feast.
    """
    # Load FeatureStore
    store = storage.get_feature_store(
        config_path=config.REPO_CONFIG,
        bucket_name=config.BUCKET_NAME
    )

    # Materialize Features to Redis
    logging.info("Beginning materialization")
    store.materialize_incremental(end_date=datetime.now())

def main(data, context):
    # Setup logger
    logging = logger.get_logger()

    # Big Query Client
    client = bigquery.Client()

    # Generate Vaccine Count Features
    features.generate_vaccine_counts(
        logging,
        client,
        f"{config.PROJECT_ID}.{config.BIGQUERY_DATASET_NAME}.{config.WEEKLY_VACCINATIONS_TABLE}"
    )
    # Generate Vaccine Search Features
    features.generate_vaccine_search_trends(
        logging,
        client,
        f"{config.PROJECT_ID}.{config.BIGQUERY_DATASET_NAME}.{config.VACCINE_SEARCH_TRENDS_TABLE}"
    )
    # Perform local materialization
    materialize_features(logging)
