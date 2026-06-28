from datetime import datetime, timezone
from bson import ObjectId
from app.utility.model import PaginatedData, Pagination, ParamRequest
from ..utility.database import get_database
from .model import PlatformPrivilegeSet, PlatformPrivilegeSetCreateRequest, PlatformPrivilegeSetUpdateRequest
import math

db = get_database()
collection = db["platform_privilege_set"]


async def create_query(platform_privilege_set: PlatformPrivilegeSetCreateRequest):
    data = platform_privilege_set.model_dump()
    now = datetime.now(timezone.utc)
    data["updated_at"] = now
    data["created_at"] = now
    data["status"] = "ACTIVE"

    await collection.insert_one(data)


async def update_query(id: str, platform_privilege_set: PlatformPrivilegeSetUpdateRequest):
    data = platform_privilege_set.model_dump(exclude_unset=True)
    data["updated_at"] = datetime.now(timezone.utc)

    return await collection.update_one({"_id": ObjectId(id)}, {"$set": data})


async def delete_query(id: str):
    return await collection.update_one(
        {"_id": ObjectId(id)}, {"$set": {"status": "DELETED"}}
    )


async def read_query(params: ParamRequest) -> PaginatedData[PlatformPrivilegeSet]:
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
        data=[PlatformPrivilegeSet.model_validate(record) for record in records],
        pagination=Pagination(
            page=page, size=size, total_pages=total_pages, total_results=total_results
        ),
    )


async def read_by_id_query(id: str) -> PlatformPrivilegeSet | None:
    record = await collection.find_one(
        {"_id": ObjectId(id), "status": {"$ne": "DELETED"}}
    )
    if not record:
        return None
    return PlatformPrivilegeSet.model_validate(record)


async def read_by_ids_query(ids: list[str]) -> list[PlatformPrivilegeSet]:
    """Return privilege sets for given ids (for batch population)."""
    if not ids:
        return []
    oids = [ObjectId(i) for i in ids]
    cursor = collection.find(
        {"_id": {"$in": oids}, "status": {"$ne": "DELETED"}}
    )
    records = await cursor.to_list(length=len(oids))
    return [PlatformPrivilegeSet.model_validate(record) for record in records]
