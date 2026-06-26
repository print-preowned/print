import os
from dataclasses import dataclass
from functools import lru_cache

from dotenv import load_dotenv

load_dotenv()


def _env_bool(name: str, default: bool = False) -> bool:
    value = os.environ.get(name)
    if value is None:
        return default
    return value.lower() in ("1", "true", "yes")


@dataclass(frozen=True)
class Settings:
    app_env: str
    jwt_secret: str
    mongodb_uri: str
    mongodb_db_name: str
    redis_host: str
    redis_port: int
    redis_password: str | None
    redis_db: int
    redis_ssl: bool


@lru_cache
def get_settings() -> Settings:
    app_env = os.environ.get("APP_ENV", "development")
    jwt_default = "secret" if app_env != "production" else ""
    jwt_secret = os.environ.get("JWT_SECRET", jwt_default)
    if app_env == "production" and not jwt_secret:
        raise RuntimeError("JWT_SECRET is required when APP_ENV=production")

    return Settings(
        app_env=app_env,
        jwt_secret=jwt_secret,
        mongodb_uri=os.environ.get("MONGODB_URI", "mongodb://localhost:27017"),
        mongodb_db_name=os.environ.get("MONGODB_DB_NAME", "print"),
        redis_host=os.environ.get("REDIS_HOST", "localhost"),
        redis_port=int(os.environ.get("REDIS_PORT", "6379")),
        redis_password=os.environ.get("REDIS_PASSWORD"),
        redis_db=int(os.environ.get("REDIS_DB", "0")),
        redis_ssl=_env_bool("REDIS_SSL"),
    )
