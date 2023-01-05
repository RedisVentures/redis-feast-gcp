# Setup Vertex AI and Triton
echo "\nSetting up Triton Model Repository in GCS"
ARTIFACT_REPOSITORY_NAME=nvidia-triton
CONTAINER_IMAGE_URI=$GCP_REGION-docker.pkg.dev/$PROJECT_ID/$ARTIFACT_REPOSITORY_NAME/vertex-triton-inference
ENDPOINT_NAME=vaccine-predictor-endpoint
DEPLOYED_MODEL_NAME=vaccine-predictor
MODEL_STORAGE_URI=gs://$BUCKET_NAME/models

# Create Vertex AI Model
echo "\nCreating Vertex AI Model"
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