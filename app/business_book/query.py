from app.business_book.model import BusinessBook


from datetime import datetime, timezone
from bson import ObjectId
from app.utility.model import PaginatedData, Pagination, ParamRequest
from ..utility.database import get_database
from .model import (
    BusinessBook,
    BusinessBookCreateRequest,
    BusinessBookUpdateRequest,
    BusinessBookWithVariantSummary,
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
    from app.variant.query import delete_by_business_book_query

    await delete_by_business_book_query(id)
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
) -> PaginatedData[BusinessBookWithVariantSummary]:
    """Read business_books for a given business with book title/image and variant summary."""
    from app.variant.query import variant_summary_for_business_books

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
    bb_ids = [rec["_id"] for rec in records]
    summaries = await variant_summary_for_business_books(bb_ids)
    for rec in records:
        book = await book_collection.find_one(
            {"_id": rec["book_id"], "status": {"$ne": "DELETED"}}
        )
        rec["book_title"] = book.get("title") if book else None
        rec["book_image"] = book.get("image") if book else None
        summary = summaries.get(str(rec["_id"]), {})
        rec["variant_count"] = summary.get("variant_count", 0)
        rec["min_price"] = summary.get("min_price")
        rec["total_stock"] = summary.get("total_stock", 0)
    return PaginatedData[BusinessBookWithVariantSummary](
        data=[BusinessBookWithVariantSummary.model_validate(record) for record in records],
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


async def read_by_id_with_variants_query(id: str):
    from app.business_book.model import BusinessBookWithVariants
    from app.variant.query import read_by_business_book_id_query
    from app.utility.model import ParamRequest

    record = await collection.find_one(
        {"_id": ObjectId(id), "status": {"$ne": "DELETED"}}
    )
    if not record:
        return None
    book = await db["book"].find_one(
        {"_id": record["book_id"], "status": {"$ne": "DELETED"}}
    )
    record["book_title"] = book.get("title") if book else None
    record["book_image"] = book.get("image") if book else None
    listing = BusinessBookWithVariants.model_validate(record)
    variants_page = await read_by_business_book_id_query(
        id, ParamRequest(page=1, size=100)
    )
    listing.variants = variants_page.data
    return listing


