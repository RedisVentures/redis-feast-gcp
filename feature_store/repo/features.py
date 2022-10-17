from datetime import timedelta

from feast import (
    BigQuerySource,
    Entity,
    FeatureService,
    FeatureView,
    Field
)
from feast.types import Float32, Int64

from repo import config

# Define an entity for the state. You can think of an entity as a primary key used to
# fetch features.
state = Entity(name="state", join_keys=["state"])

# Defines a data source from which feature values can be retrieved. Sources are queried when building training
# datasets or materializing features into an online store.
vaccine_search_trends_src = BigQuerySource(
    name="vaccine_search_trends_src",
    # The BigQuery table where features can be found
    table=f"{config.PROJECT_ID}.{config.BIGQUERY_DATASET_NAME}.{config.VACCINE_SEARCH_TRENDS_TABLE}",
    # The event timestamp is used for point-in-time joins and for ensuring only
    # features within the TTL are returned
    timestamp_field="date"
)

# Feature views are a grouping based on how features are stored in either the
# online or offline store.
vaccine_search_trends_fv = FeatureView(
    # The unique name of this feature view. Two feature views in a single
    # project cannot have the same name
    name="vaccine_search_trends",
    # The list of entities specifies the keys required for joining or looking
    # up features from this feature view. The reference provided in this field
    # correspond to the name of a defined entity (or entities)
    entities=[state],
    # The timedelta is the maximum age that each feature value may have
    # relative to its lookup time. For historical features (used in training),
    # TTL is relative to each timestamp provided in the entity dataframe.
    # TTL also allows for eviction of keys from online stores and limits the
    # amount of historical scanning required for historical feature values
    # during retrieval
    ttl=timedelta(weeks=52 * 10),  # Set to be very long for example purposes only
    # The list of features defined below act as a schema to both define features
    # for both materialization of features into a store, and are used as references
    # during retrieval for building a training dataset or serving features
    schema=[
        Field(name="lag_1_vaccine_interest", dtype=Float32),
        Field(name="lag_2_vaccine_interest", dtype=Float32),
        Field(name="lag_1_vaccine_intent", dtype=Float32),
        Field(name="lag_2_vaccine_intent", dtype=Float32),
        Field(name="lag_1_vaccine_safety", dtype=Float32),
        Field(name="lag_2_vaccine_safety", dtype=Float32)
    ],
    source=vaccine_search_trends_src,
)


weekly_vaccinations_src = BigQuerySource(
    name="weekly_vaccinations_src",
    table=f"{config.PROJECT_ID}.{config.BIGQUERY_DATASET_NAME}.{config.WEEKLY_VACCINATIONS_TABLE}",
    timestamp_field="date"
)

weekly_vaccinations_fv = FeatureView(
    name="weekly_vaccinations",
    entities=[state],
    ttl=timedelta(weeks=52 * 10),
    schema=[
        Field(name="lag_1_weekly_vaccinations_count", dtype=Int64),
        Field(name="lag_2_weekly_vaccinations_count", dtype=Int64),
        Field(name="weekly_vaccinations_count", dtype=Int64)
    ],
    source=weekly_vaccinations_src,
)


serving_features = FeatureService(
    name="serving_features",
    features=[
        vaccine_search_trends_fv[[
            "lag_1_vaccine_interest",
            "lag_2_vaccine_interest",
            "lag_1_vaccine_intent",
            "lag_2_vaccine_intent",
            "lag_1_vaccine_safety",
            "lag_2_vaccine_safety"
        ]],
        weekly_vaccinations_fv[[
            "lag_1_weekly_vaccinations_count",
            "lag_2_weekly_vaccinations_count"
        ]]
    ],
)

training_features = FeatureService(
    name="training_features",
    features=[
        vaccine_search_trends_fv,
        weekly_vaccinations_fv
    ],
)
