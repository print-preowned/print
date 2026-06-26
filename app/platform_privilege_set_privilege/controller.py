from fastapi import APIRouter, Depends, Response
from app.platform_privilege_set_privilege.model import PlatformPrivilegeSetPrivilege, PlatformPrivilegeSetPrivilegeCreateRequest, PlatformPrivilegeSetPrivilegeUpdateRequest
from app.platform_privilege_set_privilege.service import (
    create_service,
    update_service,
    delete_service,
    read_service,
    read_by_id_service,
    read_by_privilege_set_id_service,
)
from app.utility.model import BaseResponse, PaginatedResponse, ParamRequest
from app.utility.authorization import TokenPayload, require_privilege

router = APIRouter(prefix="/platform-privilege-set-privilege", tags=["platform-privilege-set-privilege"])


@router.post("", status_code=201, tags=["platform"])
async def create(
    mapping: PlatformPrivilegeSetPrivilegeCreateRequest,
    token: TokenPayload = Depends(require_privilege("MANAGE_PLATFORM_PRIVILEGE_SETS"))
) -> Response:
    """
    Create a platform privilege set-privilege mapping
    Requires PLATFORM context and MANAGE_PLATFORM_PRIVILEGE_SETS privilege
    """
    return await create_service(mapping)


@router.put("/{id}", status_code=200, tags=["platform"])
async def update(
    id: str,
    mapping: PlatformPrivilegeSetPrivilegeUpdateRequest,
    token: TokenPayload = Depends(require_privilege("MANAGE_PLATFORM_PRIVILEGE_SETS"))
) -> Response:
    """
    Update a platform privilege set-privilege mapping
    Requires PLATFORM context and MANAGE_PLATFORM_PRIVILEGE_SETS privilege
    """
    return await update_service(id, mapping)


@router.delete("/{id}", status_code=204, tags=["platform"])
async def delete(
    id: str,
    token: TokenPayload = Depends(require_privilege("MANAGE_PLATFORM_PRIVILEGE_SETS"))
) -> Response:
    """
    Delete a platform privilege set-privilege mapping
    Requires PLATFORM context and MANAGE_PLATFORM_PRIVILEGE_SETS privilege
    """
    return await delete_service(id)


@router.get("", status_code=200, tags=["platform"])
async def read(
    params: ParamRequest = Depends(),
    token: TokenPayload = Depends(require_privilege("MANAGE_PLATFORM_PRIVILEGE_SETS"))
) -> PaginatedResponse[PlatformPrivilegeSetPrivilege]:
    """
    Read platform privilege set-privilege mappings (paginated)
    Requires PLATFORM context and MANAGE_PLATFORM_PRIVILEGE_SETS privilege
    """
    return await read_service(params)


@router.get("/{id}", status_code=200, tags=["platform"])
async def read_by_id(
    id: str,
    token: TokenPayload = Depends(require_privilege("MANAGE_PLATFORM_PRIVILEGE_SETS"))
) -> BaseResponse[PlatformPrivilegeSetPrivilege]:
    """
    Read a platform privilege set-privilege mapping by ID
    Requires PLATFORM context and MANAGE_PLATFORM_PRIVILEGE_SETS privilege
    """
    return await read_by_id_service(id)


@router.get("/privilege-set/{privilege_set_id}", status_code=200, tags=["platform"])
async def read_by_privilege_set_id(
    privilege_set_id: str,
    token: TokenPayload = Depends(require_privilege("MANAGE_PLATFORM_PRIVILEGE_SETS"))
) -> BaseResponse[list[PlatformPrivilegeSetPrivilege]]:
    """
    Read platform privilege set-privilege mappings by privilege set ID
    Requires PLATFORM context and MANAGE_PLATFORM_PRIVILEGE_SETS privilege
    """
    return await read_by_privilege_set_id_service(privilege_set_id)
