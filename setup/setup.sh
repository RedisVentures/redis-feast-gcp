# Auth
gcloud auth activate-service-account $SERVICE_ACCOUNT_EMAIL \
    --key-file=$GOOGLE_APPLICATION_CREDENTIALS \
    --project=$PROJECT_ID

# Setup GCP Project Name
echo project_id = $PROJECT_ID > ~/.bigqueryrc

# Enable APIs
gcloud services enable artifactregistry.googleapis.com
gcloud services enable ml.googleapis.com
gcloud services enable bigquery.googleapis.com
gcloud services enable cloudbuild.googleapis.com
gcloud services enable cloudscheduler.googleapis.com
gcloud services enable cloudfunctions.googleapis.com

# Create Cloud Storage Bucket
gsutil ls -b gs://$BUCKET_NAME || gsutil mb gs://$BUCKET_NAME

# Create BigQuery Dataset
echo "Creating biqquery dataset"
bq --location=us mk --dataset $PROJECT_ID:gcp_feast_demo

# Deploy cloud Function
echo "Creating cloud function for materialization"
gcloud functions deploy feast-update-features \
    --source=./ \
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
echo "Creating cloud scheduler task for triggering materialization daily"
gcloud scheduler jobs create pubsub feast-daily-job \
    --location $GCP_REGION \
    --schedule "0 22 * * *" \
    --topic feast-schedule \
    --message-body "This job schedules feature materialization once a day."

# Create & Apply the Feature Store
echo "\nCreating FEAST Feature Store"
python setup/create.py
python setup/apply.py

# Setup Vertex AI and Triton
CONTAINER_IMAGE_URI=$GCP_REGION-docker.pkg.dev/$PROJECT_ID/nvidia-triton/vertex-triton-inference
ENDPOINT_NAME=vaccine-predictor-endpoint
DEPLOYED_MODEL_NAME=vaccine-predictor

## Upload Triton Model Repository Contents
gsutil cp -r ./setup/models gs://$BUCKET_NAME/
gsutil rm gs://$BUCKET_NAME/models/ensemble-model/1/.gitkeep

## Create Artifact Registry
gcloud artifacts repositories create nvidia-triton \
  --repository-format=docker \
  --location=$GCP_REGION \
  --description="NVIDIA Triton Docker repository"

## Pull and Upload Triton Image
NGC_TRITON_IMAGE_URI="ghcr.io/redisventures/triton-Python-FIL-server:22.08-py3"
docker pull $NGC_TRITON_IMAGE_URI
docker tag $NGC_TRITON_IMAGE_URI $CONTAINER_IMAGE_URI

gcloud auth configure-docker $GCP_REGION-docker.pkg.dev
docker push $CONTAINER_IMAGE_URI

## Create Vertex AI Model
gcloud ai models upload \
  --region=$GCP_REGION \
  --display-name=$DEPLOYED_MODEL_NAME \
  --container-image-uri=$CONTAINER_IMAGE_URI \
  --artifact-uri=$REGISTRY_URI

## Create Endpoint
gcloud ai endpoints create \
  --region=$GCP_REGION \
  --display-name=$ENDPOINT_NAME

