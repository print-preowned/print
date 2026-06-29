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
    web_app_url: str
    smtp_host: str | None
    smtp_port: int
    smtp_user: str | None
    smtp_password: str | None
    smtp_from: str
    smtp_use_tls: bool
    smtp_ssl_verify: bool
    smtp_debug: bool
    assets_cdn_url: str | None


@lru_cache
def get_settings() -> Settings:
    app_env = os.environ.get("APP_ENV", "development")
    jwt_default = "secret" if app_env != "production" else ""
    jwt_secret = os.environ.get("JWT_SECRET", jwt_default)
    if app_env == "production" and not jwt_secret:
        raise RuntimeError("JWT_SECRET is required when APP_ENV=production")

    web_app_default = "http://localhost:3000" if app_env != "production" else ""
    web_app_url = os.environ.get("WEB_APP_URL", web_app_default).rstrip("/")
    if app_env == "production" and not web_app_url:
        raise RuntimeError("WEB_APP_URL is required when APP_ENV=production")

    smtp_from = os.environ.get("SMTP_FROM", "noreply@print.local")

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
        web_app_url=web_app_url,
        smtp_host=os.environ.get("SMTP_HOST"),
        smtp_port=int(os.environ.get("SMTP_PORT", "587")),
        smtp_user=os.environ.get("SMTP_USER"),
        smtp_password=os.environ.get("SMTP_PASSWORD"),
        smtp_from=smtp_from,
        smtp_use_tls=_env_bool("SMTP_USE_TLS", True),
        smtp_ssl_verify=_env_bool("SMTP_SSL_VERIFY", True),
        smtp_debug=_env_bool("SMTP_DEBUG", False),
        assets_cdn_url=os.environ.get("ASSETS_CDN_URL"),
    )
