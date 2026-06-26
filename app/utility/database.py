import certifi
from motor.motor_asyncio import AsyncIOMotorClient

from app.utility.config import get_settings


def get_database():
    settings = get_settings()
    kwargs: dict = {}
    if settings.mongodb_uri.startswith("mongodb+srv://"):
        kwargs["tls"] = True
        kwargs["tlsCAFile"] = certifi.where()
        kwargs["serverSelectionTimeoutMS"] = 30000

    client = AsyncIOMotorClient(settings.mongodb_uri, **kwargs)
    return client[settings.mongodb_db_name]
