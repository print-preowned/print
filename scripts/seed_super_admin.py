"""
Seed Super Admin User Script

This script creates a platform super admin user for bootstrapping the platform.

Following MDC-PU bootstrap_super_admin:
- Creates USER with status "NEW" (forces password change on first login)
- Creates PLATFORM_USER linked to Super Admin privilege set
- Uses environment variables for admin credentials

Usage:
    SUPER_ADMIN_EMAIL=admin@example.com SUPER_ADMIN_PASSWORD=changeme python scripts/seed_super_admin.py
"""

import asyncio
import sys
import os
from pathlib import Path

# Add parent directory to path to import app modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.user.model import UserCreateRequest
from app.user.query import create_query as create_user_query, read_by_email_query
from app.platform_user.model import PlatformUserCreateRequest
from app.platform_user.query import create_query as create_platform_user_query, read_by_user_id_query
from app.utility.model import PyObjectId
from app.utility.database import get_database
from pwdlib import PasswordHash


async def find_super_admin_privilege_set():
    """Find the Super Admin privilege set by name"""
    print("Finding Super Admin privilege set...")
    
    db = get_database()
    collection = db["platform_privilege_set"]
    
    # Find by name
    record = await collection.find_one(
        {"name": "Super Admin", "status": {"$ne": "DELETED"}}
    )
    
    if not record:
        raise Exception(
            "Super Admin privilege set not found. "
            "Please run 'python scripts/seed_defaults.py' first to create platform privilege sets."
        )
    
    privilege_set_id = PyObjectId(record["_id"])
    print(f"  ✓ Found Super Admin privilege set (ID: {privilege_set_id})")
    return privilege_set_id


async def create_super_admin_user(email: str, password: str, first_name: str = "Super", last_name: str = "Admin"):
    """Create a super admin user"""
    print(f"\nCreating super admin user: {email}")
    
    # Check if user already exists
    existing_user = await read_by_email_query(email)
    if existing_user:
        print(f"  - User with email {email} already exists")
        
        # Check if they already have a platform_user record
        platform_user = await read_by_user_id_query(str(existing_user.id))
        if platform_user:
            print(f"  - User already has a platform_user record")
            return existing_user.id, platform_user.id
        
        # User exists but no platform_user - create it
        print(f"  - Creating platform_user record for existing user...")
        privilege_set_id = await find_super_admin_privilege_set()
        
        platform_user_data = PlatformUserCreateRequest(
            user_id=str(existing_user.id),
            platform_privilege_set_id=privilege_set_id,
            status="ACTIVE"
        )
        await create_platform_user_query(platform_user_data)
        
        # Get the created platform_user
        created_platform_user = await read_by_user_id_query(str(existing_user.id))
        print(f"  ✓ Created platform_user record (ID: {created_platform_user.id if created_platform_user else 'None'})")
        return existing_user.id, created_platform_user.id if created_platform_user else None
    
    # Create new user with status "NEW" to force password change
    password_hash = PasswordHash.recommended()
    hashed_password = password_hash.hash(password)
    
    user_data = UserCreateRequest(
        first_name=first_name,
        last_name=last_name,
        email=email,
        password=hashed_password,
        status="NEW"  # Force password change on first login (MDC-PU bootstrap_super_admin)
    )
    
    await create_user_query(user_data)
    
    # Get the created user
    created_user = await read_by_email_query(email)
    if not created_user:
        raise Exception("Failed to retrieve created user")
    
    print(f"  ✓ Created user (ID: {created_user.id}, status: NEW)")
    
    # Create platform_user record
    privilege_set_id = await find_super_admin_privilege_set()
    
    platform_user_data = PlatformUserCreateRequest(
        user_id=str(created_user.id),
        platform_privilege_set_id=privilege_set_id,
        status="ACTIVE"
    )
    
    await create_platform_user_query(platform_user_data)
    
    # Get the created platform_user
    created_platform_user = await read_by_user_id_query(str(created_user.id))
    if not created_platform_user:
        raise Exception("Failed to retrieve created platform_user")
    
    print(f"  ✓ Created platform_user (ID: {created_platform_user.id})")
    
    return created_user.id, created_platform_user.id


async def main():
    print("Seeding Super Admin User")
    print("=" * 60)
    
    # Get credentials from environment variables
    email = os.getenv("PRINT_SA_EMAIL")
    password = os.getenv("PRINT_SA_PASSWORD")
    first_name = os.getenv("PRINT_SA_FNAME", "Super")
    last_name = os.getenv("PRINT_SA_LNAME", "Admin")
    print(email)
    if not email:
        print("\n✗ Error: SUPER_ADMIN_EMAIL environment variable is required")
        print("\nUsage:")
        print("  SUPER_ADMIN_EMAIL=admin@example.com SUPER_ADMIN_PASSWORD=changeme python scripts/seed_super_admin.py")
        sys.exit(1)
    
    if not password:
        print("\n✗ Error: SUPER_ADMIN_PASSWORD environment variable is required")
        print("\nUsage:")
        print("  SUPER_ADMIN_EMAIL=admin@example.com SUPER_ADMIN_PASSWORD=changeme python scripts/seed_super_admin.py")
        sys.exit(1)
    
    try:
        user_id, platform_user_id = await create_super_admin_user(
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name
        )
        
        print("\n" + "=" * 60)
        print("✓ Super admin user created successfully!")
        print("=" * 60)
        print(f"\nUser ID: {user_id}")
        print(f"Platform User ID: {platform_user_id}")
        print(f"Email: {email}")
        print(f"Status: NEW (password change required on first login)")
        print("\n⚠️  IMPORTANT: Change the password after first login!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n✗ Error during seeding: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
