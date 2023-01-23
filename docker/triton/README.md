# Creating Custom Triton Image

We provide this custom image for you to use, hosted from our GitHub Container Registry at RedisVentures. **But if you wish to re-create, follow these steps. This is NOT required**.

The project requires a Docker image with NVIDIA Triton along with the following customizations:

- Python and FIL backends.
- Smaller size -- down to ~8Gb instead of ~21Gb.
- Custom `ENTRYPOINT` and required libraries.

>If doing yourself, we recommend performing these steps in a linux VM environment with x86_64 CPU architecture.

## Pull Repos and Create FIL Backend
```bash
git clone https://github.com/triton-inference-server/server.git
git clone https://github.com/triton-inference-server/fil_backend.git

cd fil_backend/

BASE_IMAGE=nvcr.io/nvidia/tritonserver:22.11-py3 ./build.sh
```

This will output a Docker image --> `triton_fil_test` image that contains the Triton FIL backend installed over the `22:11` base Triton image.

## Create Custom Triton Image
Now we want to build a custom Triton image with all other backends ripped out (to make it smaller).
```bash
cd ../server/

python3 compose.py --backend python --backend fil --container-version 22.11 --dry-run
```
The `--dry-run` option will creates a Dockerfile. We've included the generated [Dockerfile](../docker/Dockerfile.tritonDockerfile) here.

We added some addition parts from line 80 onwards to handle the custom [`ENTRYPOINT`](./entrypoint.sh) and required libraries:
```dockerfile
RUN echo "deb [signed-by=/usr/share/keyrings/cloud.google.gpg] http://packages.cloud.google.com/apt cloud-sdk main" | tee -a /etc/apt/sources.list.d/google-cloud-sdk.list && curl https://packages.cloud.google.com/apt/doc/apt-key.gpg | apt-key --keyring /usr/share/keyrings/cloud.google.gpg  add - && apt-get update -y && apt-get install google-cloud-sdk -y

WORKDIR /src

COPY ./entrypoint.sh ./

ENV LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/usr/local/cuda/compat/lib.real:/usr/local/hugectr/lib:/usr/local/cuda/extras/CUPTI/lib64:/usr/local/cuda/compat/lib:/usr/local/nvidia/lib:/usr/local/nvidia/lib64:/usr/local/cuda/lib64:/usr/local/cuda/extras/CUPTI/lib64:/usr/local/lib:/repos/dist/lib

ENTRYPOINT ./entrypoint.sh
```

## Build Image, Tag, Push
Easiest part last:

```bash
docker build -t $GCP_REGION-docker.pkg.dev/$PROJECT_ID/nvidia-triton/vertex-triton-inference:latest -f docker/Dockerfile.triton .
```

Push image:
```bash
gcloud auth configure-docker $GCP_REGION-docker.pkg.dev
docker push $GCP_REGION-docker.pkg.dev/$PROJECT_ID/nvidia-triton/vertex-triton-inference:latest
```