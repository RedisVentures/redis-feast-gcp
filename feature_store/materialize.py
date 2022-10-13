
import pandas as pd
import tempfile

from datetime import datetime
from google.cloud import bigquery
from google.cloud import storage
from feast import FeatureStore

from repo import config
from utils import file



def generate_vaccine_search_features(
    client: bigquery.Client,
    table_id: str
):
    """
    """
    job_config = bigquery.QueryJobConfig(
        destination=table_id,
        write_disposition='WRITE_TRUNCATE'
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
    print("Generated weekly vaccine search trends features.")

def generate_vaccine_count_features(
    client: bigquery.Client,
    table_id: str
):
    """
    Generate and upload vaccine count features from a CSV to BigQuery.

    Args:
        client (bigquery.Client): GCP bigquery Client.
        storage_client (storage.Client): GCP storage Client.
        table_id (str): Table ID for this feature set.
    """
    # Generate temp dir
    tmpdir = tempfile.gettempdir()
    input_filename = f"{tmpdir}/us_state_vaccinations.csv"
    output_filename = f"{tmpdir}/us_weekly_vaccinations.csv"
    output_storage_filename = "data/us_weekly_vaccinations.csv"

    # Download the CSV file from URL
    file.download_url(
        filename=input_filename,
        url=config.DAILY_VACCINATIONS_CSV_URL
    )

    print("Loading us_state_vaccinations.csv", flush=True)
    df = pd.read_csv(input_filename)[['date', 'location', 'daily_vaccinations']]
    print(len(df), "loaded daily vaccination records", flush=True)

    print("Cleaning dataset", flush=True)
    df['date'] = df['date'].astype('datetime64[ns]')

    print("Truncating records and filling NaNs", flush=True)
    df = df[(~df.location.isin(['United States', 'Long Term Care'])) & (df.date >= '2021-1-1')].fillna(0)
    print(len(df), "daily records remaining", flush=True)

    print("Rolling up counts into weeks starting on Mondays", flush=True)
    df = df.groupby([pd.Grouper(freq='W-Mon', key='date'), 'location'])['daily_vaccinations'].sum().reset_index()
    df.rename(columns={'daily_vaccinations': 'lag_1_weekly_vaccinations_count', 'location': 'state'}, inplace=True)
    print(len(df), "weekly vaccine count records for", len(df.state.value_counts()), "total states & territories", flush=True)

    print("Creating lagged features", flush=True)
    df['weekly_vaccinations_count'] = df.groupby('state').lag_1_weekly_vaccinations_count.shift(periods=-1)
    df['lag_2_weekly_vaccinations_count'] = df.groupby('state').lag_1_weekly_vaccinations_count.shift(periods=1)
    df.sort_values(['date', 'state'], inplace=True)

    print("Saving dataframe...", flush=True)
    df['weekly_vaccinations_count'] = df['weekly_vaccinations_count'].astype('Int64', errors='ignore')
    df['lag_1_weekly_vaccinations_count'] = df['lag_1_weekly_vaccinations_count'].astype('Int64', errors='ignore')
    df['lag_2_weekly_vaccinations_count'] = df['lag_2_weekly_vaccinations_count'].astype('Int64', errors='ignore')
    df['date'] = df['date'].dt.strftime("%Y-%m-%d %H:%M:%S")

    print("Uploading CSV", flush=True)
    # Save back to tempfile
    df.to_csv(output_filename, index=False)

    # Upload to cloud storage
    file.upload_to_gcs(
        local_filename=output_filename,
        remote_filename=output_storage_filename
    )

    # Load bq job config
    job_config = bigquery.LoadJobConfig(
        schema=[
            bigquery.SchemaField("date", "TIMESTAMP"),
            bigquery.SchemaField("state", "STRING"),
            bigquery.SchemaField("lag_1_weekly_vaccinations_count", "INTEGER"),
            bigquery.SchemaField("weekly_vaccinations_count", "INTEGER"),
            bigquery.SchemaField("lag_2_weekly_vaccinations_count", "INTEGER")
        ],
        skip_leading_rows=1,
        max_bad_records=2,
        source_format=bigquery.SourceFormat.CSV,
        write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE
    )
    # Start the job
    uri = f"gs://{config.BUCKET_NAME}/{output_storage_filename}"
    load_job = client.load_table_from_uri(
        uri,
        table_id,
        job_config=job_config
    )
    # Wait for job to complete
    load_job.result()
    print("Generated weekly vaccine count features.")

def materialize_features():
    """_summary_

    Args:
        storage_client (storage.Client): _description_
    """
    # Load RepoConfig
    repo_config = config.load_repo_config()
    # Load FeatureStore from RepoConfig
    store = FeatureStore(config=repo_config)
    # Materialize Features to Redis
    store.materialize_incremental(end_date=datetime.now())

def main(data, context):
    client = bigquery.Client()
    # Generate Vaccine Count Features
    generate_vaccine_count_features(
        client,
        f"{config.PROJECT_ID}.{config.BIGQUERY_DATASET_NAME}.{config.WEEKLY_VACCINATIONS_TABLE}"
    )
    # Generate Vaccine Search Features
    generate_vaccine_search_features(
        client,
        f"{config.PROJECT_ID}.{config.BIGQUERY_DATASET_NAME}.{config.VACCINE_SEARCH_TRENDS_TABLE}"
    )
    # Perform local materialization
    materialize_features()
