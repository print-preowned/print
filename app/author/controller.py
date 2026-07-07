from app.author.model import AuthorCreateRequest, AuthorUpdateRequest
from app.author.schemas import AuthorRead
from .service import (
    delete_service,
    read_service,
    read_by_id_service,
    create_service,
    update_service,
)
from ..utility.model import BaseResponse, PaginatedResponse, ParamRequest
from ..utility.authorization import (
    require_context,
    require_privilege,
    TokenPayload,
)
from fastapi import APIRouter, Response, Depends, HTTPException

router = APIRouter(prefix="/author", tags=["AuthorController"])

@router.post("/create", tags=["client"])
async def create(
    payload: AuthorCreateRequest,
    token: TokenPayload = Depends(require_privilege("CREATE_AUTHOR"))
) -> Response:
    """
    Create an author
    
    Following MDC-BE-AUTHOR-1: Requires BUSINESS context and CREATE_AUTHOR privilege
    Following MDC-AUTHOR-1: authors_are_global_entities
    """
    return await create_service(payload)


@router.put("/update/{id}", tags=["client"])
async def update(
    id: str,
    payload: AuthorUpdateRequest,
    token: TokenPayload = Depends(require_privilege("UPDATE_AUTHOR"))
) -> Response:
    """
    Update an author
    
    Following MDC-BE-AUTHOR-1: Requires BUSINESS context and UPDATE_AUTHOR privilege
    Following MDC-AUTHOR-1: authors_are_global_entities
    """
    return await update_service(id, payload)


# Following MDC-AUTHOR-2: authors_cannot_be_deleted
# No delete endpoint for authors


@router.get("/read", tags=["client"])
async def read(
    page: int = 1,
    size: int = 5,
    search: str | None = None,
    token: TokenPayload = Depends(require_privilege("READ_AUTHOR"))
) -> PaginatedResponse[AuthorRead]:
    """
    Read authors (paginated)
    
    Following MDC-BE-AUTHOR-1: Requires BUSINESS context and READ_AUTHOR privilege
    Note: Public read endpoint should be separate (READ_PUBLIC_AUTHOR for CUSTOMER context)
    """
    param = ParamRequest(page=page, size=size, search=search)
    return await read_service(param)


@router.get("/read/by-id/{id}", tags=["client"])
async def read_by_id(
    id: str,
    token: TokenPayload = Depends(require_privilege("READ_AUTHOR"))
) -> BaseResponse[AuthorRead]:
    """
    Read an author by ID
    
    Following MDC-BE-AUTHOR-1: Requires BUSINESS context and READ_AUTHOR privilege
    """
    return await read_by_id_service(id)


# Platform-only routes
@router.post("/merge", tags=["platform"])
async def merge_authors(
    source_author_id: str,
    target_author_id: str,
    token: TokenPayload = Depends(require_context("PLATFORM"))
) -> Response:
    """
    Merge two authors (platform only)
    
    Following MDC-AUTHOR platform_capabilities: merge_authors
    Requires PLATFORM context
    """
    # TODO: Implement merge logic
    # - Update all book_author.author_id references from source to target
    # - Mark source author as merged
    raise HTTPException(status_code=501, detail="Not implemented yet")


@router.post("/{id}/promote", tags=["platform"])
async def promote_to_canonical(
    id: str,
    token: TokenPayload = Depends(require_context("PLATFORM"))
) -> Response:
    """
    Promote an author to canonical status (platform only)
    
    Following MDC-AUTHOR platform_capabilities: promote_author_to_canonical
    Requires PLATFORM context
    """
    # TODO: Implement promotion logic
    raise HTTPException(status_code=501, detail="Not implemented yet")


@router.post("/{id}/deprecate", tags=["platform"])
async def deprecate_author(
    id: str,
    token: TokenPayload = Depends(require_context("PLATFORM"))
) -> Response:
    """
    Deprecate an author (platform only)
    
    Following MDC-AUTHOR platform_capabilities: deprecate_authors
    Requires PLATFORM context
    """
    # TODO: Implement deprecation logic
    raise HTTPException(status_code=501, detail="Not implemented yet")


@router.put("/{id}/correct-metadata", tags=["platform"])
async def correct_metadata(
    id: str,
    payload: AuthorUpdateRequest,
    token: TokenPayload = Depends(require_context("PLATFORM"))
) -> Response:
    """
    Correct author metadata (platform only)
    
    Following MDC-AUTHOR platform_capabilities: correct_author_metadata
    Requires PLATFORM context
    """
    return await update_service(id, payload)
