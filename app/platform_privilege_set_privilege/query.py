from datetime import datetime, timezone
from bson import ObjectId
from typing import List
from app.utility.model import PaginatedData, Pagination, ParamRequest
from ..utility.database import get_database
from .model import PlatformPrivilegeSetPrivilege, PlatformPrivilegeSetPrivilegeCreateRequest, PlatformPrivilegeSetPrivilegeUpdateRequest
import math

db = get_database()
collection = db["platform_privilege_set_privilege"]


async def create_query(mapping: PlatformPrivilegeSetPrivilegeCreateRequest):
    data = mapping.model_dump()
    now = datetime.now(timezone.utc)
    data["updated_at"] = now
    data["created_at"] = now
    data["status"] = "ACTIVE"

    await collection.insert_one(data)


async def update_query(id: str, mapping: PlatformPrivilegeSetPrivilegeUpdateRequest):
    data = mapping.model_dump(exclude_unset=True)
    data["updated_at"] = datetime.now(timezone.utc)

    return await collection.update_one({"_id": ObjectId(id)}, {"$set": data})


async def delete_query(id: str):
    return await collection.update_one(
        {"_id": ObjectId(id)}, {"$set": {"status": "DELETED"}}
    )


async def read_query(params: ParamRequest) -> PaginatedData[PlatformPrivilegeSetPrivilege]:
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
        data=[PlatformPrivilegeSetPrivilege.model_validate(record) for record in records],
        pagination=Pagination(
            page=page, size=size, total_pages=total_pages, total_results=total_results
        ),
    )


async def read_by_id_query(id: str) -> PlatformPrivilegeSetPrivilege | None:
    record = await collection.find_one(
        {"_id": ObjectId(id), "status": {"$ne": "DELETED"}}
    )
    if not record:
        return None
    return PlatformPrivilegeSetPrivilege.model_validate(record)


async def read_by_privilege_set_id_query(privilege_set_id: str) -> List[PlatformPrivilegeSetPrivilege]:
    """Find all privilege mappings for a privilege set"""
    cursor = collection.find(
        {"privilege_set_id": ObjectId(privilege_set_id), "status": {"$ne": "DELETED"}}
    )
    records = await cursor.to_list(length=None)
    return [PlatformPrivilegeSetPrivilege.model_validate(record) for record in records]


async def read_by_privilege_set_and_privilege_query(privilege_set_id: str, privilege_code: str) -> PlatformPrivilegeSetPrivilege | None:
    """Find a mapping by privilege_set_id and privilege_code"""
    record = await collection.find_one(
        {
            "privilege_set_id": ObjectId(privilege_set_id),
            "privilege_code": privilege_code,
            "status": {"$ne": "DELETED"}
        }
    )
    if not record:
        return None
    return PlatformPrivilegeSetPrivilege.model_validate(record)


async def delete_by_privilege_set_and_privilege_query(privilege_set_id: str, privilege_code: str):
    """Delete a mapping by privilege_set_id and privilege_code"""
    return await collection.update_one(
        {
            "privilege_set_id": ObjectId(privilege_set_id),
            "privilege_code": privilege_code,
            "status": {"$ne": "DELETED"}
        },
        {"$set": {"status": "DELETED"}}
    )
