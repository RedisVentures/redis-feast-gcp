# gcp-feast-demo
*An end-to-end architecture of [Feast](https://docs.feast.dev/) with [Redis Cloud](https://app.redislabs.com/) (as the Online Feature Store) deployed on Google Cloud Platform (GCP).*

>*This demo is not meant to replace a production ML system. Rather, it should demonstrate several core components, all of which should be interchangeable and modular with your specific setup.*
___

## Demo ML Application
To demonstrate the power of a Feature Store, we include a demo machine learning application that **predicts the count of next week's administered vaccine doses** (by state).

The Feature Store fuses together weekly [google search trends data]() along with lagging [vaccine dose counts]().

>*Both datasets are open source and provided free to the public!*

The full system will include:
- GCP infrastructure setup and teardown
- Offline (BigQuery) and Online (Redis Enterprise) Feature Stores using Feast
- Model Training and Serving applications

### Architecture

Here's a high-level picture of the system architecture:

![architecture](img/Feast_GCP_Redis_Ray_Demo.png)


The architecture takes advantage of many GCP managed services to make the setup/teardown as simple as possible. will include different tools based on the environment.

The stack includes the following components:

- **Feast** feature definitions in a **GitHub** repository (here).
- Feature registry persisted in a **Cloud Storage** bucket with **Feast** and **Cloud Build** for CI/CD.
- Offline feature data stored in **BigQuery** as the source of record.
- Daily **Cloud Scheduler** tasks to trigger a materialization **Cloud Function** that will migrate the latest feature updates to the Online feature store.
- **Redis Cloud** (or any Redis) as the online store.

By the end of this tutorial, you will have all of these components running in your GCP project, or just follow along to see how it's stitched together.

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

    - <img src="https://user-images.githubusercontent.com/13009163/198134507-a22ecc60-6e87-43ac-8f33-e685215a363e.png" width="30%"><img>
    - You should see the following notifications
    - <img src="https://user-images.githubusercontent.com/13009163/198134908-6b102849-dd73-4e77-9b04-1ef9d38b3307.png" width="30%"><img>

4. Acquire a GCP service account credential file and download to your machine, somewhere safe.
    - IAM -> Service Account -> Create service account

5. Create a new key for that service account.
    - In Service account, go to "keys" pane and create new key.
    - Download locally and remember the file path
    - <img src="https://user-images.githubusercontent.com/13009163/198135033-a16b7ada-5c7c-4a56-bb74-ee038b5076cb.png" width="30%"><img>


#### Redis
You have a few options here. Top two recommended options:

1. Setup a [Redis Cloud instance](https://app.redislabs.com/). (There's a 30Mb Free Tier)
2. Pull and use a separate [Redis docker image](https://hub.docker.com/_/redis).

#### Environment
We will provision GCP infrastructure from your localhost. So, we need to handle local environment variables, thankfully all handled by Docker and a `.env` file.


1. Make the env file and enter values as prompted. See template below:
    ```bash
    $ make env
    ```
    >REDIS_CONNECTION_STRING={host}:{port}

    >REDIS_PASSWORD={password}

    >GOOGLE_APPLICATION_CREDENTIALS={local-path-to-gcp-creds}

    >PROJECT_ID={gcp-project-id} (project-id not project-number)

    >GCP_REGION={preferred-gcp-region}

    >BUCKET_NAME={your-gcp-bucket-name}

    >SERVICE_ACCOUNT_EMAIL={your-gcp-scv-account-email}


#### Build
Assuming all above steps are done, build the docker images required to run the different apps.

1. From the root of the project, run:
    ```bash
    $ make docker
    ```

You may need to disable docker buildkit for Mac machines

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
Now that the Feature Store is in place, utilize the following add-on apps to perform different tasks as desired.

#### Jupyter
Run a Jupyter notebook to perform exploratory data analysis and interact with the
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

>Training can take place locally (for the demo) or in the cloud through a managed service offering, or as a Kubernetes (GKE) job. There is flexibility here, which is why we built a container.

#### Serve
Expose the vaccine demand forecast model for inference with [Ray Serve](https://docs.ray.io/en/latest/serve/index.html) and [Fast API](https://fastapi.tiangolo.com/). Online feature are pulled from **Redis** using **Feast**.

```bash
$ make serve
```

>Serving can take place locally (for the demo) or in the cloud through a managed service offering, or in Kubernetes (GKE + Kuberay). There is flexibility here, which is why we built a container.

#### Teardown
Cleanup GCP infrastructure and teardown Feature Store.

```bash
$ make teardown
```

___

