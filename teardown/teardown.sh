# Cleanup BigQuery
bq rm -t -f $config.BIGQUERY_DATASET_NAME'.'$config.WEEKLY_VACCINATIONS_TABLE
bq rm -t -f $config.BIGQUERY_DATASET_NAME'.'$config.VACCINE_SEARCH_TRENDS_TABLE
bq rm -r -f -d $config.BIGQUERY_DATASET_NAME

# Cleanup Cloud Function and Scheduler
gcloud functions delete feast-update-features --quiet
gcloud scheduler jobs delete feast-daily-job --project $PROJECT_ID --location us-east1

# Teardown Feast
echo "Tearing down Feast infrastructure"
python teardown.py