from feast import RepoConfig
from google.cloud import bigquery

from repo import config
from utils import file
from materialize import (
    generate_vaccine_count_features,
    generate_vaccine_search_features
)


if __name__ == "__main__":
    # Create a feature store repo config
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
    file.upload_pkl_to_gcs(repo_config, config.BUCKET_NAME, config.REPO_CONFIG)

    # GCP BigQuery client
    client = bigquery.Client()

    # Generate Weekly Vaccine Count Features
    generate_vaccine_count_features(
        client,
        f"{config.PROJECT_ID}.{config.BIGQUERY_DATASET_NAME}.{config.WEEKLY_VACCINATIONS_TABLE}"
    )

    # Generate Vaccine Search Features
    generate_vaccine_search_features(
        client,
        f"{config.PROJECT_ID}.{config.BIGQUERY_DATASET_NAME}.{config.VACCINE_SEARCH_TRENDS_TABLE}"
    )
