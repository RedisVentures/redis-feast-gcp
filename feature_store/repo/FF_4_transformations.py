import pandas as pd
import tempfile

from feature_store.repo import config
from feature_store.utils import storage, logger


logging = logger.get_logger()


def register_vaccine_search_trends(offline_store, online_store, entity):
    @offline_store.sql_transformation(
        name="generate_vaccine_search_trends",
        variant="default",
        description="Generate and upload weekly vaccine search trends features derived from a public Google dataset stored in BigQuery.",
    )
    def generate_vaccine_search_trends():
        return f"""
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

    generate_vaccine_search_trends.register_resources(
        name="vaccine_search_trends",
        entity=entity,
        entity_column="customerid",
        inference_store=online_store,
        features=[
            {
                "name": "lag_1_vaccine_interest",
                "column": "lag_1_vaccine_interest",
                "type": "float32",
            },
            {
                "name": "lag_2_vaccine_interest",
                "column": "lag_2_vaccine_interest",
                "type": "float32",
            },
            {
                "name": "lag_1_vaccine_intent",
                "column": "lag_1_vaccine_intent",
                "type": "float32",
            },
            {
                "name": "lag_2_vaccine_intent",
                "column": "lag_2_vaccine_intent",
                "type": "float32",
            },
            {
                "name": "lag_1_vaccine_safety",
                "column": "lag_1_vaccine_safety",
                "type": "float32",
            },
            {
                "name": "lag_2_vaccine_safety",
                "column": "lag_2_vaccine_safety",
                "type": "float32",
            },
        ],
    )


def register_vaccine_counts(offline_store, online_store, entity):
    @offline_store.df_transformation(
        name="generate_vaccine_counts",
        variant="default",
        description="Generate vaccine count features.",
    )
    def generate_vaccine_counts():
        # Generate temp dir
        tmpdir = tempfile.gettempdir()
        input_filename = f"{tmpdir}/us_state_vaccinations.csv"

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

        logging.info("Generated weekly vaccine count features")
        return df

    generate_vaccine_counts.register_resources(
        name="weekly_vaccinations",
        entity=entity,
        entity_column="customerid",
        inference_store=online_store,
        features=[
            {
                "name": "lag_1_weekly_vaccinations_count",
                "column": "lag_1_weekly_vaccinations_count",
                "type": "float32",
            },
            {
                "name": "lag_2_weekly_vaccinations_count",
                "column": "lag_2_weekly_vaccinations_count",
                "type": "float32",
            },
            {
                "name": "weekly_vaccinations_count",
                "column": "weekly_vaccinations_count",
                "type": "float32",
            },
        ],
    )
