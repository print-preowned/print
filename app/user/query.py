from copyreg import constructor
from datetime import datetime, timezone
from bson import ObjectId
from app.utility.model import PaginatedData, Pagination, ParamRequest, PyObjectId
from ..utility.database import get_database
from .model import SignupRequest, User, UserCreateRequest, UserUpdateRequest
import math

db = get_database()
collection = db["user"]


async def signup_query(user: SignupRequest) -> str:
    data = user.model_dump()
    now = datetime.now(timezone.utc)
    data["updated_at"] = now
    data["created_at"] = now
    data["status"] = "ACTIVE"

    result = await collection.insert_one(data)
    return str(result.inserted_id)


async def create_query(user: UserCreateRequest):
    data = user.model_dump()
    now = datetime.now(timezone.utc)
    data["updated_at"] = now
    data["created_at"] = now
    data["status"] = "ACTIVE"

    await collection.insert_one(data)


async def update_query(id: str, user: UserUpdateRequest):
    data = user.model_dump(exclude_unset=True)
    data["updated_at"] = datetime.utcnow()

    return await collection.update_one({"_id": ObjectId(id)}, {"$set": data})


async def delete_query(id: str):
    return await collection.update_one(
        {"_id": ObjectId(id)}, {"$set": {"status": "DELETED"}}
    )


async def read_query(params: ParamRequest) -> PaginatedData[User]:
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
        data=[User.model_validate(record) for record in records],
        pagination=Pagination(
            page=page, size=size, total_pages=total_pages, total_results=total_results
        ),
    )


async def read_by_id_query(id: str) -> User | None:
    record = await collection.find_one(
        {"_id": ObjectId(id), "status": {"$ne": "DELETED"}}
    )
    return User.model_validate(record) if record else None


async def read_by_ids_query(ids: list[str]) -> list[User]:
    """Return list of user docs for given ids (for batch population)."""
    if not ids:
        return []
    oids = [ObjectId(i) for i in ids]
    cursor = collection.find(
        {"_id": {"$in": oids}, "status": {"$ne": "DELETED"}}
    )
    records = await cursor.to_list(length=len(oids))
    return [User.model_validate(record) for record in records]


async def read_by_role_id_query(role_id: str) -> list[User]:
    cursor = collection.find(
        {"role_id": ObjectId(role_id), "status": {"$ne": "DELETED"}}
    )
    records = await cursor.to_list(length=None)
    return [User.model_validate(record) for record in records]


async def read_by_email_query(email: str) -> User | None:
    user = await collection.find_one(
        {"email": email, "status": {"$ne": "DELETED"}}
    )
    
    if not user:
        return None

    # user["_id"] = str(user["_id"])  # convert ObjectId
    return User.model_validate(user)
