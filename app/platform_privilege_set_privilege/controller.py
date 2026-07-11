from fastapi import APIRouter, Depends, Response

from app.platform_privilege_set_privilege.model import (
    PlatformPrivilegeSetPrivilege,
    PlatformPrivilegeSetPrivilegeCreateRequest,
    PlatformPrivilegeSetPrivilegeUpdateRequest,
)
from app.platform_privilege_set_privilege.service import (
    ReadablePlatformPrivilegeSetPrivilegeService,
    WritablePlatformPrivilegeSetPrivilegeService,
)
from app.utility.authorization import TokenPayload, require_privilege
from app.utility.model import BaseResponse, PaginatedResponse, ParamRequest

router = APIRouter(
    prefix="/admin/privilege-set-privileges",
    tags=["admin-privilege-set-privileges"],
)


@router.post("", status_code=201, tags=["platform"])
async def create(
    mapping: PlatformPrivilegeSetPrivilegeCreateRequest,
    token: TokenPayload = Depends(require_privilege("MANAGE_PLATFORM_PRIVILEGE_SETS")),
    service: WritablePlatformPrivilegeSetPrivilegeService = Depends(),
) -> Response:
    """
    Create a platform privilege set-privilege mapping
    Requires PLATFORM context and MANAGE_PLATFORM_PRIVILEGE_SETS privilege
    """
    return await service.create(mapping)


@router.put("/{id}", status_code=200, tags=["platform"])
async def update(
    id: str,
    mapping: PlatformPrivilegeSetPrivilegeUpdateRequest,
    token: TokenPayload = Depends(require_privilege("MANAGE_PLATFORM_PRIVILEGE_SETS")),
    service: WritablePlatformPrivilegeSetPrivilegeService = Depends(),
) -> Response:
    """
    Update a platform privilege set-privilege mapping
    Requires PLATFORM context and MANAGE_PLATFORM_PRIVILEGE_SETS privilege
    """
    return await service.update(id, mapping)


@router.delete("/{id}", status_code=204, tags=["platform"])
async def delete(
    id: str,
    token: TokenPayload = Depends(require_privilege("MANAGE_PLATFORM_PRIVILEGE_SETS")),
    service: WritablePlatformPrivilegeSetPrivilegeService = Depends(),
) -> Response:
    """
    Delete a platform privilege set-privilege mapping
    Requires PLATFORM context and MANAGE_PLATFORM_PRIVILEGE_SETS privilege
    """
    return await service.delete(id)


@router.get("", status_code=200, tags=["platform"])
async def read(
    params: ParamRequest = Depends(),
    token: TokenPayload = Depends(require_privilege("MANAGE_PLATFORM_PRIVILEGE_SETS")),
    service: ReadablePlatformPrivilegeSetPrivilegeService = Depends(),
) -> PaginatedResponse[PlatformPrivilegeSetPrivilege]:
    """
    Read platform privilege set-privilege mappings (paginated)
    Requires PLATFORM context and MANAGE_PLATFORM_PRIVILEGE_SETS privilege
    """
    return await service.read(params)


@router.get("/{id}", status_code=200, tags=["platform"])
async def read_by_id(
    id: str,
    token: TokenPayload = Depends(require_privilege("MANAGE_PLATFORM_PRIVILEGE_SETS")),
    service: ReadablePlatformPrivilegeSetPrivilegeService = Depends(),
) -> BaseResponse[PlatformPrivilegeSetPrivilege]:
    """
    Read a platform privilege set-privilege mapping by ID
    Requires PLATFORM context and MANAGE_PLATFORM_PRIVILEGE_SETS privilege
    """
    return await service.read_by_id(id)


@router.get("/by-privilege-set/{privilege_set_id}", status_code=200, tags=["platform"])
async def read_by_privilege_set_id(
    privilege_set_id: str,
    token: TokenPayload = Depends(require_privilege("MANAGE_PLATFORM_PRIVILEGE_SETS")),
    service: ReadablePlatformPrivilegeSetPrivilegeService = Depends(),
) -> BaseResponse[list[PlatformPrivilegeSetPrivilege]]:
    """
    Read platform privilege set-privilege mappings by privilege set ID
    Requires PLATFORM context and MANAGE_PLATFORM_PRIVILEGE_SETS privilege
    """
    return await service.read_by_privilege_set_id(privilege_set_id)
