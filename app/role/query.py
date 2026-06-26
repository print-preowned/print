from datetime import datetime, timezone
from bson import ObjectId
from app.utility.model import PaginatedData, Pagination, ParamRequest, PyObjectId
from ..utility.database import get_database
from .model import Role, RoleCreateRequest, RoleUpdateRequest
import math

db = get_database()
collection = db["role"]


async def create_query(role: RoleCreateRequest) -> PyObjectId:
    data = role.model_dump()
    now = datetime.now(timezone.utc)
    data["updated_at"] = now
    data["created_at"] = now
    data["status"] = "ACTIVE"

    result = await collection.insert_one(data)
    return PyObjectId(result.inserted_id)


async def update_query(id: str, role: RoleUpdateRequest):
    data = role.model_dump(exclude_unset=True)
    data["updated_at"] = datetime.utcnow()

    return await collection.update_one({"_id": ObjectId(id)}, {"$set": data})


async def delete_query(id: str):
    return await collection.update_one(
        {"_id": ObjectId(id)}, {"$set": {"status": "DELETED"}}
    )


async def read_query(params: ParamRequest) -> PaginatedData[Role]:
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
        data=[Role.model_validate(record) for record in records],
        pagination=Pagination(
            page=page, size=size, total_pages=total_pages, total_results=total_results
        ),
    )


async def read_by_id_query(id: str) -> Role | None:
    record = await collection.find_one(
        {"_id": ObjectId(id), "status": {"$ne": "DELETED"}}
    )
    if not record:
        return None
    return Role.model_validate(record)


async def read_by_code_query(code: str) -> Role | None:
    """Find a role by code"""
    record = await collection.find_one(
        {"code": code, "status": {"$ne": "DELETED"}}
    )
    if not record:
        return None
    return Role.model_validate(record)


