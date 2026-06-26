from functools import lru_cache

import redis

from app.utility.config import get_settings


@lru_cache
def _redis_client() -> redis.Redis:
    settings = get_settings()
    return redis.Redis(
        host=settings.redis_host,
        port=settings.redis_port,
        db=settings.redis_db,
        password=settings.redis_password,
        ssl=settings.redis_ssl,
    )


def set_key(key: str, value: str, ex: int = 60 * 60 * 24):
    _redis_client().set(key, value, ex=ex)


def get_key(key: str):
    return _redis_client().get(key)


def delete_key(key: str):
    _redis_client().delete(key)
