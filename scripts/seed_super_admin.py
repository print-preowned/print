"""
Seed Super Admin User Script

This script creates a platform super admin user for bootstrapping the platform.

Following MDC-PU bootstrap_super_admin:
- Creates USER with status "NEW" (forces password change on first login)
- Creates PLATFORM_USER linked to Super Admin privilege set
- Uses environment variables for admin credentials

Usage:
    PRINT_SA_EMAIL=admin@example.com PRINT_SA_PASSWORD=changeme python scripts/seed_super_admin.py
"""

import asyncio
import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.platform_privilege_set.repository import read_platform_privilege_set_by_name
from app.platform_user.model import PlatformUserCreateRequest
from app.platform_user.repository import create_platform_user, read_platform_user_by_user_id
from app.platform_user.schemas import PlatformUserCreate
from app.user.model import UserCreateRequest
from app.user.repository import create_user, read_user_by_email
from app.user.schemas import UserCreate
from app.utility.postgres import get_sessionmaker
from pwdlib import PasswordHash


async def find_super_admin_privilege_set_id(session):
    print("Finding Super Admin privilege set...")
    record = await read_platform_privilege_set_by_name(session, "Super Admin")
    if not record:
        raise Exception(
            "Super Admin privilege set not found. "
            "Please run 'python scripts/seed_defaults.py' first to create platform privilege sets."
        )
    print(f"  ✓ Found Super Admin privilege set (ID: {record.id})")
    return record.id


async def create_super_admin_user(email: str, password: str, first_name: str = "Super", last_name: str = "Admin"):
    print(f"\nCreating super admin user: {email}")

    async with get_sessionmaker()() as session:
        existing_user = await read_user_by_email(session, email)
        if existing_user:
            print(f"  - User with email {email} already exists")
            platform_user = await read_platform_user_by_user_id(session, existing_user.id)
            if platform_user:
                print("  - User already has a platform_user record")
                return existing_user.id, platform_user.id

            print("  - Creating platform_user record for existing user...")
            privilege_set_id = await find_super_admin_privilege_set_id(session)
            await create_platform_user(
                session,
                PlatformUserCreate(
                    user_id=existing_user.id,
                    platform_privilege_set_id=privilege_set_id,
                    status="ACTIVE",
                ),
            )
            await session.commit()
            platform_user = await read_platform_user_by_user_id(session, existing_user.id)
            print(f"  ✓ Created platform_user record (ID: {platform_user.id if platform_user else 'None'})")
            return existing_user.id, platform_user.id if platform_user else None

        password_hash = PasswordHash.recommended()
        hashed_password = password_hash.hash(password)
        created_user = await create_user(
            session,
            UserCreate(
                first_name=first_name,
                last_name=last_name,
                email=email,
                password=hashed_password,
                status="NEW",
            ),
        )
        print(f"  ✓ Created user (ID: {created_user.id}, status: NEW)")

        privilege_set_id = await find_super_admin_privilege_set_id(session)
        platform_user = await create_platform_user(
            session,
            PlatformUserCreate(
                user_id=created_user.id,
                platform_privilege_set_id=privilege_set_id,
                status="ACTIVE",
            ),
        )
        await session.commit()
        print(f"  ✓ Created platform_user (ID: {platform_user.id})")
        return created_user.id, platform_user.id


async def main():
    print("Seeding Super Admin User")
    print("=" * 60)

    email = os.getenv("PRINT_SA_EMAIL")
    password = os.getenv("PRINT_SA_PASSWORD")
    first_name = os.getenv("PRINT_SA_FNAME", "Super")
    last_name = os.getenv("PRINT_SA_LNAME", "Admin")

    if not email:
        print("\n✗ Error: PRINT_SA_EMAIL environment variable is required")
        print("\nUsage:")
        print("  PRINT_SA_EMAIL=admin@example.com PRINT_SA_PASSWORD=changeme python scripts/seed_super_admin.py")
        sys.exit(1)

    if not password:
        print("\n✗ Error: PRINT_SA_PASSWORD environment variable is required")
        print("\nUsage:")
        print("  PRINT_SA_EMAIL=admin@example.com PRINT_SA_PASSWORD=changeme python scripts/seed_super_admin.py")
        sys.exit(1)

    try:
        user_id, platform_user_id = await create_super_admin_user(
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
        )

        print("\n" + "=" * 60)
        print("✓ Super admin user created successfully!")
        print("=" * 60)
        print(f"\nUser ID: {user_id}")
        print(f"Platform User ID: {platform_user_id}")
        print(f"Email: {email}")
        print("Status: NEW (password change required on first login)")
        print("\n⚠️  IMPORTANT: Change the password after first login!")
        print("=" * 60)

    except Exception as e:
        print(f"\n✗ Error during seeding: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
