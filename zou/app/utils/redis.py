from urllib.parse import quote

from zou.app import config


def get_redis_url(db_index):
    redis_host = config.KEY_VALUE_STORE["host"]
    redis_port = config.KEY_VALUE_STORE["port"]
    redis_username = config.KEY_VALUE_STORE["username"]
    redis_password = config.KEY_VALUE_STORE["password"]

    if redis_username and redis_password:
        credentials = f"{quote(redis_username)}:{quote(redis_password)}@"
    elif redis_password:
        credentials = f":{quote(redis_password)}@"
    else:
        credentials = ""

    return f"redis://{credentials}{redis_host}:{redis_port}/{db_index}"
