from datetime import datetime, timezone
from bson import ObjectId
from fastapi import HTTPException
from app.utility.model import PaginatedData, Pagination, ParamRequest, PyObjectId
from ..utility.database import get_database
from .model import (
    Variant,
    VariantCreateRequest,
    VariantUpdateRequest,
    VariantWithConfig,
    PublicCatalogVariant,
    ResolvedConfig,
)
import math

db = get_database()
collection = db["variant"]
config_collection = db["variant_config"]
variant_option_collection = db["variant_option"]
variant_type_collection = db["variant_type"]
business_book_collection = db["business_book"]
book_collection = db["book"]
business_collection = db["business"]


async def update_query(id: str, item: VariantUpdateRequest):
    data = item.model_dump(exclude_unset=True)
    data["updated_at"] = datetime.now(timezone.utc)

    return await collection.update_one({"_id": ObjectId(id)}, {"$set": data})


async def delete_query(id: str):
    now = datetime.now(timezone.utc)
    result = await collection.update_one(
        {"_id": ObjectId(id)}, {"$set": {"status": "DELETED", "updated_at": now}}
    )
    if result.matched_count:
        await config_collection.update_many(
            {"variant_id": ObjectId(id), "status": {"$ne": "DELETED"}},
            {"$set": {"status": "DELETED", "updated_at": now}},
        )
    return result


async def delete_by_business_book_query(business_book_id: str):
    now = datetime.now(timezone.utc)
    variants = await collection.find(
        {"business_book_id": ObjectId(business_book_id), "status": {"$ne": "DELETED"}}
    ).to_list(length=None)
    if not variants:
        return
    variant_ids = [v["_id"] for v in variants]
    await collection.update_many(
        {"_id": {"$in": variant_ids}},
        {"$set": {"status": "DELETED", "updated_at": now}},
    )
    await config_collection.update_many(
        {"variant_id": {"$in": variant_ids}, "status": {"$ne": "DELETED"}},
        {"$set": {"status": "DELETED", "updated_at": now}},
    )


async def read_query(params: ParamRequest) -> PaginatedData[Variant]:
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
        data=[Variant.model_validate(record) for record in records],
        pagination=Pagination(
            page=page, size=size, total_pages=total_pages, total_results=total_results
        ),
    )


async def read_by_id_query(id: str) -> Variant | None:
    record = await collection.find_one(
        {"_id": ObjectId(id), "status": {"$ne": "DELETED"}}
    )
    if not record:
        return None
    return Variant.model_validate(record)


async def read_by_business_book_id_query(
    business_book_id: str, params: ParamRequest
) -> PaginatedData[VariantWithConfig]:
    page = max(1, params.page)
    size = params.size
    filt = {
        "business_book_id": ObjectId(business_book_id),
        "status": {"$ne": "DELETED"},
    }
    total_results = await collection.count_documents(filt)
    total_pages = math.ceil(total_results / size) if size else 1
    cursor = collection.find(filt).skip((page - 1) * size).limit(size)
    records = await cursor.to_list(length=size)
    config_map = await _configs_for_variants([r["_id"] for r in records])
    data = []
    for record in records:
        variant = VariantWithConfig.model_validate(record)
        variant.config = config_map.get(str(record["_id"]), [])
        data.append(variant)
    return PaginatedData(
        data=data,
        pagination=Pagination(
            page=page, size=size, total_pages=total_pages, total_results=total_results
        ),
    )


async def read_by_id_with_config_query(id: str) -> VariantWithConfig | None:
    record = await collection.find_one(
        {"_id": ObjectId(id), "status": {"$ne": "DELETED"}}
    )
    if not record:
        return None
    variant = VariantWithConfig.model_validate(record)
    config_map = await _configs_for_variants([record["_id"]])
    variant.config = config_map.get(str(record["_id"]), [])
    return variant


