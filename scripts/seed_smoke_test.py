"""
Seed smoke-test users and business marketplace data.

Creates:
- Seller user + business (owner) with ACTIVE listings and catalog variants
- Customer user (no business) for buyer / context-switch flows

Prerequisites:
  alembic upgrade head
  python scripts/seed_defaults.py
  python scripts/upload_seeds.py --all

Usage:
  python scripts/seed_smoke_test.py

Optional env:
  PRINT_ST_SELLER_EMAIL   (default: seller@example.com)
  PRINT_ST_SELLER_PASSWORD (default: changeme)
  PRINT_ST_CUSTOMER_EMAIL (default: customer@example.com)
  PRINT_ST_CUSTOMER_PASSWORD (default: changeme)
  PRINT_ST_BUSINESS_NAME  (default: Smoke Test Books)
"""

from __future__ import annotations

import asyncio
import os
import sys
from decimal import Decimal
from pathlib import Path

from pwdlib import PasswordHash
from sqlalchemy import select

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.book.repository import list_books
from app.business.repository import create_business, read_business_by_user_id
from app.business.schemas import BusinessCreate
from app.business_book.orm import BusinessBookOrm
from app.business_book.repository import create_business_book
from app.business_book.schemas import BusinessBookCreate
from app.business_user.repository import create_business_user, read_business_user_by_user_id
from app.business_user.schemas import BusinessUserCreate
from app.role.model import OWNER_ROLE_CODE
from app.role.repository import read_role_by_code
from app.user.repository import create_user, read_user_by_email
from app.user.schemas import UserCreate
from app.utility.postgres import get_sessionmaker
from app.variant.repository import count_variants, create_variant
from app.variant.schemas import VariantCreate
from app.variant_option.repository import read_product_option_value_by_option_and_value
from app.variant_type.repository import read_product_option_by_name

LISTING_COUNT = 3
VARIANT_SPECS = (
    {"condition": "New", "format": "Hardcover", "price": "24.99", "stock": 12, "sku_suffix": "HC"},
    {"condition": "New", "format": "Paperback", "price": "14.99", "stock": 20, "sku_suffix": "PB"},
)


async def ensure_user(
    session,
    *,
    email: str,
    password: str,
    first_name: str,
    last_name: str,
) -> tuple:
    existing = await read_user_by_email(session, email)
    if existing:
        print(f"  - User already exists: {email} (ID: {existing.id})")
        return existing.id, False

    password_hash = PasswordHash.recommended()
    created = await create_user(
        session,
        UserCreate(
            first_name=first_name,
            last_name=last_name,
            email=email,
            password=password_hash.hash(password),
            status="ACTIVE",
        ),
    )
    print(f"  ✓ Created user: {email} (ID: {created.id})")
    return created.id, True


async def ensure_business(session, *, user_id, name: str) -> tuple:
    existing = await read_business_by_user_id(session, user_id)
    if existing:
        print(f"  - Business already exists: {existing.name} (ID: {existing.id})")
        return existing.id, False

    owner_role = await read_role_by_code(session, OWNER_ROLE_CODE)
    if owner_role is None:
        raise RuntimeError("OWNER role not found. Run scripts/seed_defaults.py first.")

    business = await create_business(
        session,
        BusinessCreate(user_id=user_id, name=name, description="Dev smoke-test bookstore"),
    )
    await create_business_user(
        session,
        BusinessUserCreate(
            business_id=business.id,
            user_id=user_id,
            role_id=owner_role.id,
        ),
    )
    print(f"  ✓ Created business: {name} (ID: {business.id})")
    return business.id, True


async def resolve_option_value_ids(session, condition: str, format_value: str) -> list:
    condition_option = await read_product_option_by_name(session, "Condition")
    format_option = await read_product_option_by_name(session, "Format")
    if condition_option is None or format_option is None:
        raise RuntimeError("Product options missing. Run scripts/seed_defaults.py first.")

    condition_value = await read_product_option_value_by_option_and_value(
        session, condition_option.id, condition
    )
    format_row = await read_product_option_value_by_option_and_value(
        session, format_option.id, format_value
    )
    if condition_value is None or format_row is None:
        raise RuntimeError(
            "Product option values missing. Run scripts/seed_defaults.py first."
        )
    return [condition_value.id, format_row.id]


