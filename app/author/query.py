from datetime import datetime, timezone
from bson import ObjectId
from app.utility.model import PaginatedData, Pagination, ParamRequest
from ..utility.database import get_database
from .model import Author, AuthorCreateRequest, AuthorUpdateRequest
import math

db = get_database()
collection = db["author"]


async def create_query(author: AuthorCreateRequest) -> ObjectId:
    data = author.model_dump()
    now = datetime.now(timezone.utc)
    data["updated_at"] = now
    data["created_at"] = now
    data["status"] = "ACTIVE"

    result = await collection.insert_one(data)
    return result.inserted_id


async def update_query(id: str, author: AuthorUpdateRequest):
    data = author.model_dump(exclude_unset=True)
    data["updated_at"] = datetime.utcnow()

    return await collection.update_one({"_id": ObjectId(id)}, {"$set": data})


async def delete_query(id: str):
    return await collection.update_one(
        {"_id": ObjectId(id)}, {"$set": {"status": "DELETED"}}
    )


async def read_query(params: ParamRequest) -> PaginatedData[Author]:
    page = max(1, params.page)
    size = params.size

    total_results = await collection.count_documents({"status": {"$ne": "DELETED"}})
    total_pages = math.ceil(total_results / size)
    cursor = (
        collection.find({"status": {"$ne": "DELETED"}})
        .skip((page - 1) * size)
        .limit(size)
    )
    records = await cursor.to_list(length=size)

    return PaginatedData(
        data=[Author.model_validate(record) for record in records],
        pagination=Pagination(
            page=page, size=size, total_pages=total_pages, total_results=total_results
        ),
    )


async def read_by_id_query(id: str) -> Author | None:
    record = await collection.find_one(
        {"_id": ObjectId(id), "status": {"$ne": "DELETED"}}
    )
    if not record:
        return None
    return Author.model_validate(record)


async def read_by_ids_query(ids: list[str]) -> list[Author]:
    """Return list of author docs for given ids (for batch population)."""
    if not ids:
        return []
    oids = [ObjectId(i) for i in ids]
    cursor = collection.find(
        {"_id": {"$in": oids}, "status": {"$ne": "DELETED"}}
    )
    records = await cursor.to_list(length=len(oids))
    return [Author.model_validate(record) for record in records]
