from fastapi import APIRouter, Depends, Response

from app.genre.schemas import GenreCreate, GenreRead, GenreUpdate
from app.genre.service import ReadableGenreService, WritableGenreService
from app.utility.model import BaseResponse, PaginatedResponse, ParamRequest

router = APIRouter(prefix="/genre", tags=["GenreController"])


@router.post("/create")
async def create(
    payload: GenreCreate,
    service: WritableGenreService = Depends(),
) -> Response:
    return await service.create(payload)


@router.put("/update/{id}")
async def update(
    id: str,
    payload: GenreUpdate,
    service: WritableGenreService = Depends(),
) -> Response:
    return await service.update(id, payload)


@router.delete("/delete/{id}")
async def delete(
    id: str,
    service: WritableGenreService = Depends(),
) -> Response:
    return await service.delete(id)


@router.get("/read")
async def read(
    page: int = 1,
    size: int = 5,
    search: str | None = None,
    service: ReadableGenreService = Depends(),
) -> PaginatedResponse[GenreRead]:
    param = ParamRequest(page=page, size=size, search=search)
    return await service.read(param)


@router.get("/read/by-id/{id}")
async def read_by_id(
    id: str,
    service: ReadableGenreService = Depends(),
) -> BaseResponse[GenreRead]:
    return await service.read_by_id(id)
