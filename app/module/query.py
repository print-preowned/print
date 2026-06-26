from datetime import datetime, timezone
from bson import ObjectId
from app.utility.model import PaginatedData, Pagination, ParamRequest
from ..utility.database import get_database
from ..privilege.model import Privilege, PrivilegeCreateRequest, PrivilegeUpdateRequest
import math

db = get_database()
privilege_collection = db["privilege"]
role_privilege_collection = db["role_privilege"]


async def create_query(privilege: PrivilegeCreateRequest):
    data = privilege.model_dump()
    now = datetime.now(timezone.utc)
    data["updated_at"] = now
    data["created_at"] = now
    data["status"] = "ACTIVE"

    await privilege_collection.insert_one(data)
    await role_privilege_collection.insert_one(data)