async def variant_summary_for_business_books(
    business_book_ids: list[ObjectId],
) -> dict[str, dict]:
    if not business_book_ids:
        return {}
    pipeline = [
        {
            "$match": {
                "business_book_id": {"$in": business_book_ids},
                "status": {"$ne": "DELETED"},
            }
        },
        {
            "$group": {
                "_id": "$business_book_id",
                "variant_count": {"$sum": 1},
                "min_price": {"$min": "$price"},
                "total_stock": {"$sum": "$stock"},
            }
        },
    ]
    summaries: dict[str, dict] = {}
    async for row in collection.aggregate(pipeline):
        summaries[str(row["_id"])] = {
            "variant_count": row["variant_count"],
            "min_price": row["min_price"],
            "total_stock": row["total_stock"],
        }
    return summaries


async def _configs_for_variants(
    variant_ids: list[ObjectId],
) -> dict[str, list[ResolvedConfig]]:
    if not variant_ids:
        return {}
    rows = await config_collection.find(
        {"variant_id": {"$in": variant_ids}, "status": {"$ne": "DELETED"}}
    ).to_list(length=None)
    if not rows:
        return {}

    option_ids = list({r["variant_option_id"] for r in rows})
    options = await variant_option_collection.find(
        {"_id": {"$in": option_ids}, "status": {"$ne": "DELETED"}}
    ).to_list(length=None)
    option_by_id = {o["_id"]: o for o in options}

    type_ids = list({o["variant_type_id"] for o in options})
    types = await variant_type_collection.find(
        {"_id": {"$in": type_ids}, "status": {"$ne": "DELETED"}}
    ).to_list(length=None)
    type_by_id = {t["_id"]: t for t in types}

    result: dict[str, list[ResolvedConfig]] = {}
    for row in rows:
        variant_id = str(row["variant_id"])
        option = option_by_id.get(row["variant_option_id"])
        if not option:
            continue
        vtype = type_by_id.get(option["variant_type_id"])
        if not vtype:
            continue
        result.setdefault(variant_id, []).append(
            ResolvedConfig(
                variant_type_id=str(vtype["_id"]),
                variant_type_name=vtype["name"],
                variant_option_id=str(option["_id"]),
                variant_option_value=option["value"],
            )
        )
    for variant_id in result:
        result[variant_id].sort(key=lambda c: c.variant_type_name)
    return result


async def _validate_variant_options(option_ids: list[PyObjectId]) -> None:
    if not option_ids:
        raise HTTPException(
            status_code=400, detail="At least one variant option is required"
        )
    options = await variant_option_collection.find(
        {"_id": {"$in": option_ids}, "status": {"$ne": "DELETED"}}
    ).to_list(length=len(option_ids))
    if len(options) != len(option_ids):
        raise HTTPException(status_code=400, detail="Invalid variant option")

    type_ids = [o["variant_type_id"] for o in options]
    if len(type_ids) != len(set(type_ids)):
        raise HTTPException(
            status_code=400,
            detail="Only one option per variant type is allowed",
        )


async def _duplicate_config_set_exists(
    business_book_id: PyObjectId, option_ids: list[PyObjectId]
) -> bool:
    existing = await collection.find(
        {"business_book_id": business_book_id, "status": {"$ne": "DELETED"}}
    ).to_list(length=None)
    if not existing:
        return False
    target = frozenset(str(oid) for oid in option_ids)
    config_map = await _configs_for_variants([v["_id"] for v in existing])
    for variant in existing:
        existing_options = frozenset(
            c.variant_option_id for c in config_map.get(str(variant["_id"]), [])
        )
        if existing_options == target:
            return True
    return False


async def create_query(
    business_book_id: str, payload: VariantCreateRequest
) -> str:
    bb_oid = PyObjectId(business_book_id)
    option_ids = list(payload.variant_option_ids)
    await _validate_variant_options(option_ids)
    if await _duplicate_config_set_exists(bb_oid, option_ids):
        raise HTTPException(
            status_code=409,
            detail="A variant with this option combination already exists",
        )

    now = datetime.now(timezone.utc)
    variant_data = payload.model_dump(exclude={"variant_option_ids"})
    variant_data["business_book_id"] = bb_oid
    variant_data["created_at"] = now
    variant_data["updated_at"] = now
    if not variant_data.get("status"):
        variant_data["status"] = "ACTIVE"

    result = await collection.insert_one(variant_data)
    variant_id = result.inserted_id
    for option_id in option_ids:
        await config_collection.insert_one(
            {
                "variant_option_id": option_id,
                "variant_id": variant_id,
                "status": "ACTIVE",
                "created_at": now,
                "updated_at": now,
            }
        )
    return str(variant_id)


