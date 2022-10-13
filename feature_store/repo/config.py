import os


PROJECT_ID = os.environ["PROJECT_ID"]
GOOGLE_APPLICATION_CREDENTIALS = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
REDIS_CONNECTION_STRING = os.getenv("REDIS_CONNECTION_STRING", "localhost:6379")
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", "")
BUCKET_NAME = os.getenv("BUCKET_NAME", "gcp-feast-demo")
REPO_CONFIG = os.getenv("REPO_CONFIG", "data/repo_config.pkl")
BIGQUERY_DATASET_NAME = os.getenv("BIGQUERY_DATASET_NAME", "gcp_feast_demo")
VACCINE_SEARCH_TRENDS_TABLE = os.getenv("VACCINE_SEARCH_TRENDS_TABLE", "vaccine_search_trends")
WEEKLY_VACCINATIONS_TABLE = os.getenv("WEEKLY_VACCINATIONS_TABLE", "us_weekly_vaccinations")


def load_repo_config():
    import pickle
    from google.cloud import storage

    def _get_blob():
        storage_client = storage.Client()
        bucket = storage_client.bucket(BUCKET_NAME)
        blob = bucket.blob(REPO_CONFIG)
        return blob

    # Get the blob and download
    blob = _get_blob()
    pickle_in = blob.download_as_string()
    repo_config = pickle.loads(pickle_in)
    print("Repo configuration loaded from cloud storage")
    return repo_config
