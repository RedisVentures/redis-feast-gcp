import pickle
import redis.asyncio as redis


class ModelRepo:
    model_prefix = "model"
    versions = "versions"
    latest = "latest"
    latest_version = None
    model_name = None


    def __init__(self, host: str, port: str, password: str):
        """
        ModelRepo is a basic storage and versioning layer for ML models using
        Redis as the backend.

        Args:
            host (str): Redis host.
            port (str): Redis port.
            password (str): Redis password.
        """
        self.redis_client = redis.Redis(
            host=host,
            port=port,
            password=password,
            decode_responses=True
        )

    async def setup(self, model_name: str):
        """
        Set up the model repository in Redis. Must call this first before using
        the repo.

        Args:
            model_name (str): Name of the model we want to use/track.
        """
        self.model_name = model_name
        self.latest_version = await self.redis_client.hlen(self.model_versions)

    def model_versions(self) -> str:
        return f"{self.model_prefix}:{self.model_name}:{self.versions}"

    async def save_version(self, model) -> int:
        """
        Persist the model in the database and increment
        the version count.

        Args:
            model: Model object to store.

        Returns:
            int: Model version number.
        """
        pickle_out = pickle.dumps(model)
        new_version = self.latest_version + 1
        res = await self.redis_client.hset(
            name=self.model_versions,
            key=str(new_version),
            value=pickle_out
        )
        if res:
            # TODO some checks... increment version
            self.latest_version = new_version
            return self.latest_version

    async def fetch_version(self, version: int):
        """
        Fetch model by version.

        Args:
            version (int): Model version number to fetch.
        """
        res = await self.redis_client.hget(
            name=self.model_versions(),
            key=str(version)
        )
        if res:
            pickle_out = pickle.loads(res)
            return pickle_out

    async def fetch_all_versions(self) -> dict:
        """
        Fetch all model versions.

        Returns:
            dict: Dictionary of model_version : model object.
        """
        res = await self.redis_client.hgetall(name=self.model_versions())
        if res:
            return {k: pickle.loads(v) for k, v in res.items()}

    async def fetch_latest(self):
        """
        Fetch the latest model version.
        """
        res = await self.redis_client.hget(
            name=self.model_versions(),
            key=str(self.latest_version)
        )
        if res:
            pickle_out = pickle.loads(res)
            return pickle_out