async def ensure_listing(session, *, business_id, book) -> BusinessBookOrm:
    existing = await session.scalar(
        select(BusinessBookOrm).where(
            BusinessBookOrm.business_id == business_id,
            BusinessBookOrm.book_id == book.id,
            BusinessBookOrm.deleted_at.is_(None),
        )
    )
    if existing:
        if existing.status != "ACTIVE":
            existing.status = "ACTIVE"
            await session.flush()
            print(f"  - Activated listing for '{book.title}'")
        else:
            print(f"  - Listing already exists for '{book.title}'")
        return existing

    listing = await create_business_book(
        session,
        BusinessBookCreate(
            book_id=book.id,
            business_id=business_id,
            synopsis=book.synopsis,
            image=book.image,
            status="ACTIVE",
        ),
    )
    print(f"  ✓ Listed '{book.title}' (business_book ID: {listing.id})")
    return listing


async def ensure_variants(session, *, listing: BusinessBookOrm, book_title: str) -> int:
    existing_count = await count_variants(session, business_book_id=listing.id)
    if existing_count > 0:
        print(f"  - {existing_count} variant(s) already exist for '{book_title}'")
        return 0

    created = 0
    slug = book_title.upper().replace(" ", "-")[:24]
    for spec in VARIANT_SPECS:
        option_ids = await resolve_option_value_ids(
            session, spec["condition"], spec["format"]
        )
        await create_variant(
            session,
            VariantCreate(
                business_book_id=listing.id,
                description=f"{spec['format']} — {spec['condition']}",
                stock=spec["stock"],
                price=Decimal(spec["price"]),
                currency="USD",
                sku=f"SMOKE-{slug}-{spec['sku_suffix']}",
                product_option_value_ids=option_ids,
            ),
        )
        created += 1
    print(f"  ✓ Created {created} variant(s) for '{book_title}'")
    return created


async def seed_marketplace(session, business_id) -> None:
    books = await list_books(session, offset=0, limit=LISTING_COUNT)
    if not books:
        raise RuntimeError("No books in catalog. Run scripts/upload_seeds.py --all first.")

    print(f"\nSeeding up to {LISTING_COUNT} business listings and variants...")
    for book in books:
        listing = await ensure_listing(session, business_id=business_id, book=book)
        await ensure_variants(session, listing=listing, book_title=book.title)


async def main() -> None:
    seller_email = os.getenv("PRINT_ST_SELLER_EMAIL", "seller@example.com")
    seller_password = os.getenv("PRINT_ST_SELLER_PASSWORD", "changeme")
    customer_email = os.getenv("PRINT_ST_CUSTOMER_EMAIL", "customer@example.com")
    customer_password = os.getenv("PRINT_ST_CUSTOMER_PASSWORD", "changeme")
    business_name = os.getenv("PRINT_ST_BUSINESS_NAME", "Smoke Test Books")

    print("Seeding Smoke Test Users & Business Flows")
    print("=" * 60)

    async with get_sessionmaker()() as session:
        print("\n1. Seller user")
        seller_id, _ = await ensure_user(
            session,
            email=seller_email,
            password=seller_password,
            first_name="Smoke",
            last_name="Seller",
        )

        print("\n2. Customer user")
        customer_id, _ = await ensure_user(
            session,
            email=customer_email,
            password=customer_password,
            first_name="Smoke",
            last_name="Customer",
        )

        print("\n3. Business + owner membership")
        business_id, _ = await ensure_business(
            session, user_id=seller_id, name=business_name
        )

        membership = await read_business_user_by_user_id(session, seller_id)
        if membership is None:
            raise RuntimeError("Failed to create business_user membership")

        await seed_marketplace(session, business_id)
        await session.commit()

    print("\n" + "=" * 60)
    print("✓ Smoke test data ready")
    print("=" * 60)
    print("\nSeller (business owner):")
    print(f"  Email:    {seller_email}")
    print(f"  Password: {seller_password}")
    print(f"  Business: {business_name}")
    print(f"  User ID:  {seller_id}")
    print(f"  Business ID: {business_id}")
    print("\nCustomer (no business):")
    print(f"  Email:    {customer_email}")
    print(f"  Password: {customer_password}")
    print(f"  User ID:  {customer_id}")
    print("\nSmoke test checklist:")
    print("  1. Login as seller → switch to business context")
    print("  2. View seller inventory / listings")
    print("  3. Browse public catalog (no login)")
    print("  4. Login as customer → browse / order flows")
    print("=" * 60)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as exc:
        print(f"\n✗ Error during seeding: {exc}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
