from datetime import datetime, timezone
from bson import ObjectId
from app.utility.mongo_user_id import mongo_user_id_filter
from app.utility.model import PaginatedData, Pagination, ParamRequest
from app.utility.database import get_database
from .model import Business, BusinessCreateRequest, BusinessUpdateRequest
import math

db = get_database()
collection = db["business"]


async def create_query(business: BusinessCreateRequest):
    data = business.model_dump()
    now = datetime.now(timezone.utc)
    data["updated_at"] = now
    data["created_at"] = now
    if "status" not in data:
        data["status"] = "ACTIVE"

    await collection.insert_one(data)


async def update_query(id: str, business: BusinessUpdateRequest):
    data = business.model_dump(exclude_unset=True)
    data["updated_at"] = datetime.utcnow()

    return await collection.update_one({"_id": ObjectId(id)}, {"$set": data})


async def delete_query(id: str):
    return await collection.update_one(
        {"_id": ObjectId(id)}, {"$set": {"status": "DELETED"}}
    )


async def read_query(params: ParamRequest) -> PaginatedData[Business]:
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
    
    # Convert dict records to Business models
    businesses = [Business.model_validate(record) for record in records]

    return PaginatedData(
        data=businesses,
        pagination=Pagination(
            page=page, size=size, total_pages=total_pages, total_results=total_results
        ),
    )


async def read_by_id_query(id: str) -> Business | None:
    record = await collection.find_one(
        {"_id": ObjectId(id), "status": {"$ne": "DELETED"}}
    )
    if not record:
        return None
    return Business.model_validate(record)


async def read_by_user_id_query(user_id: str) -> Business | None:
    record = await collection.find_one(
        {**mongo_user_id_filter(user_id), "status": {"$ne": "DELETED"}}
    )
    if not record:
        return None
    return Business.model_validate(record)

