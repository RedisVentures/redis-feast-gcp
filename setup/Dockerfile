FROM continuumio/miniconda3:latest as baseImage

WORKDIR /app

COPY ./setup/environment.yml .

ENV PYTHONNOUSERSITE=True

RUN conda env create -f environment.yml
RUN conda install -y conda-pack
RUN conda pack -n py38 -o python3.8.tar.gz

FROM redisventures/redis-feast-gcp:1.0.0 as appImage

WORKDIR /app
COPY ./setup ./setup/
COPY ./materialize.py ./
COPY ./requirements.txt ./
COPY --from=baseImage /app/python3.8.tar.gz ./setup/models/preprocess/python3.8.tar.gz

RUN apt-get update && \
    apt-get install -y curl

ENV CLOUDSDK_INSTALL_DIR="/usr/local/gcloud/"
RUN curl -sSL https://sdk.cloud.google.com | bash
ENV PATH="/usr/local/gcloud/google-cloud-sdk/bin:$PATH"

CMD ./setup/setup.sh