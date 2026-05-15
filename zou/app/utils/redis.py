from urllib.parse import quote

from zou.app import config


def get_redis_url(db_index):
    redis_host = config.KEY_VALUE_STORE["host"]
    redis_port = config.KEY_VALUE_STORE["port"]
    username = config.KEY_VALUE_STORE.get("username")
    password = config.KEY_VALUE_STORE.get("password")
    if password:
        auth = f"{quote(username or '', safe='')}:{quote(password, safe='')}@"
    else:
        auth = ""
    return f"redis://{auth}{redis_host}:{redis_port}/{db_index}"
