from datetime import datetime, timezone
from bson import ObjectId
from app.utility.model import PaginatedData, Pagination, ParamRequest
from ..utility.database import get_database
from .model import BookAuthor, BookAuthorCreateRequest, BookAuthorUpdateRequest
import math

db = get_database()
collection = db["book_author"]


async def create_query(mapping: BookAuthorCreateRequest):
    data = mapping.model_dump()
    now = datetime.now(timezone.utc)
    data["updated_at"] = now
    data["created_at"] = now
    data["status"] = "ACTIVE"

    await collection.insert_one(data)


async def update_query(id: str, mapping: BookAuthorUpdateRequest):
    data = mapping.model_dump(exclude_unset=True)
    data["updated_at"] = datetime.utcnow()

    return await collection.update_one({"_id": ObjectId(id)}, {"$set": data})


async def delete_query(id: str):
    return await collection.update_one(
        {"_id": ObjectId(id)}, {"$set": {"status": "DELETED"}}
    )


async def delete_by_book_and_author_query(book_id: str, author_id: str):
    return await collection.update_one(
        {
            "book_id": ObjectId(book_id),
            "author_id": ObjectId(author_id),
            "status": {"$ne": "DELETED"},
        },
        {"$set": {"status": "DELETED", "updated_at": datetime.now(timezone.utc)}},
    )


async def read_query(params: ParamRequest) -> PaginatedData[BookAuthor]:
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
        data=[BookAuthor.model_validate(record) for record in records],
        pagination=Pagination(
            page=page, size=size, total_pages=total_pages, total_results=total_results
        ),
    )


async def read_by_id_query(id: str) -> BookAuthor | None:
    record = await collection.find_one(
        {"_id": ObjectId(id), "status": {"$ne": "DELETED"}}
    )
    if not record:
        return None
    return BookAuthor.model_validate(record)


async def read_by_book_id_query(book_id: str) -> list[BookAuthor]:
    cursor = collection.find(
        {"book_id": ObjectId(book_id), "status": {"$ne": "DELETED"}}
    )
    records = await cursor.to_list(length=None)
    return [BookAuthor.model_validate(record) for record in records]


async def read_by_book_ids_query(book_ids: list[str]) -> list[BookAuthor]:
    """Return all book-author links for any of the given book ids (for batch population)."""
    if not book_ids:
        return []
    oids = [ObjectId(bid) for bid in book_ids]
    cursor = collection.find(
        {"book_id": {"$in": oids}, "status": {"$ne": "DELETED"}}
    )
    records = await cursor.to_list(length=None)
    return [BookAuthor.model_validate(record) for record in records]


async def read_by_author_id_query(author_id: str) -> list[BookAuthor]:
    cursor = collection.find(
        {"author_id": ObjectId(author_id), "status": {"$ne": "DELETED"}}
    )
    records = await cursor.to_list(length=None)
    return [BookAuthor.model_validate(record) for record in records]


