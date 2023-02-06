# Set up a global error handler
err_handler() {
    echo "Error on line: $1"
    echo "Caused by: $2"
    echo "That returned exit status: $3"
    echo "Aborting..."
    exit $3
}

trap 'err_handler "$LINENO" "$BASH_COMMAND" "$?"' ERR


if [ -z "${AIP_STORAGE_URI}" ]
  then
    echo 'AIP_STORAGE_URI not set. Exiting ....'
    exit 1
fi

MODEL_REPOSITORY=/model

echo "Copying model ensemble from ${AIP_STORAGE_URI} to ${MODEL_REPOSITORY}"
mkdir ${MODEL_REPOSITORY} 
gsutil -m cp -r ${AIP_STORAGE_URI}/* ${MODEL_REPOSITORY}

# gsutil does not copy empty dirs so create a version folder for the ensemble
ENSEMBLE_DIR=$(ls ${MODEL_REPOSITORY} | grep ens)
mkdir ${MODEL_REPOSITORY}/${ENSEMBLE_DIR}/1

echo "Starting Triton Server"
tritonserver --vertex-ai-default-model=ensemble --model-repository=$MODEL_REPOSITORY --backend-config=python,shm-default-byte-size=16777216 --log-verbose=3 --log-info=1 --log-warning=1 --log-error=1