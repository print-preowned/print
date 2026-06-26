from app.book.model import (
    Book,
    BookCreateRequest,
    BookUpdateRequest,
    BookReadResponse,
    BookUploadUrlResponse,
)
from .service import (
    delete_service,
    read_service,
    read_by_id_service,
    create_service,
    read_upload_url as read_upload_url_service,
    update_service,
)
from ..utility.model import BaseResponse, PaginatedResponse, ParamRequest
from ..utility.authorization import (
    require_context,
    require_privilege,
    require_privilege_and_owner,
    TokenPayload,
)
from fastapi import APIRouter, Response, Depends, Request, HTTPException

router = APIRouter(prefix="/book", tags=["BookController"])

@router.post("/create", tags=["client"])
async def create(
    payload: BookCreateRequest,
    token: TokenPayload = Depends(require_privilege("CREATE_BOOK"))
) -> Response:
    """
    Create a book
    
    Following MDC-BE-BOOK-1: Requires BUSINESS context and CREATE_BOOK privilege
    """
    return await create_service(payload)


@router.put("/update/{id}", tags=["client"])
async def update(
    id: str,
    payload: BookUpdateRequest,
    token: TokenPayload = Depends(require_privilege("UPDATE_BOOK"))
) -> Response:
    """
    Update a book
    
    Following MDC-BE-BOOK-1: Requires BUSINESS context and UPDATE_BOOK privilege
    """
    return await update_service(id, payload)


@router.delete("/delete/{id}", tags=["client"])
async def delete(
    id: str,
    token: TokenPayload = Depends(require_privilege_and_owner("DELETE_BOOK"))
) -> Response:
    """
    Delete a book
    
    Following MDC-BE-BOOK-2: Requires BUSINESS context, DELETE_BOOK privilege, and owner status
    Following MDC-BOOK-2: deleting_book_requires_owner
    """
    return await delete_service(id)


@router.get("/read", tags=["client"])
async def read(
    page: int = 1,
    size: int = 5,
    search: str | None = None,
    token: TokenPayload = Depends(require_privilege("READ_BOOK"))
) -> PaginatedResponse[BookReadResponse]:
    """
    Read books (paginated)
    
    Following MDC-BE-BOOK-1: Requires BUSINESS context and READ_BOOK privilege
    """
    param = ParamRequest(page=page, size=size, search=search)
    return await read_service(param)


@router.get("/read/by-id/{id}", tags=["client"])
async def read_by_id(
    id: str,
    token: TokenPayload = Depends(require_privilege("READ_BOOK"))
) -> BaseResponse[BookReadResponse]:
    """
    Read a book by ID
    
    Following MDC-BE-BOOK-1: Requires BUSINESS context and READ_BOOK privilege
    """
    return await read_by_id_service(id)


@router.get("/read/upload-url", tags=["client", "platform"])
async def read_upload_url(
    file_type: str,
) -> BaseResponse[BookUploadUrlResponse]:
    return await read_upload_url_service(file_type)


# Platform-only routes
@router.post("/merge", tags=["platform"])
async def merge_books(
    source_book_id: str,
    target_book_id: str,
    token: TokenPayload = Depends(require_context("PLATFORM"))
) -> Response:
    """
    Merge two books (platform only)
    
    Following MDC-BOOK platform_capabilities: merge_books
    Requires PLATFORM context
    """
    # TODO: Implement merge logic
    # - Update all business_book.book_id references from source to target
    # - Mark source book as merged
    raise HTTPException(status_code=501, detail="Not implemented yet")


@router.post("/{id}/promote", tags=["platform"])
async def promote_to_canonical(
    id: str,
    token: TokenPayload = Depends(require_context("PLATFORM"))
) -> Response:
    """
    Promote a book to canonical status (platform only)
    
    Following MDC-BOOK platform_capabilities: promote_book_to_canonical
    Requires PLATFORM context
    """
    # TODO: Implement promotion logic
    raise HTTPException(status_code=501, detail="Not implemented yet")


@router.post("/{id}/deprecate", tags=["platform"])
async def deprecate_book(
    id: str,
    token: TokenPayload = Depends(require_context("PLATFORM"))
) -> Response:
    """
    Deprecate a book (platform on                               §        ly)
    
    Following MDC-BOOK platform_capabilities: deprecate_books
    Requires PLATFORM context
    """
    # TODO: Implement deprecation logic
    raise HTTPException(status_code=501, detail="Not implemented yet")


@router.put("/{id}/correct-metadata", tags=["platform"])
async def correct_metadata(
    id: str,
    payload: BookUpdateRequest,
    token: TokenPayload = Depends(require_context("PLATFORM"))
) -> Response:
    """
    Correct book metadata (platform only)
    
    Following MDC-BOOK platform_capabilities: correct_book_metadata
    Requires PLATFORM context
    """
    return await update_service(id, payload)
