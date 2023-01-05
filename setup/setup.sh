# Auth
gcloud auth activate-service-account $SERVICE_ACCOUNT_EMAIL \
    --key-file=$GOOGLE_APPLICATION_CREDENTIALS \
    --project=$PROJECT_ID

# Setup GCP Project Name
echo project_id = $PROJECT_ID > ~/.bigqueryrc

# Enable APIs
echo "\nEnabling GCP APIs"
gcloud services enable artifactregistry.googleapis.com
gcloud services enable ml.googleapis.com
gcloud services enable aiplatform.googleapis.com
gcloud services enable bigquery.googleapis.com
gcloud services enable cloudscheduler.googleapis.com
gcloud services enable cloudfunctions.googleapis.com

# Create Cloud Storage Bucket
echo "\nCreating cloud storage bucket"
gsutil ls -b gs://$BUCKET_NAME || gsutil mb gs://$BUCKET_NAME

# Create BigQuery Dataset
echo "\nCreating biqquery dataset"
bq --location=us mk --dataset $PROJECT_ID:gcp_feast_demo

# Deploy cloud Function
echo "\nCreating cloud function for materialization"
mv setup/materialize.py .
gcloud functions deploy feast-update-features \
    --source=./ \
    --ignore-file=./setup/.gcloudignore \
    --entry-point=main \
    --memory=1024MB \
    --allow-unauthenticated \
    --runtime python38 \
    --trigger-resource feast-schedule \
    --trigger-event google.pubsub.topic.publish \
    --timeout 540s \
    --set-build-env-vars GOOGLE_FUNCTION_SOURCE="materialize.py" \
    --set-env-vars PROJECT_ID=$PROJECT_ID

# Create Cloud Scheduler Job
echo "\nCreating cloud scheduler task for triggering materialization daily"
gcloud scheduler jobs create pubsub feast-daily-job \
    --location $GCP_REGION \
    --schedule "0 22 * * *" \
    --topic feast-schedule \
    --message-body "This job schedules feature materialization once a day."

# Create & Apply the Feature Store
echo "\nCreating Feature Store"
python setup/create.py
python setup/apply.py

## Create Artifact Registry
echo "\nCreating GCP Artifact Repository for Custom Triton Serving Container"
ARTIFACT_REPOSITORY_NAME=nvidia-triton

gcloud artifacts repositories create $ARTIFACT_REPOSITORY_NAME \
  --repository-format=docker \
  --location=$GCP_REGION \
  --description="NVIDIA Triton Docker repository"
