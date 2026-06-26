from app.business_book.model import BusinessBook


from datetime import datetime, timezone
from bson import ObjectId
from app.utility.model import PaginatedData, Pagination, ParamRequest
from ..utility.database import get_database
from .model import (
    BusinessBook,
    BusinessBookCreateRequest,
    BusinessBookUpdateRequest,
    BusinessBookWithBook,
)
import math

db = get_database()
collection = db["business_book"]


async def create_query(item: BusinessBookCreateRequest):
    data = item.model_dump()
    now = datetime.now(timezone.utc)
    data["updated_at"] = now
    data["created_at"] = now
    data["status"] = "ACTIVE"

    await collection.insert_one(data)


async def update_query(id: str, item: BusinessBookUpdateRequest):
    data = item.model_dump(exclude_unset=True)
    data.pop("business_id", None)  # Never allow changing ownership
    data["updated_at"] = datetime.utcnow()
    return await collection.update_one({"_id": ObjectId(id)}, {"$set": data})


async def delete_query(id: str):
    return await collection.update_one(
        {"_id": ObjectId(id)}, {"$set": {"status": "DELETED"}}
    )


async def read_query(params: ParamRequest) -> PaginatedData[BusinessBook]:
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

    return PaginatedData[BusinessBook](
        data=[BusinessBook.model_validate(record) for record in records],
        pagination=Pagination(
            page=page, size=size, total_pages=total_pages, total_results=total_results
        ),
    )


async def read_by_business_id_query(
    business_id: str, params: ParamRequest
) -> PaginatedData[BusinessBookWithBook]:
    """Read business_books for a given business with book title/image (seller catalog)."""
    page = max(1, params.page)
    size = params.size
    filt = {"business_id": ObjectId(business_id), "status": {"$ne": "DELETED"}}
    total_results = await collection.count_documents(filt)
    total_pages = math.ceil(total_results / size) if size else 1
    cursor = (
        collection.find(filt)
        .skip((page - 1) * size)
        .limit(size)
    )
    records = await cursor.to_list(length=size)
    book_collection = db["book"]
    for rec in records:
        book = await book_collection.find_one(
            {"_id": rec["book_id"], "status": {"$ne": "DELETED"}}
        )
        rec["book_title"] = book.get("title") if book else None
        rec["book_image"] = book.get("image") if book else None
    return PaginatedData[BusinessBookWithBook](
        data=[BusinessBookWithBook.model_validate(record) for record in records],
        pagination=Pagination(
            page=page, size=size, total_pages=total_pages, total_results=total_results
        ),
    )


async def read_by_id_query(id: str) -> BusinessBook | None:
    record = await collection.find_one(
        {"_id": ObjectId(id), "status": {"$ne": "DELETED"}}
    )
    if not record:
        return None
    return BusinessBook.model_validate(record)


