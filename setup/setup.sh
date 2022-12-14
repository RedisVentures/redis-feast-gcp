# Auth
gcloud auth activate-service-account $SERVICE_ACCOUNT_EMAIL \
    --key-file=$GOOGLE_APPLICATION_CREDENTIALS \
    --project=$PROJECT_ID


# Setup GCP Project Name
echo project_id = $PROJECT_ID > ~/.bigqueryrc

# Create Cloud Storage Bucket
gsutil mb gs://$BUCKET_NAME

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