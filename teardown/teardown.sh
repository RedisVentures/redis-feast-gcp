# Auth
gcloud auth activate-service-account $SERVICE_ACCOUNT_EMAIL \
    --key-file=$GOOGLE_APPLICATION_CREDENTIALS \
    --project=$PROJECT_ID

# Cleanup BigQuery
bq rm -t -f $BIGQUERY_DATASET_NAME'.'$WEEKLY_VACCINATIONS_TABLE
bq rm -t -f $BIGQUERY_DATASET_NAME'.'$VACCINE_SEARCH_TRENDS_TABLE
bq rm -r -f -d $BIGQUERY_DATASET_NAME

# Cleanup Cloud Function and Scheduler
gcloud functions delete feast-update-features --quiet
gcloud scheduler jobs delete feast-daily-job \
    --project=$PROJECT_ID \
    --location=$GCP_REGION

# Teardown Feast
echo "Tearing down Feast infrastructure"
python teardown/teardown.py