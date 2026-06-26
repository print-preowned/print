from datetime import datetime, timezone, timedelta
from typing import Optional
from bson import ObjectId
from app.utility.model import PyObjectId
from app.utility.database import get_database
from .model import PasswordResetToken
import hashlib

db = get_database()
collection = db["password_reset_token"]


def hash_token(token: str) -> str:
    """Hash a token using SHA-256"""
    return hashlib.sha256(token.encode()).hexdigest()


async def create_query(user_id: PyObjectId, token_hash: str, expires_at: datetime) -> ObjectId:
    """Create a password reset token with hashed token"""
    data = {
        "user_id": ObjectId(user_id),
        "token_hash": token_hash,
        "expires_at": expires_at,
        "used": False,
        "created_at": datetime.now(timezone.utc),
        "used_at": None,
    }
    result = await collection.insert_one(data)
    return result.inserted_id


async def read_by_token_hash_query(token_hash: str) -> PasswordResetToken | None:
    """Find a password reset token by token hash"""
    record = await collection.find_one({"token_hash": token_hash})
    if not record:
        return None
    return PasswordResetToken.model_validate(record)


async def mark_as_used_query(id: str):
    """Mark a password reset token as used"""
    return await collection.update_one(
        {"_id": ObjectId(id)},
        {"$set": {"used": True, "used_at": datetime.now(timezone.utc)}}
    )


async def mark_expired_query():
    """Mark expired tokens (cleanup - optional)"""
    now = datetime.now(timezone.utc)
    # This is optional - we check expiration in service layer
    pass
