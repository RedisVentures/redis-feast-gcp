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

# Setup Vertex AI and Triton
echo "\nUploading Triton Models to Cloud Storage"
CONTAINER_IMAGE_URI=$GCP_REGION-docker.pkg.dev/$PROJECT_ID/$ARTIFACT_REPOSITORY_NAME/vertex-triton-inference
NGC_TRITON_IMAGE_URI=ghcr.io/redisventures/tritonserver-python-fil:22.11-py3
MODEL_STORAGE_URI=gs://$BUCKET_NAME/models

## Upload Triton Model Repository Contents
gsutil -m cp -r ./setup/models gs://$BUCKET_NAME/
gsutil rm $MODEL_STORAGE_URI/ensemble/1/.gitkeep

# Pull and Upload Triton Image
echo "\nPulling Triton Docker Image"
docker pull $NGC_TRITON_IMAGE_URI
docker tag $NGC_TRITON_IMAGE_URI $CONTAINER_IMAGE_URI

echo "\nPushing Triton Docker Image to GCP"
gcloud auth configure-docker $GCP_REGION-docker.pkg.dev --quiet
docker push $CONTAINER_IMAGE_URI

# Create Vertex AI Model
echo "\nCreating Vertex AI Model"
ENDPOINT_NAME=vaccine-predictor-endpoint
DEPLOYED_MODEL_NAME=vaccine-predictor

gcloud ai models upload \
  --region=$GCP_REGION \
  --display-name=$DEPLOYED_MODEL_NAME \
  --container-image-uri=$CONTAINER_IMAGE_URI \
  --artifact-uri=$MODEL_STORAGE_URI \
  --container-env-vars="REDIS_CONNECTION_STRING=$REDIS_CONNECTION_STRING","REDIS_PASSWORD=$REDIS_PASSWORD","PROJECT_ID=$PROJECT_ID","GCP_REGION=$GCP_REGION","BUCKET_NAME=$BUCKET_NAME"

# Create Endpoint
echo "\nCreating Vertex AI Endpoint"
gcloud ai endpoints create \
  --region=$GCP_REGION \
  --display-name=$ENDPOINT_NAME

## Lookup Endpoint and Model IDs
echo "\nDeploying Model to Endpoint"
ENDPOINT_ID=$(gcloud ai endpoints list \
  --region=$GCP_REGION \
  --filter=display_name=$ENDPOINT_NAME \
  --format="value(name)")

MODEL_ID=$(gcloud ai models list \
  --region=$GCP_REGION \
  --filter=display_name=$DEPLOYED_MODEL_NAME \
  --format="value(name)")

# Deploy Model to the Endpoint on Vertex
gcloud ai endpoints deploy-model $ENDPOINT_ID \
  --region=$GCP_REGION \
  --model=$MODEL_ID \
  --display-name=$DEPLOYED_MODEL_NAME \
  --machine-type=n1-standard-2 \
  --service-account=$SERVICE_ACCOUNT_EMAIL