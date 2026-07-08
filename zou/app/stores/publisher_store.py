import redis

from flask_socketio import SocketIO

from zou.app import config
from zou.app.utils.redis import get_redis_url

socketio = None


def publish(event, data):
    if socketio is not None:
        socketio.emit(event, data, namespace="/events")


def init():
    """
    Initialize key value store that will be used for the event publishing.
    That way the main API takes advantage of Redis pub/sub capabilities to push
    events to the event stream API.
    """
    global socketio

    try:
        publisher_store = redis.StrictRedis(
            host=config.KEY_VALUE_STORE["host"],
            port=config.KEY_VALUE_STORE["port"],
            db=config.KV_EVENTS_DB_INDEX,
            username=config.KEY_VALUE_STORE.get("username"),
            password=config.KEY_VALUE_STORE["password"],
            decode_responses=True,
            **config.KEY_VALUE_STORE_SOCKET_OPTIONS,
        )
        publisher_store.ping()
    except redis.RedisError as exception:
        raise RuntimeError(
            "Redis event publisher is unavailable. "
            "Zou will not silently disable event publishing."
        ) from exception

    socketio = SocketIO(
        message_queue=get_redis_url(config.KV_EVENTS_DB_INDEX),
        cors_allowed_origins=[],
        cors_credentials=False,
    )

    return socketio
