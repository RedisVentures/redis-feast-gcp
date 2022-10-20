# Feature Store Overview
A quick view of what's in this package:

* [`repo/`](repo/) contains Feast feature definitions and configuration.
* [`utils/`](utils/) contains helper utilities and functions that can be used throughout.

TBD -- Need to fill this out a good bit.


>Our offline features will be stored in GCP BigQuery. Above, we've already created a dataset `gcp_feast_demo` where our cloud function can load two new tables.

- `gcp_feast_demo.us_weekly_vaccinations` - Weekly vaccination counts across the United States by State.
- `gcp_feast_demo.vaccine_search_trends` - Weekly vaccine search trends series with three search categories (interest, intent, and safety) by US state.