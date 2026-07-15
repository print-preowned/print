"""
Seed smoke-test users and business marketplace data.

Creates:
- Seller user + business (owner) with ACTIVE listings and catalog variants
- Five additional marketplace sellers, each listing multiple books with variants
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

from app.book.repository import BookRepository
from app.business.repository import BusinessRepository
from app.business.schemas import BusinessCreate
from app.business_book.orm import BusinessBookOrm
from app.business_book.repository import BusinessBookRepository
from app.business_book.schemas import BusinessBookCreate
from app.business_user.repository import BusinessUserRepository
from app.business_user.schemas import BusinessUserCreate
from app.role.model import OWNER_ROLE_CODE
from app.role.repository import RoleRepository
from app.user.repository import UserRepository
from app.user.schemas import UserCreate
from app.utility.postgres import get_sessionmaker
from app.variant.repository import VariantRepository
from app.variant.schemas import VariantCreate
from app.variant_option.repository import VariantOptionRepository
from app.variant_type.repository import VariantTypeRepository

LISTING_COUNT = 3
VARIANT_SPECS = (
    {"condition": "New", "format": "Hardcover", "price": "24.99", "stock": 12, "sku_suffix": "HC"},
    {"condition": "New", "format": "Paperback", "price": "14.99", "stock": 20, "sku_suffix": "PB"},
)

# Extra marketplace shops: each gets its own owner + overlapping book slices.
EXTRA_MARKETPLACES = (
    {
        "email": "harbor@example.com",
        "password": "changeme",
        "first_name": "Harbor",
        "last_name": "Books",
        "business_name": "Harbor Lane Books",
        "description": "Coastal indie bookstore with new releases",
        "book_offset": 0,
        "listing_count": 5,
        "sku_prefix": "HARBOR",
        "variant_specs": (
            {"condition": "New", "format": "Hardcover", "price": "28.50", "stock": 8, "sku_suffix": "HC"},
            {"condition": "New", "format": "Paperback", "price": "16.99", "stock": 18, "sku_suffix": "PB"},
            {"condition": "Like New", "format": "Paperback", "price": "12.50", "stock": 6, "sku_suffix": "LN"},
        ),
    },
    {
        "email": "folio@example.com",
        "password": "changeme",
        "first_name": "Folio",
        "last_name": "Press",
        "business_name": "Folio & Co.",
        "description": "Curated literary fiction and classics",
        "book_offset": 2,
        "listing_count": 4,
        "sku_prefix": "FOLIO",
        "variant_specs": (
            {"condition": "New", "format": "Hardcover", "price": "32.00", "stock": 5, "sku_suffix": "HC"},
            {"condition": "Very Good", "format": "Paperback", "price": "11.99", "stock": 14, "sku_suffix": "VG"},
        ),
    },
    {
        "email": "pagecraft@example.com",
        "password": "changeme",
        "first_name": "Page",
        "last_name": "Craft",
        "business_name": "Pagecraft Collective",
        "description": "Community co-op for genre readers",
        "book_offset": 4,
        "listing_count": 6,
        "sku_prefix": "PAGE",
        "variant_specs": (
            {"condition": "New", "format": "Paperback", "price": "15.49", "stock": 22, "sku_suffix": "PB"},
            {"condition": "Good", "format": "Mass Market", "price": "7.99", "stock": 30, "sku_suffix": "MM"},
            {"condition": "New", "format": "Hardcover", "price": "26.99", "stock": 9, "sku_suffix": "HC"},
        ),
    },
    {
        "email": "northstar@example.com",
        "password": "changeme",
        "first_name": "North",
        "last_name": "Star",
        "business_name": "Northstar Rare & New",
        "description": "Mix of new printings and gently used stock",
        "book_offset": 6,
        "listing_count": 5,
        "sku_prefix": "NORTH",
        "variant_specs": (
            {"condition": "Like New", "format": "Hardcover", "price": "22.00", "stock": 4, "sku_suffix": "HC"},
            {"condition": "Acceptable", "format": "Paperback", "price": "6.50", "stock": 11, "sku_suffix": "ACC"},
            {"condition": "New", "format": "Paperback", "price": "13.99", "stock": 16, "sku_suffix": "PB"},
        ),
    },
    {
        "email": "inkwell@example.com",
        "password": "changeme",
        "first_name": "Ink",
        "last_name": "Well",
        "business_name": "Inkwell Market",
        "description": "Everyday bestsellers across formats",
        "book_offset": 8,
        "listing_count": 5,
        "sku_prefix": "INK",
        "variant_specs": (
            {"condition": "New", "format": "Hardcover", "price": "29.99", "stock": 10, "sku_suffix": "HC"},
            {"condition": "New", "format": "Paperback", "price": "17.49", "stock": 25, "sku_suffix": "PB"},
            {"condition": "Very Good", "format": "Hardcover", "price": "19.99", "stock": 7, "sku_suffix": "VG"},
        ),
    },
)


async def ensure_user(
    session,
    *,
    email: str,
    password: str,
    first_name: str,
    last_name: str,
) -> tuple:
    existing = await UserRepository(session).read_user_by_email(email)
    if existing:
        print(f"  - User already exists: {email} (ID: {existing.id})")
        return existing.id, False

    password_hash = PasswordHash.recommended()
    created = await UserRepository(session).create_user(
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


async def ensure_business(
    session,
    *,
    user_id,
    name: str,
    description: str = "Dev smoke-test bookstore",
) -> tuple:
    existing = await BusinessRepository(session).read_by_user_id(user_id)
    if existing:
        print(f"  - Business already exists: {existing.name} (ID: {existing.id})")
        return existing.id, False

    owner_role = await RoleRepository(session).read_role_by_code(OWNER_ROLE_CODE)
    if owner_role is None:
        raise RuntimeError("OWNER role not found. Run scripts/seed_defaults.py first.")

    business = await BusinessRepository(session).create(
        BusinessCreate(user_id=user_id, name=name, description=description),
    )
    await BusinessUserRepository(session).create_business_user(
        BusinessUserCreate(
            business_id=business.id,
            user_id=user_id,
            role_id=owner_role.id,
        ),
    )
    print(f"  ✓ Created business: {name} (ID: {business.id})")
    return business.id, True


async def resolve_option_value_ids(session, condition: str, format_value: str) -> list:
    condition_option = await VariantTypeRepository(session).read_product_option_by_name("Condition")
    format_option = await VariantTypeRepository(session).read_product_option_by_name("Format")
    if condition_option is None or format_option is None:
        raise RuntimeError("Product options missing. Run scripts/seed_defaults.py first.")

    condition_value = await VariantOptionRepository(
        session
    ).read_product_option_value_by_option_and_value(condition_option.id, condition)
    format_row = await VariantOptionRepository(
        session
    ).read_product_option_value_by_option_and_value(format_option.id, format_value)
    if condition_value is None or format_row is None:
        raise RuntimeError("Product option values missing. Run scripts/seed_defaults.py first.")
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

    listing = await BusinessBookRepository(session).create_business_book(
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


async def ensure_variants(
    session,
    *,
    listing: BusinessBookOrm,
    book_title: str,
    sku_prefix: str = "SMOKE",
    variant_specs=VARIANT_SPECS,
) -> int:
    existing_count = await VariantRepository(session).count_variants(business_book_id=listing.id)
    if existing_count > 0:
        print(f"  - {existing_count} variant(s) already exist for '{book_title}'")
        return 0

    created = 0
    slug = book_title.upper().replace(" ", "-")[:24]
    for spec in variant_specs:
        option_ids = await resolve_option_value_ids(session, spec["condition"], spec["format"])
        await VariantRepository(session).create_variant(
            VariantCreate(
                business_book_id=listing.id,
                description=f"{spec['format']} — {spec['condition']}",
                stock=spec["stock"],
                price=Decimal(spec["price"]),
                currency="USD",
                sku=f"{sku_prefix}-{slug}-{spec['sku_suffix']}",
                product_option_value_ids=option_ids,
            ),
        )
        created += 1
    print(f"  ✓ Created {created} variant(s) for '{book_title}'")
    return created


async def seed_marketplace(
    session,
    business_id,
    *,
    offset: int = 0,
    listing_count: int = LISTING_COUNT,
    sku_prefix: str = "SMOKE",
    variant_specs=VARIANT_SPECS,
) -> None:
    books = await BookRepository(session).list_books(offset=offset, limit=listing_count)
    if not books:
        raise RuntimeError("No books in catalog. Run scripts/upload_seeds.py --all first.")

    print(f"\nSeeding up to {listing_count} business listings and variants (offset={offset})...")
    for book in books:
        listing = await ensure_listing(session, business_id=business_id, book=book)
        await ensure_variants(
            session,
            listing=listing,
            book_title=book.title,
            sku_prefix=sku_prefix,
            variant_specs=variant_specs,
        )


async def seed_extra_marketplace(session, shop: dict) -> dict:
    print(f"\n--- {shop['business_name']} ---")
    seller_id, _ = await ensure_user(
        session,
        email=shop["email"],
        password=shop["password"],
        first_name=shop["first_name"],
        last_name=shop["last_name"],
    )
    business_id, _ = await ensure_business(
        session,
        user_id=seller_id,
        name=shop["business_name"],
        description=shop["description"],
    )
    membership = await BusinessUserRepository(session).read_business_user_by_user_id(seller_id)
    if membership is None:
        raise RuntimeError(f"Failed to create business_user membership for {shop['email']}")

    await seed_marketplace(
        session,
        business_id,
        offset=shop["book_offset"],
        listing_count=shop["listing_count"],
        sku_prefix=shop["sku_prefix"],
        variant_specs=shop["variant_specs"],
    )
    return {
        "email": shop["email"],
        "password": shop["password"],
        "business_name": shop["business_name"],
        "user_id": seller_id,
        "business_id": business_id,
        "listing_count": shop["listing_count"],
    }


async def main() -> None:
    seller_email = os.getenv("PRINT_ST_SELLER_EMAIL", "seller@example.com")
    seller_password = os.getenv("PRINT_ST_SELLER_PASSWORD", "changeme")
    customer_email = os.getenv("PRINT_ST_CUSTOMER_EMAIL", "customer@example.com")
    customer_password = os.getenv("PRINT_ST_CUSTOMER_PASSWORD", "changeme")
    business_name = os.getenv("PRINT_ST_BUSINESS_NAME", "Smoke Test Books")

    print("Seeding Smoke Test Users & Business Flows")
    print("=" * 60)

    extra_shops: list[dict] = []
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
        business_id, _ = await ensure_business(session, user_id=seller_id, name=business_name)

        membership = await BusinessUserRepository(session).read_business_user_by_user_id(seller_id)
        if membership is None:
            raise RuntimeError("Failed to create business_user membership")

        await seed_marketplace(session, business_id)

        print("\n4. Extra marketplace businesses")
        for shop in EXTRA_MARKETPLACES:
            extra_shops.append(await seed_extra_marketplace(session, shop))

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
    print("\nExtra marketplace sellers:")
    for shop in extra_shops:
        print(
            f"  - {shop['business_name']}: {shop['email']} / {shop['password']} "
            f"({shop['listing_count']} books)"
        )
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
