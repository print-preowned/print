from fastapi import APIRouter, Depends, Response

from app.platform_privilege_set.model import (
    PlatformPrivilegeSet,
    PlatformPrivilegeSetCreateRequest,
    PlatformPrivilegeSetUpdateRequest,
)
from app.platform_privilege_set.service import (
    ReadablePlatformPrivilegeSetService,
    WritablePlatformPrivilegeSetService,
)
from app.utility.authorization import TokenPayload, require_privilege
from app.utility.model import BaseResponse, PaginatedResponse, ParamRequest

router = APIRouter(prefix="/platform-privilege-set", tags=["platform-privilege-set"])


@router.post("", status_code=201, tags=["platform"])
async def create(
    platform_privilege_set: PlatformPrivilegeSetCreateRequest,
    token: TokenPayload = Depends(require_privilege("MANAGE_PLATFORM_PRIVILEGE_SETS")),
    service: WritablePlatformPrivilegeSetService = Depends(),
) -> Response:
    """
    Create a platform privilege set
    Requires PLATFORM context and MANAGE_PLATFORM_PRIVILEGE_SETS privilege
    """
    return await service.create(platform_privilege_set)


@router.put("/{id}", status_code=200, tags=["platform"])
async def update(
    id: str,
    platform_privilege_set: PlatformPrivilegeSetUpdateRequest,
    token: TokenPayload = Depends(require_privilege("MANAGE_PLATFORM_PRIVILEGE_SETS")),
    service: WritablePlatformPrivilegeSetService = Depends(),
) -> Response:
    """
    Update a platform privilege set
    Requires PLATFORM context and MANAGE_PLATFORM_PRIVILEGE_SETS privilege
    """
    return await service.update(id, platform_privilege_set)


@router.delete("/{id}", status_code=204, tags=["platform"])
async def delete(
    id: str,
    token: TokenPayload = Depends(require_privilege("MANAGE_PLATFORM_PRIVILEGE_SETS")),
    service: WritablePlatformPrivilegeSetService = Depends(),
) -> Response:
    """
    Delete a platform privilege set
    Requires PLATFORM context and MANAGE_PLATFORM_PRIVILEGE_SETS privilege
    """
    return await service.delete(id)


@router.get("", status_code=200, tags=["platform"])
async def read(
    params: ParamRequest = Depends(),
    token: TokenPayload = Depends(require_privilege("MANAGE_PLATFORM_PRIVILEGE_SETS")),
    service: ReadablePlatformPrivilegeSetService = Depends(),
) -> PaginatedResponse[PlatformPrivilegeSet]:
    """
    Read platform privilege sets (paginated)
    Requires PLATFORM context and MANAGE_PLATFORM_PRIVILEGE_SETS privilege
    """
    return await service.read(params)


@router.get("/{id}", status_code=200, tags=["platform"])
async def read_by_id(
    id: str,
    token: TokenPayload = Depends(require_privilege("MANAGE_PLATFORM_PRIVILEGE_SETS")),
    service: ReadablePlatformPrivilegeSetService = Depends(),
) -> BaseResponse[PlatformPrivilegeSet]:
    """
    Read a platform privilege set by ID
    Requires PLATFORM context and MANAGE_PLATFORM_PRIVILEGE_SETS privilege
    """
    return await service.read_by_id(id)
