import requests
import pickle

from feast import FeatureStore
from google.cloud import storage
from typing import Any


def get_feature_store(
    config_path: str,
    bucket_name: str
) -> FeatureStore:
    """
    Fetch the Feast Feature Store using the repo config stored
    in GCS.

    Returns:
        FeatureStore: Feast FeatureStore
    """
    return FeatureStore(
        config = fetch_pkl(
            remote_filename=config_path,
            bucket_name=bucket_name
        )
    )

def get_blob(
    remote_filename: str,
    bucket_name: str
):
    """
    Grab a pointer to the GCS blob in bucket.

    Args:
        remote_filename (str): Path to the remote file within the GCS bucket.
        bucket_name (str): Name of the GCS bucket.
    """
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(remote_filename)
    return blob


def upload_file(
    local_filename: str,
    bucket_name: str,
    remote_filename: str
) -> None:
    """
    Upload a local file to GCS (Google Cloud Storage) bucket

    Args:
        local_filename (str): Path to the local file to upload to GCS.
        bucket_name (str): Name of the GCS bucket.
        remote_filename (str): Path to the remote file within the GCS bucket.
    """
    blob = get_blob(remote_filename, bucket_name)
    blob.upload_from_filename(local_filename)

def upload_pkl(
    obj: Any,
    bucket_name: str,
    remote_filename: str,
) -> None:
    """
    Upload an object to GCS as a pickle file.

    Args:
        obj (Any): Some object.
        bucket_name (str): Name of the GCS bucket.
        remote_filename (str): Path to the remote file within the GCS bucket.
    """
    blob = get_blob(remote_filename, bucket_name)
    pickle_out = pickle.dumps(obj)
    blob.upload_from_string(pickle_out)

def fetch_pkl(
    bucket_name: str,
    remote_filename: str
) -> Any:
    """
    Fetch a pickled object from GCS.

    Args:
        bucket_name (str): Name of the GCS bucket.
        remote_filename (str): Path to the remote file within the GCS bucket.

    Returns:
        Any: Some object.
    """
    # Get the blob and download
    blob = get_blob(remote_filename, bucket_name)
    pickle_in = blob.download_as_string()
    obj = pickle.loads(pickle_in)
    return obj


def download_file_url(
    filename: str,
    url: str
):
    """
    Download a file by iterating over chunks of content and
    saving it to a local file.

    Args:
        filename (str): Filename to store the resulting data in.
        url (str): URL to fetch the file from.
    """
    with requests.get(url, stream=True) as r:
        r.raise_for_status()
        with open(filename, 'wb') as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)