from datetime import datetime, timezone, timedelta
from typing import Optional
from bson import ObjectId
from app.utility.model import PaginatedData, Pagination, ParamRequest, PyObjectId
from ..utility.database import get_database
from .model import PlatformInvite, PlatformInviteCreateRequest
import math
import hashlib
import re

db = get_database()
collection = db["platform_invite"]


def hash_token(token: str) -> str:
    """Hash a token using SHA-256 (MDC-PU-S-4: raw_invite_tokens_are_never_stored)"""
    return hashlib.sha256(token.encode()).hexdigest()


async def read_pending_by_email_query(email: str) -> PlatformInvite | None:
    """Find a pending invite for an email (case-insensitive)."""
    record = await collection.find_one(
        {
            "email": {"$regex": f"^{re.escape(email)}$", "$options": "i"},
            "status": "PENDING",
        }
    )
    if not record:
        return None
    return PlatformInvite.model_validate(record)


async def resend_pending_query(
    id: str,
    *,
    token_hash: str,
    platform_privilege_set_id: ObjectId,
    expires_at: datetime,
    updated_by: PyObjectId,
) -> bool:
    """Update a pending invite with a new token, privilege set, and expiry."""
    result = await collection.update_one(
        {"_id": ObjectId(id), "status": "PENDING"},
        {
            "$set": {
                "token_hash": token_hash,
                "platform_privilege_set_id": platform_privilege_set_id,
                "expires_at": expires_at,
                "updated_at": datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc),
                "updated_by": updated_by,
            }
        },
    )
    return result.matched_count > 0


async def create_query(invite: PlatformInviteCreateRequest, token_hash: str, invited_by: PyObjectId, expires_at: datetime) -> ObjectId:
    """Create a platform invite with hashed token"""
    data = {
        "email": invite.email,
        "platform_privilege_set_id": ObjectId(invite.platform_privilege_set_id),
        "token_hash": token_hash,
        "expires_at": expires_at,
        "status": "PENDING",
        "invited_by": ObjectId(invited_by),
        "created_at": datetime.now(timezone.utc),
        "accepted_at": None,
    }
    result = await collection.insert_one(data)
    return result.inserted_id


async def read_query(params: ParamRequest) -> PaginatedData[PlatformInvite]:
    """Read platform invites with pagination"""
    page = max(1, params.page)
    size = params.size

    total_results = await collection.count_documents({"status": {"$ne": "EXPIRED"}})
    total_pages = math.ceil(total_results / size) if size else 1
    cursor = (
        collection.find({"status": {"$ne": "EXPIRED"}})
        .skip((page - 1) * size)
        .limit(size)
    )
    records = await cursor.to_list(length=size)

    return PaginatedData(
        data=[PlatformInvite.model_validate(record) for record in records],
        pagination=Pagination(
            page=page, size=size, total_pages=total_pages, total_results=total_results
        ),
    )


async def read_by_id_query(id: str) -> PlatformInvite | None:
    """Read a platform invite by ID"""
    record = await collection.find_one({"_id": ObjectId(id)})
    if not record:
        return None
    return PlatformInvite.model_validate(record)


async def read_by_token_hash_query(token_hash: str) -> PlatformInvite | None:
    """Find a platform invite by token hash (MDC-PU-S-3: invite_validation)"""
    record = await collection.find_one({"token_hash": token_hash})
    if not record:
        return None
    return PlatformInvite.model_validate(record)


async def update_status_query(id: str, status: str, accepted_at: Optional[datetime] = None):
    """Update invite status (accepted, rejected, expired)"""
    update_data = {
        "status": status,
        "updated_at": datetime.now(timezone.utc),
    }
    if accepted_at:
        update_data["accepted_at"] = accepted_at
    
    return await collection.update_one(
        {"_id": ObjectId(id)},
        {"$set": update_data}
    )


async def mark_expired_query():
    """Mark expired invites as expired (MDC-PU-S-3: invite_tokens_are_single_use_and_expiring)"""
    now = datetime.now(timezone.utc)
    return await collection.update_many(
        {
            "status": "PENDING",
            "expires_at": {"$lt": now}
        },
        {"$set": {"status": "EXPIRED", "updated_at": now}}
    )
