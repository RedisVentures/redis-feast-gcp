
#
# Multistage build.
#
ARG TRITON_VERSION=2.28.0
ARG TRITON_CONTAINER_VERSION=22.11

FROM triton_fil_test AS full

FROM nvcr.io/nvidia/tritonserver:22.11-py3-min

ARG TRITON_VERSION
ARG TRITON_CONTAINER_VERSION

ENV TRITON_SERVER_VERSION ${TRITON_VERSION}
ENV NVIDIA_TRITON_SERVER_VERSION ${TRITON_CONTAINER_VERSION}
LABEL com.nvidia.tritonserver.version="${TRITON_SERVER_VERSION}"

ENV PATH /opt/tritonserver/bin:${PATH}

ENV TF_ADJUST_HUE_FUSED         1
ENV TF_ADJUST_SATURATION_FUSED  1
ENV TF_ENABLE_WINOGRAD_NONFUSED 1
ENV TF_AUTOTUNE_THRESHOLD       2
ENV TRITON_SERVER_GPU_ENABLED    1

# Create a user that can be used to run triton as
# non-root. Make sure that this user to given ID 1000. All server
# artifacts copied below are assign to this user.
ENV TRITON_SERVER_USER=triton-server
RUN userdel tensorrt-server > /dev/null 2>&1 || true &&     if ! id -u $TRITON_SERVER_USER > /dev/null 2>&1 ; then         useradd $TRITON_SERVER_USER;     fi &&     [ `id -u $TRITON_SERVER_USER` -eq 1000 ] &&     [ `id -g $TRITON_SERVER_USER` -eq 1000 ]

# Ensure apt-get won't prompt for selecting options
ENV DEBIAN_FRONTEND=noninteractive

# Common dependencies. FIXME (can any of these be conditional? For
# example libcurl only needed for GCS?)
RUN apt-get update &&     apt-get install -y --no-install-recommends             software-properties-common             libb64-0d             libcurl4-openssl-dev             libre2-5             git             gperf             dirmngr             libgoogle-perftools-dev             libnuma-dev             curl              &&     rm -rf /var/lib/apt/lists/*

# Set TCMALLOC_RELEASE_RATE for users setting LD_PRELOAD with tcmalloc
ENV TCMALLOC_RELEASE_RATE 200

ENV DCGM_VERSION 2.2.9
# Install DCGM. Steps from https://developer.nvidia.com/dcgm#Downloads
RUN curl -o /tmp/cuda-keyring.deb     https://developer.download.nvidia.com/compute/cuda/repos/ubuntu2004/x86_64/cuda-keyring_1.0-1_all.deb     && apt install /tmp/cuda-keyring.deb && rm /tmp/cuda-keyring.deb &&     apt-get update && apt-get install -y datacenter-gpu-manager=1:2.2.9

# Extra defensive wiring for CUDA Compat lib
RUN ln -sf ${_CUDA_COMPAT_PATH}/lib.real ${_CUDA_COMPAT_PATH}/lib  && echo ${_CUDA_COMPAT_PATH}/lib > /etc/ld.so.conf.d/00-cuda-compat.conf  && ldconfig  && rm -f ${_CUDA_COMPAT_PATH}/lib

# python3, python3-pip and some pip installs required for the python backend
RUN apt-get update &&     apt-get install -y --no-install-recommends             python3 libarchive-dev             python3-pip             libpython3-dev &&     pip3 install --upgrade pip &&     pip3 install --upgrade wheel setuptools &&     pip3 install --upgrade numpy &&     rm -rf /var/lib/apt/lists/*

WORKDIR /opt/tritonserver
RUN rm -fr /opt/tritonserver/*
ENV NVIDIA_PRODUCT_NAME="Triton Server"
COPY docker/entrypoint.d/ /opt/nvidia/entrypoint.d/

ENV NVIDIA_BUILD_ID 48581223
LABEL com.nvidia.build.id=48581223
LABEL com.nvidia.build.ref=672b06cfa8c8be41ca941d58cf70fa73046860e1

WORKDIR /opt/tritonserver
COPY --chown=1000:1000 --from=full /opt/tritonserver/LICENSE .
COPY --chown=1000:1000 --from=full /opt/tritonserver/TRITON_VERSION .
COPY --chown=1000:1000 --from=full /opt/tritonserver/NVIDIA_Deep_Learning_Container_License.pdf .
COPY --chown=1000:1000 --from=full /opt/tritonserver/bin bin/
COPY --chown=1000:1000 --from=full /opt/tritonserver/lib lib/
COPY --chown=1000:1000 --from=full /opt/tritonserver/include include/
# Copying over backends
COPY --chown=1000:1000 --from=full /opt/tritonserver/backends/python /opt/tritonserver/backends/python
COPY --chown=1000:1000 --from=full /opt/tritonserver/backends/fil /opt/tritonserver/backends/fil

# Top-level /opt/tritonserver/backends not copied so need to explicitly set permissions here
RUN chown triton-server:triton-server /opt/tritonserver/backends
#  Copying over repoagents

LABEL com.amazonaws.sagemaker.capabilities.accept-bind-to-port=true
COPY --chown=1000:1000 --from=full /usr/bin/serve /usr/bin/.

RUN echo "deb [signed-by=/usr/share/keyrings/cloud.google.gpg] http://packages.cloud.google.com/apt cloud-sdk main" | tee -a /etc/apt/sources.list.d/google-cloud-sdk.list && curl https://packages.cloud.google.com/apt/doc/apt-key.gpg | apt-key --keyring /usr/share/keyrings/cloud.google.gpg  add - && apt-get update -y && apt-get install google-cloud-sdk -y

WORKDIR /src

COPY ./entrypoint.sh ./

ENV LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/usr/local/cuda/compat/lib.real:/usr/local/hugectr/lib:/usr/local/cuda/extras/CUPTI/lib64:/usr/local/cuda/compat/lib:/usr/local/nvidia/lib:/usr/local/nvidia/lib64:/usr/local/cuda/lib64:/usr/local/cuda/extras/CUPTI/lib64:/usr/local/lib:/repos/dist/lib
