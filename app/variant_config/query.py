from datetime import datetime, timezone
from bson import ObjectId
from app.utility.model import PaginatedData, Pagination, ParamRequest
from ..utility.database import get_database
from .model import (
    VariantConfig,
    VariantConfigCreateRequest,
    VariantConfigUpdateRequest,
)
import math

db = get_database()
collection = db["variant_config"]


async def create_query(item: VariantConfigCreateRequest):
    data = item.model_dump()
    now = datetime.now(timezone.utc)
    data["updated_at"] = now
    data["created_at"] = now
    data["status"] = "ACTIVE"

    await collection.insert_one(data)


async def update_query(id: str, item: VariantConfigUpdateRequest):
    data = item.model_dump(exclude_unset=True)
    data["updated_at"] = datetime.now(timezone.utc)

    return await collection.update_one({"_id": ObjectId(id)}, {"$set": data})


async def delete_query(id: str):
    return await collection.update_one(
        {"_id": ObjectId(id)}, {"$set": {"status": "DELETED"}}
    )


async def read_query(params: ParamRequest) -> PaginatedData[VariantConfig]:
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
        data=[VariantConfig.model_validate(record) for record in records],
        pagination=Pagination(
            page=page, size=size, total_pages=total_pages, total_results=total_results
        ),
    )


async def read_by_id_query(id: str) -> VariantConfig | None:
    record = await collection.find_one(
        {"_id": ObjectId(id), "status": {"$ne": "DELETED"}}
    )
    if not record:
        return None
    return VariantConfig.model_validate(record)
