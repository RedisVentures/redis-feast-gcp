from feast import FeatureStore
from repo import config
from utils import file


if __name__ == '__main__':

    # Fetch repo config from storage
    repo_config = file.fetch_pkl_frm_gcs(
        remote_filename=config.REPO_CONFIG,
        bucket_name=config.BUCKET_NAME
    )

    # Create FeatureStore
    store = FeatureStore(config=repo_config)

    # Teardown
    print("Tearing down feature store")
    store.teardown()
