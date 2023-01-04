FROM jupyter/minimal-notebook:python-3.8 as jupyterImg

# Change to root user to install things
USER root

ENV PYTHONUNBUFFERED 1
ENV PYTHONDONTWRITEBYTECODE 1

RUN python3 -m pip install --upgrade pip setuptools wheel

WORKDIR /home/jovyan/work

# Copy over resources
COPY setup.py ./
COPY setup.cfg ./
COPY ./feature_store ./feature_store/

# Install Feature Store package
RUN pip install -e .

# Install Curl
RUN apt-get update \
    && echo "Installing curl" \
    && apt-get install -y curl

# Install GCloud CLI
ENV CLOUDSDK_INSTALL_DIR="/usr/local/gcloud/"
RUN curl -sSL https://sdk.cloud.google.com | bash
ENV PATH="/usr/local/gcloud/google-cloud-sdk/bin:$PATH"

# Let's change to  "$NB_USER" command so the image runs as a non root user by default
USER $NB_UID

#Let's define this parameter to install jupyter lab instead of the default juyter notebook command so we don't have to use it when running the container with the option -e
ENV JUPYTER_ENABLE_LAB=yes