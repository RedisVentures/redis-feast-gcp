export $(cat .env | xargs)

# Setup Vertex AI and Triton
echo "\nUploading Triton Models to Cloud Storage"
ARTIFACT_REPOSITORY_NAME=nvidia-triton
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
