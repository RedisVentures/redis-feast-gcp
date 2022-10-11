import os

PROJECT_ID = os.environ["PROJECT_ID"]
GOOGLE_APPLICATION_CREDENTIALS = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
REDIS_CONNECTION_STRING = os.getenv("REDIS_CONNECTION_STRING", "localhost:6379")
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", "")
BUCKET_NAME = os.getenv("BUCKET_NAME", "gcp-feast-demo")
GCP_REGION = os.getenv("GCP_REGION", "us-east1")
FEAST_PROJECT = os.getenv("FEAST_PROJECT", "feature_store")
REPO_CONFIG = "data/repo_config.pkl"
BIGQUERY_DATASET_NAME = "gcp_feast_demo"
MODEL_NAME = "vaccine_demand"
VACCINE_SEARCH_TRENDS_TABLE = "vaccine_search_trends"
WEEKLY_VACCINATIONS_TABLE = "us_weekly_vaccinations"
DAILY_VACCINATIONS_CSV_URL = "https://raw.githubusercontent.com/owid/covid-19-data/master/public/data/vaccinations/us_state_vaccinations.csv"
