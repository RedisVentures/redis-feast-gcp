from feast import RepoConfig
from google.cloud import bigquery
from feature_store.utils import (
    logger,
    storage
)
from feature_store.repo import (
    config,
    features
)


if __name__ == "__main__":
    # Setup logger
    logging = logger.get_logger()

    # Create a feature store repo config
    logging.info("Creating Feast repo configuration")
    repo_config = RepoConfig(
        project=config.FEAST_PROJECT,
        # Cloud Storage Blob for the Registry
        registry=f"gs://{config.BUCKET_NAME}/data/registry.db",
        # Google Cloud Project -- GCP
        provider="gcp",
        # Redis Enterprise as the Online Store
        online_store={
            "type": "redis",
            "connection_string": f"{config.REDIS_CONNECTION_STRING},password={config.REDIS_PASSWORD}"
        },
        entity_key_serialization_version=2
    )

    # Host the config in cloud storage
    logging.info("Uploading repo config to cloud storage bucket")
    storage.upload_pkl(repo_config, config.BUCKET_NAME, config.REPO_CONFIG)

    # Generate initial features data in offline store
    logging.info("Generating initial vaccine features in GCP")
    client = bigquery.Client()

    features.generate_vaccine_counts(
        logging,
        client,
        f"{config.PROJECT_ID}.{config.BIGQUERY_DATASET_NAME}.{config.WEEKLY_VACCINATIONS_TABLE}"
    )

    features.generate_vaccine_search_trends(
        logging,
        client,
        f"{config.PROJECT_ID}.{config.BIGQUERY_DATASET_NAME}.{config.VACCINE_SEARCH_TRENDS_TABLE}"
    )

    logging.info("Done")
