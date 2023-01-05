FROM jupyter/minimal-notebook:python-3.8 as jupyterImg

WORKDIR /home/jovyan/work

USER root
ENV PYTHONUNBUFFERED 1
ENV PYTHONDONTWRITEBYTECODE 1

RUN python3 -m pip install --upgrade pip setuptools wheel

# Copy over resources
COPY setup.py ./
COPY setup.cfg ./
COPY ./feature_store ./feature_store/

# Install Feature Store package
RUN pip install -e .

COPY ./jupyter/requirements.txt .
RUN python3 -m pip install -r requirements.txt

# Install Curl
RUN apt-get update \
    && echo "Installing curl" \
    && apt-get install -y curl

# Install GCloud CLI
ENV CLOUDSDK_INSTALL_DIR="/usr/local/gcloud/"
RUN curl -sSL https://sdk.cloud.google.com | bash
ENV PATH="/usr/local/gcloud/google-cloud-sdk/bin:$PATH"
RUN sudo chown jovyan -R ~/

# Define this parameter to install jupyter lab
ENV JUPYTER_ENABLE_LAB=yes