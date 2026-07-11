from fastapi import APIRouter, Depends, Response

from app.author.model import AuthorCreateRequest, AuthorUpdateRequest
from app.author.schemas import AuthorRead
from app.author.service import ReadableAuthorService, WritableAuthorService
from app.utility.authorization import TokenPayload, require_context, require_privilege
from app.utility.model import BaseResponse, PaginatedResponse, ParamRequest

router = APIRouter(prefix="/authors", tags=["authors"])


@router.post("", status_code=201, tags=["client"])
async def create(
    payload: AuthorCreateRequest,
    token: TokenPayload = Depends(require_privilege("CREATE_AUTHOR")),
    service: WritableAuthorService = Depends(),
) -> Response:
    return await service.create(payload)


@router.patch("/{id}", tags=["client"])
async def update(
    id: str,
    payload: AuthorUpdateRequest,
    token: TokenPayload = Depends(require_privilege("UPDATE_AUTHOR")),
    service: WritableAuthorService = Depends(),
) -> Response:
    return await service.update(id, payload)


@router.get("", tags=["client"])
async def read(
    page: int = 1,
    size: int = 5,
    search: str | None = None,
    service: ReadableAuthorService = Depends(),
) -> PaginatedResponse[AuthorRead]:
    param = ParamRequest(page=page, size=size, search=search)
    return await service.read(param)


@router.get("/{id}", tags=["client"])
async def read_by_id(
    id: str,
    service: ReadableAuthorService = Depends(),
) -> BaseResponse[AuthorRead]:
    return await service.read_by_id(id)


@router.post("/merge", tags=["platform"])
async def merge_authors(
    source_author_id: str,
    target_author_id: str,
    token: TokenPayload = Depends(require_context("PLATFORM")),
    service: WritableAuthorService = Depends(),
) -> Response:
    return await service.merge(source_author_id, target_author_id)


@router.post("/{id}/promote", tags=["platform"])
async def promote_to_canonical(
    id: str,
    token: TokenPayload = Depends(require_context("PLATFORM")),
    service: WritableAuthorService = Depends(),
) -> Response:
    return await service.promote(id)


@router.post("/{id}/deprecate", tags=["platform"])
async def deprecate_author(
    id: str,
    token: TokenPayload = Depends(require_context("PLATFORM")),
    service: WritableAuthorService = Depends(),
) -> Response:
    return await service.deprecate(id)
