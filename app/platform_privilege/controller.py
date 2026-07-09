from fastapi import APIRouter, Depends, Response

from app.platform_privilege.model import (
    PlatformPrivilege,
    PlatformPrivilegeCreateRequest,
    PlatformPrivilegeUpdateRequest,
)
from app.platform_privilege.service import (
    ReadablePlatformPrivilegeService,
    WritablePlatformPrivilegeService,
)
from app.utility.authorization import TokenPayload, require_privilege
from app.utility.model import BaseResponse, PaginatedResponse, ParamRequest

router = APIRouter(prefix="/platform-privilege", tags=["platform-privilege"])


@router.post("", status_code=201, tags=["platform"])
async def create(
    platform_privilege: PlatformPrivilegeCreateRequest,
    token: TokenPayload = Depends(require_privilege("MANAGE_PLATFORM_PRIVILEGES")),
    service: WritablePlatformPrivilegeService = Depends(),
) -> Response:
    """
    Create a platform privilege
    Requires PLATFORM context and MANAGE_PLATFORM_PRIVILEGES privilege
    """
    return await service.create(platform_privilege)


@router.put("/{id}", status_code=200, tags=["platform"])
async def update(
    id: str,
    platform_privilege: PlatformPrivilegeUpdateRequest,
    token: TokenPayload = Depends(require_privilege("MANAGE_PLATFORM_PRIVILEGES")),
    service: WritablePlatformPrivilegeService = Depends(),
) -> Response:
    """
    Update a platform privilege
    Requires PLATFORM context and MANAGE_PLATFORM_PRIVILEGES privilege
    """
    return await service.update(id, platform_privilege)


@router.delete("/{id}", status_code=204, tags=["platform"])
async def delete(
    id: str,
    token: TokenPayload = Depends(require_privilege("MANAGE_PLATFORM_PRIVILEGES")),
    service: WritablePlatformPrivilegeService = Depends(),
) -> Response:
    """
    Delete a platform privilege
    Requires PLATFORM context and MANAGE_PLATFORM_PRIVILEGES privilege
    """
    return await service.delete(id)


@router.get("", status_code=200, tags=["platform"])
async def read(
    params: ParamRequest = Depends(),
    token: TokenPayload = Depends(require_privilege("MANAGE_PLATFORM_PRIVILEGES")),
    service: ReadablePlatformPrivilegeService = Depends(),
) -> PaginatedResponse[PlatformPrivilege]:
    """
    Read platform privileges (paginated)
    Requires PLATFORM context and MANAGE_PLATFORM_PRIVILEGES privilege
    """
    return await service.read(params)


@router.get("/{id}", status_code=200, tags=["platform"])
async def read_by_id(
    id: str,
    token: TokenPayload = Depends(require_privilege("MANAGE_PLATFORM_PRIVILEGES")),
    service: ReadablePlatformPrivilegeService = Depends(),
) -> BaseResponse[PlatformPrivilege]:
    """
    Read a platform privilege by ID
    Requires PLATFORM context and MANAGE_PLATFORM_PRIVILEGES privilege
    """
    return await service.read_by_id(id)


@router.get("/code/{code}", status_code=200, tags=["platform"])
async def read_by_code(
    code: str,
    token: TokenPayload = Depends(require_privilege("MANAGE_PLATFORM_PRIVILEGES")),
    service: ReadablePlatformPrivilegeService = Depends(),
) -> BaseResponse[PlatformPrivilege | None]:
    """
    Read a platform privilege by code
    Requires PLATFORM context and MANAGE_PLATFORM_PRIVILEGES privilege
    """
    return await service.read_by_code(code)
