import redis

from rq import Queue
from zou.app import config


try:
    if config.ENABLE_JOB_QUEUE:
        queue_store = redis.StrictRedis(
            host=config.KEY_VALUE_STORE["host"],
            port=config.KEY_VALUE_STORE["port"],
            db=config.KV_JOB_DB_INDEX,
            username=config.KEY_VALUE_STORE.get("username"),
            password=config.KEY_VALUE_STORE["password"],
            decode_responses=True,
            **config.KEY_VALUE_STORE_SOCKET_OPTIONS,
        )
        queue_store.ping()
except redis.RedisError as exception:
    raise RuntimeError(
        "Redis job queue store is unavailable. "
        "Zou will not fall back to an in-memory queue."
    ) from exception

if config.ENABLE_JOB_QUEUE:
    job_queue = Queue(connection=queue_store)
