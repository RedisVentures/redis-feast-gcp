gcloud scheduler jobs create pubsub feast-daily-job \
    --location us-central1 \
    --schedule "0 22 * * *" \
    --topic feast-schedule \
    --message-body "This job schedules feature materialization once a day."