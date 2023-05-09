from feature_store.repo import FF_0_config as config

# TODO: Check if the parameters are correct
# TODO: Check if this is the best way to structure the providers
def register_providers(ff):
    # TODO: Check if the credentials_path should be pulling from somewhere else
    # # i.e. in the redis_feast project it's a var but we pass in a path as a string
    bigquery = ff.register_bigquery(
        name="bigquery-ff",
        description="A BigQuery deployment we created for the Covid-19 vaccine demo.",
        project_id=f"{config.PROJECT_ID}",
        dataset_id=f"{config.BIGQUERY_DATASET_NAME}",
        credentials_path=f"{config.GOOGLE_APPLICATION_CREDENTIALS}",
    )

    # Redis Registeration
    redis = ff.register_redis(
        name=f"{config.PROJECT_ID}",
        description="A Redis Deployment we created for the Covid-19 vaccine demo.",
        team=f"{config.REDIS_TEAM}",
        host=f"{config.REDIS_HOST}",  # The internal dns name for redis - "quickstart-redis",
        port=f"{config.REDIS_PORT}",
        password=f"{config.REDIS_PASSWORD}",
        db=f"{config.REDIS_DB}",
    )

    return bigquery, redis
