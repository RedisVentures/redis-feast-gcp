FROM redisventures/redis-feast-gcp:1.0.0

WORKDIR /app
COPY ./setup ./setup/
COPY ./materialize.py ./
COPY ./requirements.txt ./

RUN apt-get update && \
    apt-get install -y curl

ENV CLOUDSDK_INSTALL_DIR="/usr/local/gcloud/"
RUN curl -sSL https://sdk.cloud.google.com | bash
ENV PATH="/usr/local/gcloud/google-cloud-sdk/bin:$PATH"

CMD ./setup/setup.sh