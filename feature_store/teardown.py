from repo import config

from feast import FeatureStore


if __name__ == '__main__':

    # Fetch repo config from storage
    repo_config = config.load_repo_config()

    # Create FeatureStore
    store = FeatureStore(config=repo_config)

    # Teardown
    store.teardown()