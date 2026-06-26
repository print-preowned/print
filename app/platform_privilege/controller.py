from fastapi import APIRouter, Depends, Response
from app.platform_privilege.model import PlatformPrivilege, PlatformPrivilegeCreateRequest, PlatformPrivilegeUpdateRequest
from app.platform_privilege.service import (
    create_service,
    update_service,
    delete_service,
    read_service,
    read_by_id_service,
    read_by_code_service,
)
from app.utility.model import BaseResponse, PaginatedResponse, ParamRequest
from app.utility.authorization import TokenPayload, require_privilege

router = APIRouter(prefix="/platform-privilege", tags=["platform-privilege"])


@router.post("", status_code=201, tags=["platform"])
async def create(
    platform_privilege: PlatformPrivilegeCreateRequest,
    token: TokenPayload = Depends(require_privilege("MANAGE_PLATFORM_PRIVILEGES"))
) -> Response:
    """
    Create a platform privilege
    Requires PLATFORM context and MANAGE_PLATFORM_PRIVILEGES privilege
    """
    return await create_service(platform_privilege)


@router.put("/{id}", status_code=200, tags=["platform"])
async def update(
    id: str,
    platform_privilege: PlatformPrivilegeUpdateRequest,
    token: TokenPayload = Depends(require_privilege("MANAGE_PLATFORM_PRIVILEGES"))
) -> Response:
    """
    Update a platform privilege
    Requires PLATFORM context and MANAGE_PLATFORM_PRIVILEGES privilege
    """
    return await update_service(id, platform_privilege)


@router.delete("/{id}", status_code=204, tags=["platform"])
async def delete(
    id: str,
    token: TokenPayload = Depends(require_privilege("MANAGE_PLATFORM_PRIVILEGES"))
) -> Response:
    """
    Delete a platform privilege
    Requires PLATFORM context and MANAGE_PLATFORM_PRIVILEGES privilege
    """
    return await delete_service(id)


@router.get("", status_code=200, tags=["platform"])
async def read(
    params: ParamRequest = Depends(),
    token: TokenPayload = Depends(require_privilege("MANAGE_PLATFORM_PRIVILEGES"))
) -> PaginatedResponse[PlatformPrivilege]:
    """
    Read platform privileges (paginated)
    Requires PLATFORM context and MANAGE_PLATFORM_PRIVILEGES privilege
    """
    return await read_service(params)


@router.get("/{id}", status_code=200, tags=["platform"])
async def read_by_id(
    id: str,
    token: TokenPayload = Depends(require_privilege("MANAGE_PLATFORM_PRIVILEGES"))
) -> BaseResponse[PlatformPrivilege]:
    """
    Read a platform privilege by ID
    Requires PLATFORM context and MANAGE_PLATFORM_PRIVILEGES privilege
    """
    return await read_by_id_service(id)


@router.get("/code/{code}", status_code=200, tags=["platform"])
async def read_by_code(
    code: str,
    token: TokenPayload = Depends(require_privilege("MANAGE_PLATFORM_PRIVILEGES"))
) -> BaseResponse[PlatformPrivilege | None]:
    """
    Read a platform privilege by code
    Requires PLATFORM context and MANAGE_PLATFORM_PRIVILEGES privilege
    """
    return await read_by_code_service(code)
