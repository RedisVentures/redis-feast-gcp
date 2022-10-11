pwd

WD=$(pwd)

gcloud functions deploy feast-update-features \
    --source=$WD \
    --entry-point=main \
    --memory=1024MB \
    --allow-unauthenticated \
    --runtime python38 \
    --trigger-resource feast-schedule \
    --trigger-event google.pubsub.topic.publish \
    --timeout 540s \
    --set-build-env-vars GOOGLE_FUNCTION_SOURCE="materialize.py" \
    --set-env-vars PROJECT_ID=$1,BIGQUERY_DATASET_NAME=$2,VACCINE_SEARCH_TRENDS_TABLE=$3,WEEKLY_VACCINATIONS_TABLE=$4