"""Guardrails for the singleton super admin role."""

from fastapi import HTTPException

from app.platform_privilege_set.query import read_by_name_query
from app.platform_user.schemas import PlatformUserRead
from app.platform_user.query import read_active_by_privilege_set_id_query

SUPER_ADMIN_SET_NAME = "Super Admin"
ADMIN_SET_NAME = "Admin"


async def get_super_admin_privilege_set_id() -> str | None:
    privilege_set = await read_by_name_query(SUPER_ADMIN_SET_NAME)
    return str(privilege_set.id) if privilege_set else None


async def get_admin_privilege_set_id() -> str | None:
    privilege_set = await read_by_name_query(ADMIN_SET_NAME)
    return str(privilege_set.id) if privilege_set else None


async def is_super_admin_privilege_set(privilege_set_id: str) -> bool:
    super_admin_set_id = await get_super_admin_privilege_set_id()
    return super_admin_set_id is not None and str(privilege_set_id) == super_admin_set_id


async def read_active_super_admin() -> PlatformUserRead | None:
    super_admin_set_id = await get_super_admin_privilege_set_id()
    if not super_admin_set_id:
        return None
    return await read_active_by_privilege_set_id_query(super_admin_set_id)


async def ensure_super_admin_not_invitable(privilege_set_id: str) -> None:
    """Super Admin is bootstrap/transfer only — never via invite or platform user create."""
    if await is_super_admin_privilege_set(privilege_set_id):
        raise HTTPException(
            status_code=409,
            detail="Super Admin cannot be assigned via invite. Transfer the role from Account settings.",
        )


async def ensure_super_admin_not_removed(platform_user: PlatformUserRead) -> None:
    if await is_super_admin_privilege_set(str(platform_user.platform_privilege_set_id)):
        raise HTTPException(
            status_code=409,
            detail="Cannot remove the super admin",
        )


async def ensure_super_admin_not_assignable_via_update(privilege_set_id: str) -> None:
    if await is_super_admin_privilege_set(privilege_set_id):
        raise HTTPException(
            status_code=409,
            detail="Super Admin can only be transferred from Account settings by the current super admin",
        )


async def ensure_caller_is_super_admin(caller_user_id: str) -> PlatformUserRead:
    active_super_admin = await read_active_super_admin()
    if active_super_admin is None:
        raise HTTPException(status_code=409, detail="No super admin is configured")
    if str(active_super_admin.user_id) != caller_user_id:
        raise HTTPException(
            status_code=403,
            detail="Only the current super admin can transfer this role",
        )
    return active_super_admin


async def ensure_super_admin_not_demoted(
    existing: PlatformUserRead,
    new_privilege_set_id: str,
) -> None:
    if str(new_privilege_set_id) == str(existing.platform_privilege_set_id):
        return
    if await is_super_admin_privilege_set(str(existing.platform_privilege_set_id)):
        if not await is_super_admin_privilege_set(str(new_privilege_set_id)):
            raise HTTPException(
                status_code=409,
                detail="Cannot demote the super admin. Transfer the role from Account settings.",
            )
