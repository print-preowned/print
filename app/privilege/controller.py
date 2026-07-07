from app.privilege.model import PrivilegeCreateRequest, PrivilegeUpdateRequest
from app.privilege.schemas import PrivilegeRead
from .service import (
    delete_service,
    read_service,
    read_by_id_service,
    create_service,
    update_service,
)
from ..utility.model import BaseResponse, PaginatedResponse, ParamRequest
from fastapi import APIRouter, Response

router = APIRouter(prefix="/privilege", tags=["PrivilegeController"])


@router.post("/create")
async def create(payload: PrivilegeCreateRequest) -> Response:
    return await create_service(payload)


@router.put("/update/{id}")
async def update(id: str, payload: PrivilegeUpdateRequest) -> Response:
    return await update_service(id, payload)


@router.delete("/delete/{id}")
async def delete(id) -> Response:
    return await delete_service(id)


@router.get("/read")
async def read(
    page: int = 1, size: int = 5, search: str | None = None
) -> PaginatedResponse[PrivilegeRead]:
    param = ParamRequest(page=page, size=size, search=search)
    return await read_service(param)


@router.get("/read/by-id/{id}")
async def read_by_id(id: str) -> BaseResponse[PrivilegeRead]:
    return await read_by_id_service(id)


