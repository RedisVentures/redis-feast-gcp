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

# Teardown Vertex AI Stuff
ENDPOINT_NAME=vaccine-predictor-endpoint
DEPLOYED_MODEL_NAME=vaccine-predictor
ARTIFACT_REPOSITORY_NAME=nvidia-triton

ENDPOINT_ID=$(gcloud ai endpoints list \
   --region=$GCP_REGION \
   --filter=display_name=$ENDPOINT_NAME \
   --format="value(name)")

DEPLOYED_MODEL_ID=$(gcloud ai endpoints describe $ENDPOINT_ID \
   --region=$GCP_REGION \
   --format="value(deployedModels.id)")

gcloud ai endpoints undeploy-model $ENDPOINT_ID \
  --region=$GCP_REGION \
  --deployed-model-id=$DEPLOYED_MODEL_ID

gcloud ai endpoints delete $ENDPOINT_ID \
   --region=$GCP_REGION \
   --quiet

MODEL_ID=$(gcloud ai models list \
--region=$GCP_REGION \
--filter=display_name=$DEPLOYED_MODEL_NAME \
--format="value(name)")

gcloud ai models delete $MODEL_ID \
   --region=$GCP_REGION \
   --quiet

gcloud artifacts repositories delete $ARTIFACT_REPOSITORY_NAME \
  --location=$GCP_REGION \
  --quiet

# Teardown Feast
echo "Tearing down Feast infrastructure"
python setup/teardown.py