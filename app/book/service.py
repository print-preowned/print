from __future__ import annotations

import math
import uuid
from collections import defaultdict

from fastapi import HTTPException, Response
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.author.repository import AuthorRepository
from app.author.schemas import AuthorRead
from app.book.model import (
    AuthorRef,
    BookCreateRequest,
    BookReadResponse,
    BookUpdateRequest,
    BookUploadUrlResponse,
    GenreRef,
)
from app.book.repository import BookRepository
from app.book.schemas import BookCreate, BookRead, BookUpdate
from app.book_author.repository import BookAuthorRepository
from app.book_author.schemas import BookAuthorCreate
from app.book_genre.repository import BookGenreRepository
from app.book_genre.schemas import BookGenreCreate
from app.genre.repository import GenreRepository
from app.genre.schemas import GenreRead
from app.utility.aws.s3 import (
    create_object_url,
    create_presigned_upload_url,
    delete_object_if_exists,
    file_type_from_staging_key,
    object_key_from_url,
    resolve_persisted_book_image,
    staging_key_from_image,
    staging_object_key,
)
from app.utility.model import BaseResponse, PaginatedResponse, Pagination, ParamRequest
from app.utility.service_deps import readable_service, writable_service


def _validate_uuids(ids: list[str], field_name: str) -> None:
    for value in ids:
        try:
            uuid.UUID(value)
        except ValueError as exc:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid {field_name}: {value}",
            ) from exc


async def _sync_book_links(
    book_id: str,
    author_ids: list[str],
    genre_ids: list[str],
    book_author_repo: BookAuthorRepository,
    book_genre_repo: BookGenreRepository,
) -> None:
    parsed_book_id = uuid.UUID(book_id)
    existing_authors = await book_author_repo.read_by_book_id(parsed_book_id)
    existing_genres = await book_genre_repo.read_by_book_id(parsed_book_id)
    existing_author_ids = {str(link.author_id) for link in existing_authors}
    existing_genre_ids = {str(link.genre_id) for link in existing_genres}
    target_author_ids = set(author_ids)
    target_genre_ids = set(genre_ids)

    for author_id in target_author_ids - existing_author_ids:
        await book_author_repo.create_book_author(
            BookAuthorCreate(
                book_id=parsed_book_id,
                author_id=uuid.UUID(author_id),
            )
        )

    for author_id in existing_author_ids - target_author_ids:
        await book_author_repo.soft_delete_by_book_and_author(
            parsed_book_id,
            uuid.UUID(author_id),
        )

    for genre_id in target_genre_ids - existing_genre_ids:
        await book_genre_repo.create_book_genre(
            BookGenreCreate(
                book_id=parsed_book_id,
                genre_id=uuid.UUID(genre_id),
            )
        )

    for genre_id in existing_genre_ids - target_genre_ids:
        await book_genre_repo.soft_delete_by_book_and_genre(
            parsed_book_id,
            uuid.UUID(genre_id),
        )


async def _rollback_book_creation(
    book_repo: BookRepository,
    book_id: str,
    promoted_image_url: str | None = None,
) -> None:
    await book_repo.soft_delete_book(uuid.UUID(book_id))
    if promoted_image_url:
        key = object_key_from_url(promoted_image_url)
        if key:
            delete_object_if_exists(key)


def _author_ref(author: AuthorRead) -> AuthorRef:
    return AuthorRef(
        id=str(author.id),
        name=f"{author.first_name} {author.last_name}".strip() or "Unknown",
    )


def _genre_ref(genre: GenreRead) -> GenreRef:
    return GenreRef(id=str(genre.id), name=genre.name or "")


def _author_refs(authors: list[AuthorRead]) -> list[AuthorRef]:
    return [_author_ref(author) for author in authors]


def _genre_refs(genres: list[GenreRead]) -> list[GenreRef]:
    return [_genre_ref(genre) for genre in genres]


def _to_book_read_response(
    book: BookRead,
    author_refs: list[AuthorRef],
    genre_refs: list[GenreRef],
) -> BookReadResponse:
    return BookReadResponse.model_construct(
        **book.model_dump(),
        authors=author_refs,
        genres=genre_refs,
    )


