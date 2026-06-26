from datetime import datetime, timezone
from typing import List
from bson import ObjectId
from app.utility.model import PaginatedData, Pagination, ParamRequest
from ..utility.database import get_database
from .model import RolePrivilege, RolePrivilegeCreateRequest, RolePrivilegeUpdateRequest
import math

db = get_database()
collection = db["role_privilege"]


async def create_query(mapping: RolePrivilegeCreateRequest):
    data = mapping.model_dump()
    now = datetime.now(timezone.utc)
    data["updated_at"] = now
    data["created_at"] = now
    data["status"] = "ACTIVE"

    await collection.insert_one(data)


async def update_query(id: str, mapping: RolePrivilegeUpdateRequest):
    data = mapping.model_dump(exclude_unset=True)
    data["updated_at"] = datetime.utcnow()

    return await collection.update_one({"_id": ObjectId(id)}, {"$set": data})


async def delete_query(id: str):
    return await collection.update_one(
        {"_id": ObjectId(id)}, {"$set": {"status": "DELETED"}}
    )


async def read_query(params: ParamRequest) -> PaginatedData[RolePrivilege]:
    page = max(1, params.page)
    size = params.size

    total_results = await collection.count_documents({"status": {"$ne": "DELETED"}})
    total_pages = math.ceil(total_results / size) if size else 1
    cursor = (
        collection.find({"status": {"$ne": "DELETED"}})
        .skip((page - 1) * size)
        .limit(size)
    )
    records = await cursor.to_list(length=size)

    return PaginatedData(
        data=[RolePrivilege.model_validate(record) for record in records],
        pagination=Pagination(
            page=page, size=size, total_pages=total_pages, total_results=total_results
        ),
    )


async def read_by_id_query(id: str) -> RolePrivilege | None:
    record = await collection.find_one(
        {"_id": ObjectId(id), "status": {"$ne": "DELETED"}}
    )
    if not record:
        return None
    return RolePrivilege.model_validate(record)


async def read_by_role_and_privilege_query(role_id: str, privilege_code: str) -> RolePrivilege | None:
    """Find a role_privilege mapping by role_id and privilege_code"""
    record = await collection.find_one(
        {
            "role_id": ObjectId(role_id),
            "privilege_code": privilege_code,
            "status": {"$ne": "DELETED"}
        }
    )
    if not record:
        return None
    return RolePrivilege.model_validate(record)


async def read_by_privilege_code_query(privilege_code: str) -> List[RolePrivilege]:
    """Find all role_privilege mappings for a privilege code"""
    cursor = collection.find(
        {"privilege_code": privilege_code, "status": {"$ne": "DELETED"}}
    )
    records = await cursor.to_list(length=None)
    return [RolePrivilege.model_validate(record) for record in records]


async def read_privilege_codes_by_role_id_query(role_id: str) -> List[str]:
    """Return privilege codes for a role (for token materialization)."""
    cursor = collection.find(
        {"role_id": ObjectId(role_id), "status": {"$ne": "DELETED"}}
    )
    records = await cursor.to_list(length=None)
    return [r["privilege_code"] for r in records]


async def delete_by_role_and_privilege_query(role_id: str, privilege_code: str):
    """Delete a role_privilege mapping by role_id and privilege_code"""
    return await collection.update_one(
        {
            "role_id": ObjectId(role_id),
            "privilege_code": privilege_code,
            "status": {"$ne": "DELETED"}
        },
        {"$set": {"status": "DELETED"}}
    )


