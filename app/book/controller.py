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
from app.utility.model import BaseResponse, PaginatedResponse, ParamRequest

router = APIRouter(prefix="/book", tags=["BookController"])


@router.post("/create", tags=["client"])
async def create(
    payload: BookCreateRequest,
    token: TokenPayload = Depends(require_privilege("CREATE_BOOK")),
    service: WritableBookService = Depends(),
) -> Response:
    """
    Create a book

    Following MDC-BE-BOOK-1: Requires BUSINESS context and CREATE_BOOK privilege
    """
    return await service.create(payload)


@router.put("/update/{id}", tags=["client"])
async def update(
    id: str,
    payload: BookUpdateRequest,
    token: TokenPayload = Depends(require_privilege("UPDATE_BOOK")),
    service: WritableBookService = Depends(),
) -> Response:
    """
    Update a book

    Following MDC-BE-BOOK-1: Requires BUSINESS context and UPDATE_BOOK privilege
    """
    return await service.update(id, payload)


@router.delete("/delete/{id}", tags=["client"])
async def delete(
    id: str,
    token: TokenPayload = Depends(require_privilege_and_owner("DELETE_BOOK")),
    service: WritableBookService = Depends(),
) -> Response:
    """
    Delete a book

    Following MDC-BE-BOOK-2: Requires BUSINESS context, DELETE_BOOK privilege, and owner status
    Following MDC-BOOK-2: deleting_book_requires_owner
    """
    return await service.delete(id)


@router.get("/read", tags=["client"])
async def read(
    page: int = 1,
    size: int = 5,
    search: str | None = None,
    token: TokenPayload = Depends(require_privilege("READ_BOOK")),
    service: ReadableBookService = Depends(),
) -> PaginatedResponse[BookReadResponse]:
    """
    Read books (paginated)

    Following MDC-BE-BOOK-1: Requires BUSINESS context and READ_BOOK privilege
    """
    param = ParamRequest(page=page, size=size, search=search)
    return await service.read(param)


@router.get("/read/by-id/{id}", tags=["client"])
async def read_by_id(
    id: str,
    token: TokenPayload = Depends(require_privilege("READ_BOOK")),
    service: ReadableBookService = Depends(),
) -> BaseResponse[BookReadResponse]:
    """
    Read a book by ID

    Following MDC-BE-BOOK-1: Requires BUSINESS context and READ_BOOK privilege
    """
    return await service.read_by_id(id)


@router.get("/read/upload-url", tags=["client", "platform"])
async def read_upload_url(
    file_type: str,
    service: ReadableBookService = Depends(),
) -> BaseResponse[BookUploadUrlResponse]:
    return await service.read_upload_url(file_type)


# Platform-only routes
@router.post("/merge", tags=["platform"])
async def merge_books(
    source_book_id: str,
    target_book_id: str,
    token: TokenPayload = Depends(require_context("PLATFORM")),
) -> Response:
    """
    Merge two books (platform only)

    Following MDC-BOOK platform_capabilities: merge_books
    Requires PLATFORM context
    """
    raise HTTPException(status_code=501, detail="Not implemented yet")


@router.post("/{id}/promote", tags=["platform"])
async def promote_to_canonical(
    id: str,
    token: TokenPayload = Depends(require_context("PLATFORM")),
) -> Response:
    """
    Promote a book to canonical status (platform only)

    Following MDC-BOOK platform_capabilities: promote_book_to_canonical
    Requires PLATFORM context
    """
    raise HTTPException(status_code=501, detail="Not implemented yet")


@router.post("/{id}/deprecate", tags=["platform"])
async def deprecate_book(
    id: str,
    token: TokenPayload = Depends(require_context("PLATFORM")),
) -> Response:
    """
    Deprecate a book (platform only)

    Following MDC-BOOK platform_capabilities: deprecate_books
    Requires PLATFORM context
    """
    raise HTTPException(status_code=501, detail="Not implemented yet")


@router.put("/{id}/correct-metadata", tags=["platform"])
async def correct_metadata(
    id: str,
    payload: BookUpdateRequest,
    token: TokenPayload = Depends(require_context("PLATFORM")),
    service: WritableBookService = Depends(),
) -> Response:
    """
    Correct book metadata (platform only)

    Following MDC-BOOK platform_capabilities: correct_book_metadata
    Requires PLATFORM context
    """
    return await service.update(id, payload)
