from fastapi import APIRouter, Depends, Response

from app.genre.schemas import GenreCreate, GenreRead, GenreUpdate
from app.genre.service import ReadableGenreService, WritableGenreService
from app.utility.authorization import TokenPayload, require_privilege
from app.utility.model import BaseResponse, PaginatedResponse
from app.utility.pagination import PaginationParams, pagination_params_with

router = APIRouter(prefix="/genres", tags=["genres"])


@router.post("", status_code=201)
async def create(
    payload: GenreCreate,
    token: TokenPayload = Depends(require_privilege("CREATE_GENRE")),
    service: WritableGenreService = Depends(),
) -> Response:
    return await service.create(payload)


@router.patch("/{id}")
async def update(
    id: str,
    payload: GenreUpdate,
    token: TokenPayload = Depends(require_privilege("UPDATE_GENRE")),
    service: WritableGenreService = Depends(),
) -> Response:
    return await service.update(id, payload)


@router.delete("/{id}")
async def delete(
    id: str,
    token: TokenPayload = Depends(require_privilege("DELETE_GENRE")),
    service: WritableGenreService = Depends(),
) -> Response:
    return await service.delete(id)


@router.get("")
async def read(
    params: PaginationParams = Depends(pagination_params_with(default_size=5)),
    token: TokenPayload = Depends(require_privilege("READ_GENRE")),
    service: ReadableGenreService = Depends(),
) -> PaginatedResponse[GenreRead]:
    return await service.read(params)


@router.get("/{id}")
async def read_by_id(
    id: str,
    token: TokenPayload = Depends(require_privilege("READ_GENRE")),
    service: ReadableGenreService = Depends(),
) -> BaseResponse[GenreRead]:
    return await service.read_by_id(id)
