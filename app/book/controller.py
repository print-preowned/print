from fastapi import APIRouter, Depends, HTTPException, Response

from app.book.model import (
    BookCreateRequest,
    BookReadResponse,
    BookUpdateRequest,
    BookUploadUrlResponse,
)
from app.book.service import ReadableBookService, WritableBookService
from app.utility.authorization import (
    TokenPayload,
    require_context,
    require_privilege,
    require_privilege_and_owner,
)
from app.utility.model import BaseResponse, PaginatedResponse
from app.utility.pagination import PaginationParams, pagination_params_with

router = APIRouter(prefix="/books", tags=["books"])


@router.post("", status_code=201, tags=["client"])
async def create(
    payload: BookCreateRequest,
    token: TokenPayload = Depends(require_privilege("CREATE_BOOK")),
    service: WritableBookService = Depends(),
) -> Response:
    return await service.create(payload)


@router.patch("/{id}", tags=["client"])
async def update(
    id: str,
    payload: BookUpdateRequest,
    token: TokenPayload = Depends(require_privilege("UPDATE_BOOK")),
    service: WritableBookService = Depends(),
) -> Response:
    return await service.update(id, payload)


@router.delete("/{id}", tags=["client"])
async def delete(
    id: str,
    token: TokenPayload = Depends(require_privilege_and_owner("DELETE_BOOK")),
    service: WritableBookService = Depends(),
) -> Response:
    return await service.delete(id)


@router.get("/upload-url", tags=["client", "platform"])
async def read_upload_url(
    file_type: str,
    token: TokenPayload = Depends(require_privilege("CREATE_BOOK")),
    service: ReadableBookService = Depends(),
) -> BaseResponse[BookUploadUrlResponse]:
    return await service.read_upload_url(file_type)


@router.get("", tags=["client"])
async def read(
    params: PaginationParams = Depends(pagination_params_with(default_size=5)),
    service: ReadableBookService = Depends(),
) -> PaginatedResponse[BookReadResponse]:
    return await service.read(params)


@router.get("/{id}", tags=["client"])
async def read_by_id(
    id: str,
    service: ReadableBookService = Depends(),
) -> BaseResponse[BookReadResponse]:
    return await service.read_by_id(id)


@router.post("/merge", tags=["platform"])
async def merge_books(
    source_book_id: str,
    target_book_id: str,
    token: TokenPayload = Depends(require_context("PLATFORM")),
) -> Response:
    raise HTTPException(status_code=501, detail="Not implemented yet")


@router.post("/{id}/promote", tags=["platform"])
async def promote_to_canonical(
    id: str,
    token: TokenPayload = Depends(require_context("PLATFORM")),
) -> Response:
    raise HTTPException(status_code=501, detail="Not implemented yet")


@router.post("/{id}/deprecate", tags=["platform"])
async def deprecate_book(
    id: str,
    token: TokenPayload = Depends(require_context("PLATFORM")),
) -> Response:
    raise HTTPException(status_code=501, detail="Not implemented yet")
