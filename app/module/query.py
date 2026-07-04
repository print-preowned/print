from datetime import datetime, timezone

from app.privilege.model import PrivilegeCreateRequest
from app.role_privilege.model import RolePrivilegeCreateRequest
from app.utility.model import PyObjectId
from ..privilege.query import create_query as privilege_create_query
from ..role_privilege.query import create_query as role_privilege_create_query


async def create_privilege_query(privilege: PrivilegeCreateRequest) -> None:
    """Insert a privilege row only (never write privilege fields into role_privilege)."""
    data = privilege.model_dump()
    now = datetime.now(timezone.utc)
    data["updated_at"] = now
    data["created_at"] = now
    data["status"] = "ACTIVE"

    from ..utility.database import get_database

    db = get_database()
    await db["privilege"].insert_one(data)


async def map_privilege_to_owner_role(
    owner_role_id: PyObjectId, privilege_code: str
) -> None:
    """Create an owner role_privilege mapping with the correct shape."""
    await role_privilege_create_query(
        RolePrivilegeCreateRequest(
            role_id=owner_role_id,
            privilege_code=privilege_code,
            status="ACTIVE",
        )
    )


async def create_privilege_and_map_to_owner(
    privilege: PrivilegeCreateRequest, owner_role_id: PyObjectId
) -> None:
    await privilege_create_query(privilege)
    await map_privilege_to_owner_role(owner_role_id, privilege.code)
