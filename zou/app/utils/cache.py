"""Redis-backed memoization cache.

Zou can run on multiple FaaS instances, so memoized data must be shared
across instances. Local Flask-Caching backends such as SimpleCache are
intentionally rejected instead of silently hiding cache failures.
"""

import redis

from flask_caching import Cache
from zou.app import config
from zou.app.utils.redis import get_redis_url

LOCAL_CACHE_TYPES = {"simple", "null", "filesystem"}


def _normalize_cache_type(cache_type):
    if cache_type is None:
        return None
    return cache_type.strip().lower()


def _validate_cache_type(cache_type):
    if cache_type in LOCAL_CACHE_TYPES:
        raise RuntimeError(
            "Local cache backend '%s' is not supported. "
            "Use Redis for Zou memoization cache." % cache_type
        )
    if cache_type not in (None, "redis"):
        raise RuntimeError(
            "Unsupported cache backend '%s'. Use CACHE_TYPE=redis or unset it."
            % cache_type
        )


def _build_redis_cache_config():
    try:
        redis_cache = redis.StrictRedis(
            host=config.KEY_VALUE_STORE["host"],
            port=config.KEY_VALUE_STORE["port"],
            db=config.MEMOIZE_DB_INDEX,
            username=config.KEY_VALUE_STORE.get("username"),
            password=config.KEY_VALUE_STORE["password"],
            decode_responses=True,
        )
        redis_cache.ping()
    except redis.RedisError as exception:
        raise RuntimeError(
            "Redis memoization cache is unavailable. "
            "Zou will not fall back to a local cache backend."
        ) from exception

    return {
        "CACHE_TYPE": "redis",
        "CACHE_REDIS_URL": get_redis_url(config.MEMOIZE_DB_INDEX),
    }


def _build_cache():
    cache_type = _normalize_cache_type(config.CACHE_TYPE)
    _validate_cache_type(cache_type)
    return Cache(config=_build_redis_cache_config())


cache = _build_cache()


def memoize_function(timeout=120):
    def decorator(func):
        return cache.memoize(timeout)(func)

    return decorator


def invalidate(*args):
    cache.delete_memoized(*args)


def clear():
    cache.clear()
