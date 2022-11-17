# redis-feast-gcp
*An end-to-end machine learning feature store architecture using [Feast](https://docs.feast.dev/) and [Redis Enterprise](https://app.redislabs.com/) (as the Online Feature Store) deployed on [Google Cloud Platform](https://cloud.google.com/) (GCP).*

>This prototype is a reference architecture. All components are containerized, and various customizations and optimizations are required before running in production.
___

## Demo ML Application: COVID-19 Vaccination Forecasting
To demonstrate the power of a Feature Store, we provide a demo application that **forecasts the count administered COVID-19 vaccine doses** (by US state) **for next week**.

The Feature Store fuses together weekly [google search trends data](https://console.cloud.google.com/marketplace/product/bigquery-public-datasets/covid19-vaccination-search-insights) along with lagging [vaccine dose counts](https://github.com/owid/covid-19-data). *Both datasets are open source and provided free to the public.*

The full system will include:
- GCP infrastructure setup and teardown
- Offline (BigQuery) and Online (Redis Enterprise) Feature Stores using Feast
- Model Training and Serving applications

### Architecture

Here's a high-level picture of the system architecture:

![architecture](img/redis-feast-gcp-architecture.png)


The architecture takes advantage of GCP managed services in combination with Feast and Redis.

- **Feast** feature definitions in a **GitHub** repository (here).
- Feature registry persisted in a **Cloud Storage** bucket with **Feast** and **Cloud Build** for CI/CD (*coming soon*).
- Offline feature data stored in **BigQuery** as the source of record.
- Daily **Cloud Scheduler** tasks to trigger a materialization **Cloud Function** that will migrate the latest feature updates to the Online feature store.
- Model training tasks can run by pulling historically accurate training data through **Feast**. Models stored+versioned in **Redis**.
- Model serving tasks pull online (low latency) features with **Feast**.

By the end of this tutorial, you will have all components running in your GCP project.

___

## Getting Started
The demo contains several smaller apps organized by Docker Compose. Below we will cover prereq's and setup tasks.

### Prerequisites

#### Docker
Install Docker on your machine. [Docker Desktop](https://www.docker.com/products/docker-desktop/) is best, thanks to it's ease of use, in our opinion.

#### ☁️ GCP

#### GCP Account Setup

In order to run this in Google Cloud, you will need a GCP project. The steps are

1. If you don't have one [create a new GCP project](https://console.cloud.google.com/cloud-resource-manager)
2. [Make sure that billing is enabled for your project.](https://cloud.google.com/billing/docs/how-to/modify-project)

3. Enable the following GCP APIs:
    1. [Cloud Scheduler](https://console.cloud.google.com/apis/library/cloudscheduler.googleapis.com?q=cloud&id=1d54d828-14ed-4976-959b-3b18cca9e859)
    2. [Cloud Build](https://console.cloud.google.com/apis/library/cloudbuild.googleapis.com?q=cloud&id=9472915e-c82c-4bef-8a6a-34c81e5aebcc)
    3. [Cloud Functions](https://console.cloud.google.com/apis/library/cloudfunctions.googleapis.com?q=cloud%20functions&id=2174da14-0e34-49ed-9267-e258674e95da)

        <img src="https://user-images.githubusercontent.com/13009163/198134507-a22ecc60-6e87-43ac-8f33-e685215a363e.png" width="30%"><img>

    4. You should see the following notifications:

        <img src="https://user-images.githubusercontent.com/13009163/198134908-6b102849-dd73-4e77-9b04-1ef9d38b3307.png" width="30%"><img>


4. Acquire a GCP service account credential file and download to your machine, somewhere safe.
    - IAM -> Service Account -> Create service account

5. Create a new key for that service account.
    - In Service account, go to "keys" pane and create new key.
    - Download locally and remember the file path:

        <img src="https://user-images.githubusercontent.com/13009163/198135033-a16b7ada-5c7c-4a56-bb74-ee038b5076cb.png" width="30%"><img>


#### Redis Cloud
Setup a [Redis Cloud instance](https://app.redislabs.com/) and record the public endpoint `{host}:{port}` and password. **There's a 30Mb Free Tier** which will be perfect for this demo.

#### Environment
This demo provisions GCP infrastructure from your localhost. So, we need to handle local environment variables, thankfully all handled by Docker and a `.env` file.


Make the env file and enter values as prompted. See template below:
```bash
$ make env
```
>REDIS_CONNECTION_STRING={host}:{port}

>REDIS_PASSWORD={password}

>GOOGLE_APPLICATION_CREDENTIALS={local-path-to-gcp-creds}

>PROJECT_ID={gcp-project-id} **(project-id NOT project-number)**

>GCP_REGION={preferred-gcp-region}

>BUCKET_NAME={your-gcp-bucket-name} **(must be globally unique)**

>SERVICE_ACCOUNT_EMAIL={your-gcp-scv-account-email}


#### Build Containers
Assuming all above steps are done, build the docker images required to run the different apps.

From the root of the project, run:
```bash
$ make docker
```

**TIP**: Disable docker buildkit for Mac machines (if you have trouble with this step)

```bash
export DOCKER_BUILDKIT=0
```

The script will build a [base docker image](./Dockerfile) and then build individiual images for each app: [`setup`](setup/), [`train`](train/), [`serve`](serve/), [`jupyter`](jupyter/), and [`teardown`](teardown/).

This will take some time, ~5-10min, so grab a cup of coffee.

### Feature Store Setup

Provision GCP infrastructure, generate datasets, and create the Feast Feature Store.
```bash
$ make setup
```
At the completion of this step, the majority of the architecture above will be deployed in your GCP.
___

### Other Components
Now that the Feature Store is in place, utilize the following add-ons to perform different tasks as desired.

#### Jupyter
Run a Jupyter notebook to perform exploratory data analysis (including data drift analysis) and interact with the
Feature Store using the [Feast SDK](https://rtd.feast.dev/en/master/).

```bash
$ make jupyter
```
#### Train
Train a vaccine demand forecast model using [XGBoost](https://xgboost.readthedocs.io/en/stable/) and ML features
pulled from **BigQuery** using **Feast**. The model is versioned, pickled, and stored in Redis for access from other apps.

```bash
$ make train
```

>Training takes place locally for the demo. But there is flexibility here, which is why we built a container. This could also be deployed in the cloud with Vertex AI (coming soon).

#### Serve
Expose the vaccine demand forecast model for inference with [Fast API](https://fastapi.tiangolo.com/). Online feature are pulled from **Redis** using **Feast** for low-latency retrieval.

```bash
$ make serve
```

>Serving takes place locally for the demo. But there is flexibility here, which is why we built a container. This could also be deployed in the cloud with Vertex AI (coming soon).

Once the serve container is running, you can run:
```bash
$ curl -X GET -H "Content-type: application/json" -d '{"state":"California"}' "http://127.0.0.1:8000/predict"
```
with any US State to get the forecast for next week's COVID-19 vaccine demand.

#### Teardown
Cleanup GCP infrastructure and teardown Feature Store.

```bash
$ make teardown
```

### Cleanup
Besides running the teardown container, you should run `docker compose down` periodically after shutting down containers to clean up excess networks and unused Docker artifacts.

___

