from fastapi import APIRouter, Depends, Response
from app.platform_privilege_set.model import PlatformPrivilegeSet, PlatformPrivilegeSetCreateRequest, PlatformPrivilegeSetUpdateRequest
from app.platform_privilege_set.service import (
    create_service,
    update_service,
    delete_service,
    read_service,
    read_by_id_service,
)
from app.utility.model import BaseResponse, PaginatedResponse, ParamRequest
from app.utility.authorization import TokenPayload, require_privilege

router = APIRouter(prefix="/platform-privilege-set", tags=["platform-privilege-set"])


@router.post("", status_code=201, tags=["platform"])
async def create(
    platform_privilege_set: PlatformPrivilegeSetCreateRequest,
    token: TokenPayload = Depends(require_privilege("MANAGE_PLATFORM_PRIVILEGE_SETS"))
) -> Response:
    """
    Create a platform privilege set
    Requires PLATFORM context and MANAGE_PLATFORM_PRIVILEGE_SETS privilege
    """
    return await create_service(platform_privilege_set)


@router.put("/{id}", status_code=200, tags=["platform"])
async def update(
    id: str,
    platform_privilege_set: PlatformPrivilegeSetUpdateRequest,
    token: TokenPayload = Depends(require_privilege("MANAGE_PLATFORM_PRIVILEGE_SETS"))
) -> Response:
    """
    Update a platform privilege set
    Requires PLATFORM context and MANAGE_PLATFORM_PRIVILEGE_SETS privilege
    """
    return await update_service(id, platform_privilege_set)


@router.delete("/{id}", status_code=204, tags=["platform"])
async def delete(
    id: str,
    token: TokenPayload = Depends(require_privilege("MANAGE_PLATFORM_PRIVILEGE_SETS"))
) -> Response:
    """
    Delete a platform privilege set
    Requires PLATFORM context and MANAGE_PLATFORM_PRIVILEGE_SETS privilege
    """
    return await delete_service(id)


@router.get("", status_code=200, tags=["platform"])
async def read(
    params: ParamRequest = Depends(),
    token: TokenPayload = Depends(require_privilege("MANAGE_PLATFORM_PRIVILEGE_SETS"))
) -> PaginatedResponse[PlatformPrivilegeSet]:
    """
    Read platform privilege sets (paginated)
    Requires PLATFORM context and MANAGE_PLATFORM_PRIVILEGE_SETS privilege
    """
    return await read_service(params)


@router.get("/{id}", status_code=200, tags=["platform"])
async def read_by_id(
    id: str,
    token: TokenPayload = Depends(require_privilege("MANAGE_PLATFORM_PRIVILEGE_SETS"))
) -> BaseResponse[PlatformPrivilegeSet]:
    """
    Read a platform privilege set by ID
    Requires PLATFORM context and MANAGE_PLATFORM_PRIVILEGE_SETS privilege
    """
    return await read_by_id_service(id)
