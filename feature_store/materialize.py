import os
import requests
import pandas as pd
import tempfile

from datetime import datetime
from google.cloud import bigquery
from feast import FeatureStore



def _download_file(filename, url):
    # NOTE the stream=True parameter below
    with requests.get(url, stream=True) as r:
        r.raise_for_status()
        with open(filename, 'wb') as f:
            for chunk in r.iter_content(chunk_size=8192): 
                # If you have chunk encoded response uncomment if
                # and set chunk_size parameter to None.
                #if chunk:
                f.write(chunk)

def generate_vaccine_search_features(client: bigquery.Client, table_id: str):
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

def generate_vaccine_count_features(client: bigquery.Client, table_id: str):
    tmpdir = tempfile.gettempdir()
    filename = f"{tmpdir}/us_state_vaccinations.csv"
    file_url = "https://raw.githubusercontent.com/owid/covid-19-data/master/public/data/vaccinations/us_state_vaccinations.csv"
    _download_file(filename, file_url)

    print("Loading us_state_vaccinations.csv", flush=True)
    df = pd.read_csv("data/us_state_vaccinations.csv")[['date', 'location', 'daily_vaccinations']]
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
    df['weekly_vaccinations_count'] = df['weekly_vaccinations_count'].astype(int, errors='ignore')
    df['lag_1_weekly_vaccinations_count'] = df['lag_1_weekly_vaccinations_count'].astype(int, errors='ignore')
    df['lag_2_weekly_vaccinations_count'] = df['lag_2_weekly_vaccinations_count'].astype(int, errors='ignore')
    df['date'] = df.date.dt.strftime("%Y-%m-%d %H:%M:%S")

    df.to_csv(f'{tmpdir}/us_weekly_vaccinations.csv', index=False)

    print("Uploading CSV", flush=True)
    # Load job config
    job_config = bigquery.LoadJobConfig(
        schema=[
            bigquery.SchemaField("date", "TIMESTAMP"),
            bigquery.SchemaField("state", "STRING"),
            bigquery.SchemaField("weekly_vaccinations_count", "INTEGER"),
            bigquery.SchemaField("lag_1_weekly_vaccinations_count", "INTEGER"),
            bigquery.SchemaField("lag_2_weekly_vaccinations_count", "INTEGER")
        ],
        skip_leading_rows=1,
        max_bad_records=2,
        source_format=bigquery.SourceFormat.CSV,
        replace=True
    )
    # Start the job
    load_job = client.load_table_from_uri(
        "data/us_weekly_vaccinations.csv",
        table_id,
        job_config=job_config
    )
    # Wait for job to complete
    load_job.result()
    print("Generated weekly vaccine count features.")

def materialize_features(feature_repo: str):
    store = FeatureStore(feature_repo)
    serving
    store.materialize_incremental(end_date=datetime.now())

def main(data, context):
    client = bigquery.Client()
    project_id = os.environ['PROJECT_ID']
    bigquery_dataset_name = os.environ['BIGQUERY_DATASET_NAME']
    vaccine_search_trends_table = os.environ['VACCINE_SEARCH_TRENDS_TABLE']
    weekly_vaccinations_table = os.environ['WEEKLY_VACCINATIONS_TABLE']
    # Generate Vaccine Count Features
    generate_vaccine_count_features(client, f"{project_id}.{bigquery_dataset_name}.{weekly_vaccinations_table}")
    # Generate Vaccine Search Features
    generate_vaccine_search_features(client, f"{project_id}.{bigquery_dataset_name}.{vaccine_search_trends_table}")
    # Perform local materialization
    materialize_features('./feature_repo/')
