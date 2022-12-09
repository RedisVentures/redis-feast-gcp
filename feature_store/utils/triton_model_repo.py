from .logger import get_logger
from google.cloud import storage


logging = get_logger()

class TritonGCSModelRepo:
    repo_name = "models"
    versions = []
    latest_version = 0
    model_name = None

    def __init__(
        self,
        bucket_name: str,
        model_name: str,
        model_filename: str
    ):
        """
        TritonModelRepo is a basic storage and versioning layer for ML models using
        Redis as the backend.
        """
        self.bucket_name = bucket_name
        self.model_name = model_name
        self.model_filename = model_filename
        self.storage_client = storage.Client()
        self.bucket = self.storage_client.bucket(bucket_name)
        self._refresh()

    def _refresh(self):
        self.versions = self.list_versions()
        self.latest_version = len(self.versions)

    def _version_path(self, version: str) -> str:
        return f"{self.repo_name}/{self.model_name}/{version}"

    def create(self, config: str):
        path = f"{self.repo_name}/{self.model_name}/config.pbtxt"
        blob = self.bucket.blob(path)
        if not blob.exists():
            logging.info(f"Creating Model Repository for {self.model_name}")
            blob.upload_from_string(config)
        else:
            logging.info(f"Model Repository already exists.")

    def list_versions(self):
        blobs = [
            blob.name for blob in
            self.bucket.list_blobs(prefix=f"{self.repo_name}/{self.model_name}")
            if ".pbtxt" not in blob.name
        ]
        return blobs

    def save_version(self, model_path: str, version: int = None) -> int:
        """
        Persist the model in GCS and increment
        the version count.

        Args:
            model: Model object to store.

        Returns:
            int: Model version number.
        """
        if not version:
            version = self.latest_version + 1
            logging.info(f"Saving new model version {version}.")
        path = f"{self._version_path(version)}/{self.model_filename}"
        blob = self.bucket.blob(path)
        blob.upload_from_filename(model_path)
        logging.info(f"Saved model version {version}.")
        self._refresh()
        return version

    def fetch_version(self, version: int) -> str:
        """
        Fetch model by version.

        Args:
            version (int): Model version number to fetch.
        """
        path = f"{self._version_path(version)}/{self.model_filename}"


    def fetch_latest(self) -> str:
        """
        Fetch the latest model version.
        """
        path = f"{self._version_path(self.latest_version)}/{self.model_filename}"
