# gcp-feast-demo
*An end-to-end demo of [Feast](https://docs.feast.dev/) with [Redis](https://app.redislabs.com/) as the Online Feature Store deployed on Google Cloud Platform (GCP).*

___

## Demo ML Application
The demo application fuses together [google search trends data]() along with [vaccine dose counts]() by state and week. Both datasets are open source and provided free to the public. **The trained model will try to predict next week's vaccine doses administered by state**.

The full system will include:
- GCP infrastructure setup and teardown
- Offline (BigQuery) and Online (Redis Enterprise) Feature Stores
- Training and Serving applications


Here's a high-level picture of the system architecture:

![](img/Feast_GCP_Redis_Ray_Demo.png)


The stack will include different tools based on the environment. On GCP, our stack will include the following:

- All model feature definitions will live in a **GitHub** repository (this one).
- Features will be registered to a **Cloud Storage** bucket using the **Feast** SDK and **Cloud Build** for CI/CD.
- **BigQuery** will be the offline source of record for ML features.
- Periodically, a **Cloud Scheduler** job will trigger a **Cloud Function** to materialize the latest features to the online store.
- **Redis Enterprise** will be the online store.

___

## Apps
This demo is broken out into different sections/steps that form small Dockerized applications. We use Docker Compose to manage the runtime environment of the apps. Make sure you have Docker installed on your machine before proceeding

**Prerequisites**
1. Install Docker on your machine
2. [Create a new GCP project](https://console.cloud.google.com/cloud-resource-manager)
3. [Make sure that billing is enabled for your project.](https://cloud.google.com/billing/docs/how-to/modify-project)
4. Enable the following GCP APIs:
    1. [Cloud Scheduler](https://console.cloud.google.com/apis/library/cloudscheduler.googleapis.com?q=cloud&id=1d54d828-14ed-4976-959b-3b18cca9e859)
    2. [Cloud Build](https://console.cloud.google.com/apis/library/cloudbuild.googleapis.com?q=cloud&id=9472915e-c82c-4bef-8a6a-34c81e5aebcc)
    3. [Cloud Functions](https://console.cloud.google.com/apis/library/cloudfunctions.googleapis.com?q=cloud%20functions&id=2174da14-0e34-49ed-9267-e258674e95da)
5. Get access to a Redis database. Local or deployed in the cloud.
6. Setup the environment by running `cp .env.template .env` and filling out all ENV VAR blanks.

### Setup
Provision GCP infrastructure and create the Feast Feature Store.

**Command**: `docker compose run setup`

### Jupyter
Run a Jupyter notebook to perform exploratory data analysis and interact with the
Feature Store using the [Feast SDK](https://rtd.feast.dev/en/master/).

**Command**: `docker compose run jupyter`

### Train
Train a vaccine demand forecast model using XGBoost and Offline features
pulled from Feast.

**Command**: `docker compose run train`

### Serve
Expose the vaccine demand forecast model with Ray Serve and Fast API.

**Command**: `docker compose run serve`

### Teardown
Cleanup GCP infrastructure and teardown Feature Store.

**Command**: `docker compose run teardown`