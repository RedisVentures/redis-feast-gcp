import pandas as pd
import tempfile

from datetime import timedelta
from google.cloud import bigquery
from feast import BigQuerySource, Entity, FeatureService, FeatureView, Field
from feast.types import Float32, Int64
from feature_store.repo import config
from feature_store.utils import storage


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
    timestamp_field="date",
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
        Field(name="lag_2_vaccine_safety", dtype=Float32),
    ],
    source=vaccine_search_trends_src,
)


weekly_vaccinations_src = BigQuerySource(
    name="weekly_vaccinations_src",
    table=f"{config.PROJECT_ID}.{config.BIGQUERY_DATASET_NAME}.{config.WEEKLY_VACCINATIONS_TABLE}",
    timestamp_field="date",
)

weekly_vaccinations_fv = FeatureView(
    name="weekly_vaccinations",
    entities=[state],
    ttl=timedelta(weeks=52 * 10),
    schema=[
        Field(name="lag_1_weekly_vaccinations_count", dtype=Int64),
        Field(name="lag_2_weekly_vaccinations_count", dtype=Int64),
        Field(name="weekly_vaccinations_count", dtype=Int64),
    ],
    source=weekly_vaccinations_src,
)


serving_features = FeatureService(
    name="serving_features",
    features=[
        vaccine_search_trends_fv,
        weekly_vaccinations_fv[
            ["lag_1_weekly_vaccinations_count", "lag_2_weekly_vaccinations_count"]
        ],
    ],
)

training_features = FeatureService(
    name="training_features",
    features=[vaccine_search_trends_fv, weekly_vaccinations_fv],
)


def generate_vaccine_search_trends(logging, client: bigquery.Client, table_id: str):
    """
    Generate and upload weekly vaccine search trends features derived from a public
    Google dataset stored in BigQuery.

    Args:
        client (bigquery.Client): GCP bigquery Client.
        table_id (str): Table ID for this feature set.
    """
    job_config = bigquery.QueryJobConfig(
        destination=table_id, write_disposition="WRITE_TRUNCATE"
    )
    sql = f"""
    WITH vaccine_trends AS (
            SELECT
                date,
                sub_region_1 as state,
                avg(sni_covid19_vaccination) as lag_1_vaccine_interest,
                avg(sni_vaccination_intent) as lag_1_vaccine_intent,
                avg(sni_safety_side_effects) as lag_1_vaccine_safety
            FROM
                `bigquery-public-data.covid19_vaccination_search_insights.covid19_vaccination_search_insights`
            GROUP BY
                date, state
        ),
        weekly_trends AS (
            SELECT
                TIMESTAMP(date) as date,
                state,
                lag_1_vaccine_interest,
                lag(lag_1_vaccine_interest)
                    over (partition by state order by date ASC) as lag_2_vaccine_interest,
                lag_1_vaccine_intent,
                lag(lag_1_vaccine_intent)
                    over (partition by state order by date ASC) as lag_2_vaccine_intent,
                lag_1_vaccine_safety,
                lag(lag_1_vaccine_safety)
                    over (partition by state order by date ASC) as lag_2_vaccine_safety
            FROM
                vaccine_trends
        )
        SELECT
            date,
            state,
            lag_1_vaccine_interest,
            lag_2_vaccine_interest,
            lag_1_vaccine_intent,
            lag_2_vaccine_intent,
            lag_1_vaccine_safety,
            lag_2_vaccine_safety
        FROM
            weekly_trends
        WHERE
            state IS NOT NULL AND
            lag_1_vaccine_interest IS NOT NULL AND
            lag_2_vaccine_interest IS NOT NULL AND
            lag_1_vaccine_intent IS NOT NULL AND
            lag_2_vaccine_intent IS NOT NULL AND
            lag_1_vaccine_safety IS NOT NULL AND
            lag_2_vaccine_safety IS NOT NULL
        ORDER BY
            date ASC,
            state;
    """
    query_job = client.query(sql, job_config=job_config)
    query_job.result()
    logging.info("Generated weekly vaccine search trends features")


