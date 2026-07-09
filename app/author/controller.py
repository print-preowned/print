from fastapi import APIRouter, Depends, Response

from app.author.model import AuthorCreateRequest, AuthorUpdateRequest
from app.author.schemas import AuthorRead
from app.author.service import ReadableAuthorService, WritableAuthorService
from app.utility.authorization import TokenPayload, require_context, require_privilege
from app.utility.model import BaseResponse, PaginatedResponse, ParamRequest

router = APIRouter(prefix="/author", tags=["AuthorController"])


@router.post("/create", tags=["client"])
async def create(
    payload: AuthorCreateRequest,
    token: TokenPayload = Depends(require_privilege("CREATE_AUTHOR")),
    service: WritableAuthorService = Depends(),
) -> Response:
    """
    Create an author

    Following MDC-BE-AUTHOR-1: Requires BUSINESS context and CREATE_AUTHOR privilege
    Following MDC-AUTHOR-1: authors_are_global_entities
    """
    return await service.create(payload)


@router.put("/update/{id}", tags=["client"])
async def update(
    id: str,
    payload: AuthorUpdateRequest,
    token: TokenPayload = Depends(require_privilege("UPDATE_AUTHOR")),
    service: WritableAuthorService = Depends(),
) -> Response:
    """
    Update an author

    Following MDC-BE-AUTHOR-1: Requires BUSINESS context and UPDATE_AUTHOR privilege
    Following MDC-AUTHOR-1: authors_are_global_entities
    """
    return await service.update(id, payload)


# Following MDC-AUTHOR-2: authors_cannot_be_deleted
# No delete endpoint for authors


@router.get("/read", tags=["client"])
async def read(
    page: int = 1,
    size: int = 5,
    search: str | None = None,
    token: TokenPayload = Depends(require_privilege("READ_AUTHOR")),
    service: ReadableAuthorService = Depends(),
) -> PaginatedResponse[AuthorRead]:
    """
    Read authors (paginated)

    Following MDC-BE-AUTHOR-1: Requires BUSINESS context and READ_AUTHOR privilege
    Note: Public read endpoint should be separate (READ_PUBLIC_AUTHOR for CUSTOMER context)
    """
    param = ParamRequest(page=page, size=size, search=search)
    return await service.read(param)


@router.get("/read/by-id/{id}", tags=["client"])
async def read_by_id(
    id: str,
    token: TokenPayload = Depends(require_privilege("READ_AUTHOR")),
    service: ReadableAuthorService = Depends(),
) -> BaseResponse[AuthorRead]:
    """
    Read an author by ID

    Following MDC-BE-AUTHOR-1: Requires BUSINESS context and READ_AUTHOR privilege
    """
    return await service.read_by_id(id)


# Platform-only routes
@router.post("/merge", tags=["platform"])
async def merge_authors(
    source_author_id: str,
    target_author_id: str,
    token: TokenPayload = Depends(require_context("PLATFORM")),
    service: WritableAuthorService = Depends(),
) -> Response:
    """
    Merge two authors (platform only)

    Following MDC-AUTHOR platform_capabilities: merge_authors
    Requires PLATFORM context
    """
    return await service.merge(source_author_id, target_author_id)


@router.post("/{id}/promote", tags=["platform"])
async def promote_to_canonical(
    id: str,
    token: TokenPayload = Depends(require_context("PLATFORM")),
    service: WritableAuthorService = Depends(),
) -> Response:
    """
    Promote an author to canonical status (platform only)

    Following MDC-AUTHOR platform_capabilities: promote_author_to_canonical
    Requires PLATFORM context
    """
    return await service.promote(id)


@router.post("/{id}/deprecate", tags=["platform"])
async def deprecate_author(
    id: str,
    token: TokenPayload = Depends(require_context("PLATFORM")),
    service: WritableAuthorService = Depends(),
) -> Response:
    """
    Deprecate an author (platform only)

    Following MDC-AUTHOR platform_capabilities: deprecate_authors
    Requires PLATFORM context
    """
    return await service.deprecate(id)


@router.put("/{id}/correct-metadata", tags=["platform"])
async def correct_metadata(
    id: str,
    payload: AuthorUpdateRequest,
    token: TokenPayload = Depends(require_context("PLATFORM")),
    service: WritableAuthorService = Depends(),
) -> Response:
    """
    Correct author metadata (platform only)

    Following MDC-AUTHOR platform_capabilities: correct_author_metadata
    Requires PLATFORM context
    """
    return await service.update(id, payload)
