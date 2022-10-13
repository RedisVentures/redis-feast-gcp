import os
import pickle
from google.cloud import storage


PROJECT_ID = os.environ["PROJECT_ID"]
GOOGLE_APPLICATION_CREDENTIALS = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
REDIS_CONNECTION_STRING = os.getenv("REDIS_CONNECTION_STRING", "localhost:6379")
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", "")
BUCKET_NAME = os.getenv("BUCKET_NAME", "gcp-feast-demo")
REPO_CONFIG = os.getenv("REPO_CONFIG", "data/repo_config.pkl")
BIGQUERY_DATASET_NAME = os.getenv("BIGQUERY_DATASET_NAME", "gcp_feast_demo")
VACCINE_SEARCH_TRENDS_TABLE = os.getenv("VACCINE_SEARCH_TRENDS_TABLE", "vaccine_search_trends")
WEEKLY_VACCINATIONS_TABLE = os.getenv("WEEKLY_VACCINATIONS_TABLE", "us_weekly_vaccinations")


def _get_blob():
    storage_client = storage.Client()
    bucket = storage_client.bucket(BUCKET_NAME)
    blob = bucket.blob(REPO_CONFIG)
    return blob

def load_repo_config():
    # Get the blob and download
    blob = _get_blob()
    pickle_in = blob.download_as_string()
    repo_config = pickle.loads(pickle_in)
    print("Repo configuration loaded from cloud storage")
    return repo_config

def write_repo_config(repo_config):
    # Get the blob and upload
    blob = _get_blob()
    pickle_out = pickle.dumps(repo_config)
    blob.upload_from_string(pickle_out)
