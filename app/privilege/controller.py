from fastapi import APIRouter, Depends, Response

from app.privilege.model import PrivilegeCreateRequest, PrivilegeUpdateRequest
from app.privilege.schemas import PrivilegeRead
from app.privilege.service import ReadablePrivilegeService, WritablePrivilegeService
from app.utility.model import BaseResponse, PaginatedResponse, ParamRequest

router = APIRouter(prefix="/privilege", tags=["PrivilegeController"])


@router.post("/create")
async def create(
    payload: PrivilegeCreateRequest,
    service: WritablePrivilegeService = Depends(),
) -> Response:
    return await service.create(payload)


@router.put("/update/{id}")
async def update(
    id: str,
    payload: PrivilegeUpdateRequest,
    service: WritablePrivilegeService = Depends(),
) -> Response:
    return await service.update(id, payload)


@router.delete("/delete/{id}")
async def delete(
    id: str,
    service: WritablePrivilegeService = Depends(),
) -> Response:
    return await service.delete(id)


@router.get("/read")
async def read(
    page: int = 1,
    size: int = 5,
    search: str | None = None,
    service: ReadablePrivilegeService = Depends(),
) -> PaginatedResponse[PrivilegeRead]:
    param = ParamRequest(page=page, size=size, search=search)
    return await service.read(param)


@router.get("/read/by-id/{id}")
async def read_by_id(
    id: str,
    service: ReadablePrivilegeService = Depends(),
) -> BaseResponse[PrivilegeRead]:
    return await service.read_by_id(id)
