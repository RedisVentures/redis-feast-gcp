# Import the configs for featureform
import featureform as ff

from feature_store.repo import (
    FF_0_config as config,
    FF_1_providers as providers,
    FF_4_transformations as transformations,
    FF_5_registering_sets as reg_sets,
)
from feature_store.utils import logger, storage


if __name__ == "__main__":
    # Setup logger
    logging = logger.get_logger()

    # Connect to featureform host
    logging.info("Connecting to GKE cluster with Featureform")
    client = ff.ResourceClient(f"{config.FEATUREFORM_HOST}")

    # TODO: Register providers (Bigquery & Redis) with Featureform
    logging.info("Register BigQuery & Redis as providers with Featureform")
    bigquery, redis = providers.register_providers(ff)

    # TODO: Register Sets with Featureform
    logging.info("Registering entity with Featureform")
    # Define an entity for the state.
    # You can think of an entity as a primary key used to
    state = ff.register_entity("state")

    # TODO: Defining & Registering Transformations with Featureform
    transformations.register_vaccine_search_trends(bigquery, redis, state)
    transformations.register_vaccine_counts(bigquery, redis, state)

    logging.info("Registering training & serving sets with Featureform")
    reg_sets.register_sets(ff)

    # TODO: Apply
    client.apply()
