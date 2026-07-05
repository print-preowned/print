from __future__ import annotations

from bson import ObjectId
from bson.errors import InvalidId


def mongo_user_id_filter(user_id: str) -> dict:
    """Match Mongo user_id stored as ObjectId (legacy) or string UUID."""
    try:
        oid = ObjectId(user_id)
        return {"$or": [{"user_id": oid}, {"user_id": user_id}]}
    except InvalidId:
        return {"user_id": user_id}
