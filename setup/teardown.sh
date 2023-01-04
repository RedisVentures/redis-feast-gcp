# Auth
gcloud auth activate-service-account $SERVICE_ACCOUNT_EMAIL \
    --key-file=$GOOGLE_APPLICATION_CREDENTIALS \
    --project=$PROJECT_ID

# Cleanup BigQuery
bq rm -t -f "gcp_feast_demo.vaccine_search_trends"
bq rm -t -f "gcp_feast_demo.us_weekly_vaccinations"
bq rm -r -f -d "gcp_feast_demo"

# Cleanup Cloud Function and Scheduler
gcloud functions delete feast-update-features --quiet
gcloud scheduler jobs delete feast-daily-job \
    --project=$PROJECT_ID \
    --location=$GCP_REGION \
    --quiet

# Teardown Feast
echo "Tearing down Feast infrastructure"
python teardown/teardown.py