class BookService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = BookRepository(session)
        self._author_repo = AuthorRepository(session)
        self._book_author_repo = BookAuthorRepository(session)
        self._book_genre_repo = BookGenreRepository(session)
        self._genre_repo = GenreRepository(session)

    async def create(self, book: BookCreateRequest) -> Response:
        staging_key = staging_key_from_image(book.image) if book.image else None
        create_payload = BookCreate.model_validate(
            book.model_dump(include=set(BookCreate.model_fields.keys()))
            | {"image": "" if staging_key else book.image}
        )
        created = await self._repo.create_book(create_payload)
        book_id = str(created.id)
        final_image: str | None = None

        try:
            if staging_key:
                final_image = resolve_persisted_book_image(book.image, book_id)
                update = await self._repo.update_book(
                    created.id,
                    BookUpdate(image=final_image),
                )
                if update is None:
                    raise HTTPException(status_code=500, detail="Failed to save book image")

            _validate_uuids(book.author_ids, "author_id")
            _validate_uuids(book.genre_ids, "genre_id")
            await _sync_book_links(
                book_id,
                book.author_ids,
                book.genre_ids,
                self._book_author_repo,
                self._book_genre_repo,
            )
        except HTTPException:
            await _rollback_book_creation(self._repo, book_id, final_image)
            raise
        except Exception as exc:
            await _rollback_book_creation(self._repo, book_id, final_image)
            raise HTTPException(status_code=500, detail="Failed to create book") from exc

        return JSONResponse(
            status_code=201,
            content={"id": book_id, "message": "Book created"},
        )

    async def update(self, id: str, book: BookUpdateRequest) -> Response:
        parsed_id = uuid.UUID(id)
        existing_row = await self._repo.read_book_by_id(parsed_id)
        if existing_row is None:
            raise HTTPException(status_code=404, detail="Book not found")
        existing = BookRead.model_validate(existing_row)

        update_payload = book.model_dump(exclude_unset=True, exclude={"author_ids", "genre_ids"})
        if book.image is not None:
            update_payload["image"] = resolve_persisted_book_image(
                book.image,
                id,
                old_image=existing.image,
            )

        if update_payload:
            update = await self._repo.update_book(parsed_id, BookUpdate(**update_payload))
            if update is None:
                raise HTTPException(status_code=404, detail="Book not found")

        if book.author_ids is not None or book.genre_ids is not None:
            author_links = await self._book_author_repo.read_by_book_id(parsed_id)
            genre_links = await self._book_genre_repo.read_by_book_id(parsed_id)
            next_author_ids = (
                book.author_ids
                if book.author_ids is not None
                else [str(link.author_id) for link in author_links]
            )
            next_genre_ids = (
                book.genre_ids
                if book.genre_ids is not None
                else [str(link.genre_id) for link in genre_links]
            )
            _validate_uuids(next_author_ids, "author_id")
            _validate_uuids(next_genre_ids, "genre_id")
            await _sync_book_links(
                id,
                next_author_ids,
                next_genre_ids,
                self._book_author_repo,
                self._book_genre_repo,
            )

        return Response(status_code=200)

    async def delete(self, id: str) -> Response:
        deleted = await self._repo.soft_delete_book(uuid.UUID(id))

        if not deleted:
            raise HTTPException(status_code=404, detail="Book not found")

        return Response(status_code=204)

    async def read(self, params: ParamRequest) -> PaginatedResponse[BookReadResponse]:
        page = max(1, params.page)
        size = params.size
        offset = (page - 1) * size

        total_results = await self._repo.count_books()
        rows = await self._repo.list_books(offset=offset, limit=size)
        books = [BookRead.model_validate(row) for row in rows]
        pagination = Pagination(
            page=page,
            size=size,
            total_pages=math.ceil(total_results / size) if size else 1,
            total_results=total_results,
        )
        if not books:
            return PaginatedResponse[BookReadResponse](
                status_code=200,
                message="Successful",
                data=[],
                pagination=pagination,
            )

        book_ids = [str(b.id) for b in books]
        author_links = await self._book_author_repo.read_by_book_ids(
            [uuid.UUID(book_id) for book_id in book_ids]
        )
        genre_links = await self._book_genre_repo.read_by_book_ids(
            [uuid.UUID(book_id) for book_id in book_ids]
        )

        author_ids_by_book: dict[str, list[str]] = defaultdict(list)
        for link in author_links:
            author_ids_by_book[str(link.book_id)].append(str(link.author_id))
        genre_ids_by_book: dict[str, list[str]] = defaultdict(list)
        for link in genre_links:
            genre_ids_by_book[str(link.book_id)].append(str(link.genre_id))

        all_author_ids = set[str]()
        for ids in author_ids_by_book.values():
            all_author_ids.update(ids)
        all_genre_ids = set[str]()
        for ids in genre_ids_by_book.values():
            all_genre_ids.update(ids)

        authors = [
            AuthorRead.model_validate(row)
            for row in await self._author_repo.read_authors_by_ids(
                [uuid.UUID(author_id) for author_id in all_author_ids]
            )
        ]
        genres = [
            GenreRead.model_validate(row)
            for row in await self._genre_repo.read_genres_by_ids(
                [uuid.UUID(genre_id) for genre_id in all_genre_ids]
            )
        ]
        author_map = {str(author.id): _author_ref(author) for author in authors}
        genre_map = {str(genre.id): _genre_ref(genre) for genre in genres}

        data: list[BookReadResponse] = []
        for book in books:
            bid = str(book.id)
            author_refs = [
                author_map[aid] for aid in author_ids_by_book.get(bid, []) if aid in author_map
            ]
            genre_refs = [
                genre_map[gid] for gid in genre_ids_by_book.get(bid, []) if gid in genre_map
            ]
            data.append(_to_book_read_response(book, author_refs, genre_refs))

        return PaginatedResponse[BookReadResponse](
            status_code=200,
            message="Successful",
            data=data,
            pagination=pagination,
        )

    async def read_by_id(self, id: str) -> BaseResponse[BookReadResponse]:
        parsed_id = uuid.UUID(id)
        row = await self._repo.read_book_by_id(parsed_id)

        if row is None:
            raise HTTPException(status_code=404, detail="Book not found")
        book = BookRead.model_validate(row)

        author_links = await self._book_author_repo.read_by_book_id(parsed_id)
        genre_links = await self._book_genre_repo.read_by_book_id(parsed_id)
        author_ids = [str(link.author_id) for link in author_links]
        genre_ids = [str(link.genre_id) for link in genre_links]

        authors = [
            AuthorRead.model_validate(row)
            for row in await self._author_repo.read_authors_by_ids(
                [uuid.UUID(author_id) for author_id in author_ids]
            )
        ]
        genres = [
            GenreRead.model_validate(row)
            for row in await self._genre_repo.read_genres_by_ids(
                [uuid.UUID(genre_id) for genre_id in genre_ids]
            )
        ]
        author_refs = _author_refs(authors)
        genre_refs = _genre_refs(genres)

        data = _to_book_read_response(book, author_refs, genre_refs)

        return BaseResponse[BookReadResponse](status_code=200, message="Successful", data=data)

    async def read_upload_url(self, file_type: str) -> BaseResponse[BookUploadUrlResponse]:
        object_key = staging_object_key(file_type)
        upload_url = create_presigned_upload_url(
            object_key,
            file_type_from_staging_key(object_key),
        )

        if upload_url is None:
            raise HTTPException(status_code=500, detail="Failed to create presigned URL")

        data = BookUploadUrlResponse(
            upload_url=upload_url,
            url=create_object_url(object_key),
        )
        return BaseResponse[BookUploadUrlResponse](status_code=200, message="Successful", data=data)


class WritableBookService(writable_service(BookService)):
    pass


class ReadableBookService(readable_service(BookService)):
    pass
