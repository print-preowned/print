"""
Upload Seed Data Script

This script uploads seed data from CSV files directly to the database.
It supports uploading books, authors, and genres.

Usage:
    python scripts/upload_seeds.py --type authors --file scripts/seeds/authors.csv
    python scripts/upload_seeds.py --type genres --file scripts/seeds/genres.csv
    python scripts/upload_seeds.py --type books --file scripts/seeds/books.csv

    Or upload all:
    python scripts/upload_seeds.py --all
"""

import argparse
import asyncio
import csv
import sys
from pathlib import Path
from typing import Any, Dict

# Add parent directory to path to import app modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.author.model import AuthorCreateRequest
from app.author.repository import AuthorRepository
from app.author.schemas import AuthorCreate
from app.book.model import BookCreateRequest
from app.book.repository import BookRepository
from app.book.schemas import BookCreate
from app.genre.repository import GenreRepository
from app.genre.schemas import GenreCreate
from app.utility.postgres import get_sessionmaker


async def upload_authors(file_path: Path) -> Dict[str, Any]:
    """Upload authors from CSV file directly to database"""
    results = {"success": 0, "failed": 0, "errors": []}

    with open(file_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for idx, row in enumerate(reader, start=2):  # Start at 2 (header is row 1)
            try:
                # Create AuthorCreateRequest to validate data
                author_request = AuthorCreateRequest(
                    first_name=row["first_name"].strip(),
                    last_name=row["last_name"].strip(),
                    middle_name=row.get("middle_name", "").strip() or None,
                    about=row["about"].strip(),
                    image=row.get("image", "").strip() or "",
                    status=row.get("status", "ACTIVE").strip(),
                )

                async with get_sessionmaker()() as session:
                    await AuthorRepository(session).create_author(
                        AuthorCreate.model_validate(
                            author_request.model_dump(include=set(AuthorCreate.model_fields.keys()))
                        )
                    )
                    await session.commit()
                results["success"] += 1
                print(
                    f"✓ Row {idx}: Created author "
                    f"{author_request.first_name} {author_request.last_name}"
                )

            except Exception as e:
                results["failed"] += 1
                error_msg = f"Row {idx}: {str(e)}"
                results["errors"].append(error_msg)
                print(f"✗ {error_msg}")

    return results


async def upload_genres(file_path: Path) -> Dict[str, Any]:
    """Upload genres from CSV file directly to database"""
    results = {"success": 0, "failed": 0, "errors": []}

    with open(file_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for idx, row in enumerate(reader, start=2):
            try:
                genre_payload = GenreCreate(
                    name=row["name"].strip(),
                    description=row.get("description", "").strip() or None,
                )

                async with get_sessionmaker()() as session:
                    await GenreRepository(session).create_genre(genre_payload)
                    await session.commit()
                results["success"] += 1
                print(f"✓ Row {idx}: Created genre {genre_payload.name}")

            except Exception as e:
                results["failed"] += 1
                error_msg = f"Row {idx}: {str(e)}"
                results["errors"].append(error_msg)
                print(f"✗ {error_msg}")

    return results


async def upload_books(file_path: Path) -> Dict[str, Any]:
    """Upload books from CSV file directly to database"""
    results = {"success": 0, "failed": 0, "errors": []}

    with open(file_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for idx, row in enumerate(reader, start=2):
            try:
                # Parse genres (comma-separated)
                genres_str = row["genres"].strip()
                genres = [g.strip() for g in genres_str.split(",") if g.strip()]

                if not genres:
                    raise ValueError("At least one genre is required")

                # Create BookCreateRequest to validate data
                book_request = BookCreateRequest(
                    title=row["title"].strip(),
                    genre_ids=[],
                    image=row["image"].strip(),
                    synopsis=row["synopsis"].strip(),
                )

                async with get_sessionmaker()() as session:
                    await BookRepository(session).create_book(
                        BookCreate.model_validate(
                            book_request.model_dump(include=set(BookCreate.model_fields.keys()))
                        )
                    )
                    await session.commit()
                results["success"] += 1
                print(f"✓ Row {idx}: Created book {book_request.title}")

            except Exception as e:
                results["failed"] += 1
                error_msg = f"Row {idx}: {str(e)}"
                results["errors"].append(error_msg)
                print(f"✗ {error_msg}")

    return results


async def upload_all():
    """Upload all seed files"""
    script_dir = Path(__file__).parent
    seeds_dir = script_dir / "seeds"

    results = {}

    # Upload genres first (books depend on genres)
    genres_file = seeds_dir / "genres.csv"
    if genres_file.exists():
        print("\n=== Uploading Genres ===")
        results["genres"] = await upload_genres(genres_file)
    else:
        print(f"⚠ Genres file not found: {genres_file}")

    # Upload authors
    authors_file = seeds_dir / "authors.csv"
    if authors_file.exists():
        print("\n=== Uploading Authors ===")
        results["authors"] = await upload_authors(authors_file)
    else:
        print(f"⚠ Authors file not found: {authors_file}")

    # Upload books last (may depend on authors and genres)
    books_file = seeds_dir / "books.csv"
    if books_file.exists():
        print("\n=== Uploading Books ===")
        results["books"] = await upload_books(books_file)
    else:
        print(f"⚠ Books file not found: {books_file}")

    return results


def print_summary(results: Dict[str, Dict[str, Any]]):
    """Print upload summary"""
    print("\n" + "=" * 50)
    print("UPLOAD SUMMARY")
    print("=" * 50)

    total_success = 0
    total_failed = 0

    for resource_type, result in results.items():
        success = result.get("success", 0)
        failed = result.get("failed", 0)
        total_success += success
        total_failed += failed

        print(f"\n{resource_type.upper()}:")
        print(f"  ✓ Success: {success}")
        print(f"  ✗ Failed: {failed}")

        if result.get("errors"):
            print("  Errors:")
            for error in result["errors"][:5]:  # Show first 5 errors
                print(f"    - {error}")
            if len(result["errors"]) > 5:
                print(f"    ... and {len(result['errors']) - 5} more errors")

    print("\nTOTAL:")
    print(f"  ✓ Success: {total_success}")
    print(f"  ✗ Failed: {total_failed}")
    print("=" * 50)


async def main():
    parser = argparse.ArgumentParser(
        description="Upload seed data from CSV files directly to database"
    )
    parser.add_argument(
        "--type",
        choices=["authors", "genres", "books"],
        help="Type of data to upload",
    )
    parser.add_argument(
        "--file",
        type=Path,
        help="Path to CSV file",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Upload all seed files",
    )

    args = parser.parse_args()

    try:
        if args.all:
            results = await upload_all()
            print_summary(results)
        elif args.type and args.file:
            if args.type == "authors":
                result = await upload_authors(args.file)
                print_summary({"authors": result})
            elif args.type == "genres":
                result = await upload_genres(args.file)
                print_summary({"genres": result})
            elif args.type == "books":
                result = await upload_books(args.file)
                print_summary({"books": result})
        else:
            parser.print_help()
            sys.exit(1)

    except KeyboardInterrupt:
        print("\n\n⚠ Upload interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Error: {str(e)}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
