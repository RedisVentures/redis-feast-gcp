import os
import pickle

from utils import file


PROJECT_ID = os.environ["PROJECT_ID"]
GOOGLE_APPLICATION_CREDENTIALS = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
REDIS_CONNECTION_STRING = os.getenv("REDIS_CONNECTION_STRING", "localhost:6379")
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", "")
BUCKET_NAME = os.getenv("BUCKET_NAME", "gcp-feast-demo")
REPO_CONFIG = os.getenv("REPO_CONFIG", "data/repo_config.pkl")
BIGQUERY_DATASET_NAME = os.getenv("BIGQUERY_DATASET_NAME", "gcp_feast_demo")
VACCINE_SEARCH_TRENDS_TABLE = os.getenv("VACCINE_SEARCH_TRENDS_TABLE", "vaccine_search_trends")
WEEKLY_VACCINATIONS_TABLE = os.getenv("WEEKLY_VACCINATIONS_TABLE", "us_weekly_vaccinations")
DAILY_VACCINATIONS_CSV_URL = os.getenv("DAILY_VACCINATIONS_CSV_URL", "https://raw.githubusercontent.com/owid/covid-19-data/master/public/data/vaccinations/us_state_vaccinations.csv")