async def read_public_catalog_query(
    params: ParamRequest,
) -> PaginatedData[PublicCatalogVariant]:
    page = max(1, params.page)
    size = params.size
    filt = {"status": "ACTIVE", "stock": {"$gt": 0}}
    total_results = await collection.count_documents(filt)
    total_pages = math.ceil(total_results / size) if size else 1
    cursor = collection.find(filt).skip((page - 1) * size).limit(size)
    records = await cursor.to_list(length=size)

    bb_ids = list({r["business_book_id"] for r in records})
    business_books = (
        await business_book_collection.find(
            {"_id": {"$in": bb_ids}, "status": "ACTIVE"}
        ).to_list(length=len(bb_ids))
        if bb_ids
        else []
    )
    bb_by_id = {bb["_id"]: bb for bb in business_books}

    book_ids = list({bb["book_id"] for bb in business_books})
    books = (
        await book_collection.find(
            {"_id": {"$in": book_ids}, "status": {"$ne": "DELETED"}}
        ).to_list(length=len(book_ids))
        if book_ids
        else []
    )
    book_by_id = {b["_id"]: b for b in books}

    business_ids = list({bb["business_id"] for bb in business_books})
    businesses = (
        await business_collection.find(
            {"_id": {"$in": business_ids}, "status": {"$ne": "DELETED"}}
        ).to_list(length=len(business_ids))
        if business_ids
        else []
    )
    business_by_id = {b["_id"]: b for b in businesses}

    config_map = await _configs_for_variants([r["_id"] for r in records])
    data: list[PublicCatalogVariant] = []
    for record in records:
        bb = bb_by_id.get(record["business_book_id"])
        if not bb:
            continue
        book = book_by_id.get(bb["book_id"])
        business = business_by_id.get(bb["business_id"])
        if not book or not business:
            continue
        effective_price = record["price"]
        if record.get("discount"):
            effective_price = record["price"] * (1 - record["discount"] / 100)
        data.append(
            PublicCatalogVariant(
                id=str(record["_id"]),
                business_book_id=str(bb["_id"]),
                book_id=str(book["_id"]),
                book_title=book.get("title", ""),
                book_image=record.get("image") or bb.get("image") or book.get("image"),
                business_id=str(business["_id"]),
                business_name=business.get("name", ""),
                price=effective_price,
                currency=record["currency"],
                discount=record.get("discount"),
                stock=record["stock"],
                image=record.get("image"),
                config=config_map.get(str(record["_id"]), []),
            )
        )

    return PaginatedData(
        data=data,
        pagination=Pagination(
            page=page, size=size, total_pages=total_pages, total_results=total_results
        ),
    )


async def read_public_catalog_by_id_query(id: str) -> PublicCatalogVariant | None:
    record = await collection.find_one(
        {"_id": ObjectId(id), "status": "ACTIVE", "stock": {"$gt": 0}}
    )
    if not record:
        return None
    bb = await business_book_collection.find_one(
        {"_id": record["business_book_id"], "status": "ACTIVE"}
    )
    if not bb:
        return None
    book = await book_collection.find_one(
        {"_id": bb["book_id"], "status": {"$ne": "DELETED"}}
    )
    business = await business_collection.find_one(
        {"_id": bb["business_id"], "status": {"$ne": "DELETED"}}
    )
    if not book or not business:
        return None
    config_map = await _configs_for_variants([record["_id"]])
    effective_price = record["price"]
    if record.get("discount"):
        effective_price = record["price"] * (1 - record["discount"] / 100)
    return PublicCatalogVariant(
        id=str(record["_id"]),
        business_book_id=str(bb["_id"]),
        book_id=str(book["_id"]),
        book_title=book.get("title", ""),
        book_image=record.get("image") or bb.get("image") or book.get("image"),
        business_id=str(business["_id"]),
        business_name=business.get("name", ""),
        price=effective_price,
        currency=record["currency"],
        discount=record.get("discount"),
        stock=record["stock"],
        image=record.get("image"),
        config=config_map.get(str(record["_id"]), []),
    )
