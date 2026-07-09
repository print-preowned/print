from __future__ import annotations

from collections import defaultdict
import uuid

from fastapi import HTTPException, Response
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.author.query import read_by_ids_query as read_authors_by_ids
from app.author.schemas import AuthorRead
from app.book.model import (
    AuthorRef,
    BookCreateRequest,
    BookReadResponse,
    BookUpdateRequest,
    BookUploadUrlResponse,
    GenreRef,
)
from app.book.schemas import BookRead
from app.book_author.model import BookAuthorCreateRequest
from app.book_author.query import (
    create_query as create_book_author_query,
    delete_by_book_and_author_query,
    read_by_book_id_query as read_book_authors,
    read_by_book_ids_query as read_book_authors_batch,
)
from app.book_genre.model import BookGenreCreateRequest
from app.book_genre.query import (
    create_query as create_book_genre_query,
    delete_by_book_and_genre_query,
    read_by_book_id_query as read_book_genres,
    read_by_book_ids_query as read_book_genres_batch,
)
from app.genre.query import read_by_ids_query as read_genres_by_ids
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
from app.utility.model import BaseResponse, PaginatedResponse, ParamRequest
from app.utility.service_deps import readable_service, writable_service

from .query import (
    create_query,
    delete_query,
    read_by_id_query,
    read_query,
    update_query,
)


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
) -> None:
    existing_authors = await read_book_authors(book_id)
    existing_genres = await read_book_genres(book_id)
    existing_author_ids = {str(link.author_id) for link in existing_authors}
    existing_genre_ids = {str(link.genre_id) for link in existing_genres}
    target_author_ids = set(author_ids)
    target_genre_ids = set(genre_ids)

    for author_id in target_author_ids - existing_author_ids:
        await create_book_author_query(
            BookAuthorCreateRequest(
                book_id=book_id,
                author_id=author_id,
            )
        )

    for author_id in existing_author_ids - target_author_ids:
        await delete_by_book_and_author_query(book_id, author_id)

    for genre_id in target_genre_ids - existing_genre_ids:
        await create_book_genre_query(
            BookGenreCreateRequest(
                book_id=book_id,
                genre_id=genre_id,
            )
        )

    for genre_id in existing_genre_ids - target_genre_ids:
        await delete_by_book_and_genre_query(book_id, genre_id)


async def _rollback_book_creation(
    book_id: str,
    promoted_image_url: str | None = None,
) -> None:
    await delete_query(book_id)
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

    async def create(self, book: BookCreateRequest) -> Response:
        staging_key = staging_key_from_image(book.image) if book.image else None
        create_payload = BookCreateRequest(
            title=book.title,
            synopsis=book.synopsis,
            image="" if staging_key else book.image,
        )
        inserted_id = await create_query(create_payload)
        book_id = str(inserted_id)
        final_image: str | None = None

        try:
            if staging_key:
                final_image = resolve_persisted_book_image(book.image, book_id)
                update = await update_query(book_id, BookUpdateRequest(image=final_image))
                if update.matched_count == 0:
                    raise HTTPException(status_code=500, detail="Failed to save book image")

            _validate_uuids(book.author_ids, "author_id")
            _validate_uuids(book.genre_ids, "genre_id")
            await _sync_book_links(book_id, book.author_ids, book.genre_ids)
        except HTTPException:
            await _rollback_book_creation(book_id, final_image)
            raise
        except Exception as exc:
            await _rollback_book_creation(book_id, final_image)
            raise HTTPException(status_code=500, detail="Failed to create book") from exc

        return JSONResponse(
            status_code=201,
            content={"id": book_id, "message": "Book created"},
        )

    async def update(self, id: str, book: BookUpdateRequest) -> Response:
        existing = await read_by_id_query(id)
        if existing is None:
            raise HTTPException(status_code=404, detail="Book not found")

        update_payload = book.model_dump(exclude_unset=True, exclude={"author_ids", "genre_ids"})
        if book.image is not None:
            update_payload["image"] = resolve_persisted_book_image(
                book.image,
                id,
                old_image=existing.image,
            )

        if update_payload:
            update = await update_query(id, BookUpdateRequest(**update_payload))
            if update.matched_count == 0:
                raise HTTPException(status_code=404, detail="Book not found")

        if book.author_ids is not None or book.genre_ids is not None:
            author_links = await read_book_authors(id)
            genre_links = await read_book_genres(id)
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
            await _sync_book_links(id, next_author_ids, next_genre_ids)

        return Response(status_code=200)

    async def delete(self, id: str) -> Response:
        deleted = await delete_query(id)

        if deleted.matched_count == 0:
            raise HTTPException(status_code=404, detail="Book not found")

        return Response(status_code=204)

    async def read(self, params: ParamRequest) -> PaginatedResponse[BookReadResponse]:
        books_result = await read_query(params)
        books = books_result.data
        if not books:
            return PaginatedResponse[BookReadResponse](
                status_code=200,
                message="Successful",
                data=[],
                pagination=books_result.pagination,
            )

        book_ids = [str(b.id) for b in books]
        author_links = await read_book_authors_batch(book_ids)
        genre_links = await read_book_genres_batch(book_ids)

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

        authors = await read_authors_by_ids(list[str](all_author_ids))
        genres = await read_genres_by_ids(list[str](all_genre_ids))
        author_map = {str(author.id): _author_ref(author) for author in authors}
        genre_map = {str(genre.id): _genre_ref(genre) for genre in genres}

        data: list[BookReadResponse] = []
        for book in books:
            bid = str(book.id)
            author_refs = [author_map[aid] for aid in author_ids_by_book.get(bid, []) if aid in author_map]
            genre_refs = [genre_map[gid] for gid in genre_ids_by_book.get(bid, []) if gid in genre_map]
            data.append(_to_book_read_response(book, author_refs, genre_refs))

        return PaginatedResponse[BookReadResponse](
            status_code=200,
            message="Successful",
            data=data,
            pagination=books_result.pagination,
        )

    async def read_by_id(self, id: str) -> BaseResponse[BookReadResponse]:
        book = await read_by_id_query(id)

        if book is None:
            raise HTTPException(status_code=404, detail="Book not found")

        author_links = await read_book_authors(id)
        genre_links = await read_book_genres(id)
        author_ids = [str(link.author_id) for link in author_links]
        genre_ids = [str(link.genre_id) for link in genre_links]

        authors = await read_authors_by_ids(author_ids)
        genres = await read_genres_by_ids(genre_ids)
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
        return BaseResponse[BookUploadUrlResponse](
            status_code=200, message="Successful", data=data
        )


class WritableBookService(writable_service(BookService)):
    pass


class ReadableBookService(readable_service(BookService)):
    pass