def generate_vaccine_counts(logging, client: bigquery.Client, table_id: str):
    """
    Generate and upload vaccine count features from a CSV to BigQuery.

    Args:
        client (bigquery.Client): GCP bigquery Client.
        table_id (str): Table ID for this feature set.
    """
    # Generate temp dir
    tmpdir = tempfile.gettempdir()
    input_filename = f"{tmpdir}/us_state_vaccinations.csv"
    output_filename = f"{tmpdir}/us_weekly_vaccinations.csv"
    output_storage_filename = "data/us_weekly_vaccinations.csv"

    # Download the CSV file from URL
    storage.download_file_url(
        filename=input_filename, url=config.DAILY_VACCINATIONS_CSV_URL
    )

    logging.info("Loading us_state_vaccinations.csv")
    df = pd.read_csv(input_filename)[["date", "location", "daily_vaccinations"]]
    logging.info(f"Loaded {len(df)} daily vaccination records")

    logging.info("Cleaning dataset")
    df["date"] = df["date"].astype("datetime64[ns]")

    logging.info("Truncating records and filling NaNs")
    df = df[
        (~df.location.isin(["United States", "Long Term Care"]))
        & (df.date >= "2021-1-1")
    ].fillna(0)
    logging.info(f"{len(df)} daily records remaining")

    logging.info("Rolling up counts into weeks starting on Mondays")
    df = (
        df.groupby([pd.Grouper(freq="W-Mon", key="date"), "location"])[
            "daily_vaccinations"
        ]
        .sum()
        .reset_index()
    )
    df.rename(
        columns={
            "daily_vaccinations": "lag_1_weekly_vaccinations_count",
            "location": "state",
        },
        inplace=True,
    )
    logging.info(
        f"{len(df)} weekly vaccine count records for {len(df.state.value_counts())} total states & territories"
    )

    logging.info("Creating lagged features")
    df["weekly_vaccinations_count"] = df.groupby(
        "state"
    ).lag_1_weekly_vaccinations_count.shift(periods=-1)
    df["lag_2_weekly_vaccinations_count"] = df.groupby(
        "state"
    ).lag_1_weekly_vaccinations_count.shift(periods=1)
    df.sort_values(["date", "state"], inplace=True)

    logging.info("Saving dataframe...")
    df["weekly_vaccinations_count"] = df["weekly_vaccinations_count"].astype(
        "Int64", errors="ignore"
    )
    df["lag_1_weekly_vaccinations_count"] = df[
        "lag_1_weekly_vaccinations_count"
    ].astype("Int64", errors="ignore")
    df["lag_2_weekly_vaccinations_count"] = df[
        "lag_2_weekly_vaccinations_count"
    ].astype("Int64", errors="ignore")
    df["date"] = df["date"].dt.strftime("%Y-%m-%d %H:%M:%S")

    logging.info("Uploading CSV")
    # Save back to tempfile
    df.to_csv(output_filename, index=False)

    # Upload to cloud storage
    storage.upload_file(
        local_filename=output_filename,
        remote_filename=output_storage_filename,
        bucket_name=config.BUCKET_NAME,
    )

    # Load bq job config
    job_config = bigquery.LoadJobConfig(
        schema=[
            bigquery.SchemaField("date", "TIMESTAMP"),
            bigquery.SchemaField("state", "STRING"),
            bigquery.SchemaField("lag_1_weekly_vaccinations_count", "INTEGER"),
            bigquery.SchemaField("weekly_vaccinations_count", "INTEGER"),
            bigquery.SchemaField("lag_2_weekly_vaccinations_count", "INTEGER"),
        ],
        skip_leading_rows=1,
        max_bad_records=2,
        source_format=bigquery.SourceFormat.CSV,
        write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE,
    )
    # Start the job
    logging.info("Running query")
    load_job = client.load_table_from_uri(
        f"gs://{config.BUCKET_NAME}/{output_storage_filename}",
        table_id,
        job_config=job_config,
    )
    # Wait for job to complete
    load_job.result()
    logging.info("Generated weekly vaccine count features")
