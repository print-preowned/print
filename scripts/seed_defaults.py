"""
Seed Default Records Script

This script creates default records for:
1. Roles (OWNER role)
2. Privileges (from app.auth.privilege_catalog)
3. Role-Privilege mappings (owner-default privileges mapped to OWNER role)
4. Platform Privileges
5. Platform Privilege Sets
6. Platform Privilege Set-Privilege mappings

Run with: python scripts/seed_defaults.py
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.auth.privilege_catalog import (
    PLATFORM_PRIVILEGE_SETS,
    PLATFORM_PRIVILEGES,
    business_privilege_defs,
)
from app.role.model import RoleCreateRequest, OWNER_ROLE_CODE
from app.role.query import create_query as create_role_query, read_by_code_query as read_role_by_code_query
from app.privilege.model import PrivilegeCreateRequest
from app.privilege.query import create_query as create_privilege_query, read_by_code_query as read_privilege_by_code_query
from app.role_privilege.model import RolePrivilegeCreateRequest
from app.role_privilege.query import create_query as create_role_privilege_query, read_by_role_and_privilege_query
from app.platform_privilege.model import PlatformPrivilegeCreateRequest
from app.platform_privilege.query import create_query as create_platform_privilege_query, read_by_code_query as read_platform_privilege_by_code_query
from app.platform_privilege_set.model import PlatformPrivilegeSetCreateRequest
from app.platform_privilege_set.query import create_query as create_platform_privilege_set_query
from app.platform_privilege_set_privilege.model import PlatformPrivilegeSetPrivilegeCreateRequest
from app.platform_privilege_set_privilege.query import create_query as create_platform_privilege_set_privilege_query, read_by_privilege_set_and_privilege_query
from app.utility.model import PyObjectId

VARIANT_TYPES = {
    "Condition": ["New", "Like New", "Very Good", "Good", "Acceptable"],
    "Format": ["Hardcover", "Paperback", "Mass Market", "Other"],
}


async def create_owner_role():
    print("Creating OWNER role...")
    existing_role = await read_role_by_code_query(OWNER_ROLE_CODE)
    if existing_role:
        print(f"  ✓ OWNER role already exists (ID: {existing_role.id})")
        return existing_role.id

    role_data = RoleCreateRequest(
        name="Owner",
        code=OWNER_ROLE_CODE,
        description="Business owner role with full access to all privileges",
        status="ACTIVE",
    )
    role_id = await create_role_query(role_data)
    print(f"  ✓ Created OWNER role (ID: {role_id})")
    return role_id


async def seed_business_privilege(privilege_def, owner_role_id: PyObjectId) -> tuple[bool, bool]:
    created = False
    mapped = False

    existing_privilege = await read_privilege_by_code_query(privilege_def.code)
    if existing_privilege:
        print(f"    - {privilege_def.code} already exists")
    else:
        await create_privilege_query(
            PrivilegeCreateRequest(
                code=privilege_def.code,
                name=privilege_def.name,
                module_name=privilege_def.module,
                status="ACTIVE",
            )
        )
        created = True
        print(f"    ✓ Created {privilege_def.code}")

    if not privilege_def.owner_default:
        return created, mapped

    role_id_str = str(owner_role_id)
    existing_mapping = await read_by_role_and_privilege_query(role_id_str, privilege_def.code)
    if existing_mapping:
        print(f"    - {privilege_def.code} already mapped to OWNER role")
    else:
        await create_role_privilege_query(
            RolePrivilegeCreateRequest(
                role_id=owner_role_id,
                privilege_code=privilege_def.code,
                status="ACTIVE",
            )
        )
        mapped = True
        print(f"    ✓ Mapped {privilege_def.code} to OWNER role")

    return created, mapped


async def create_all_privileges(owner_role_id: PyObjectId):
    print("\nCreating business privileges from catalog...")
    total_created = 0
    total_mapped = 0

    for privilege_def in business_privilege_defs():
        created, mapped = await seed_business_privilege(privilege_def, owner_role_id)
        total_created += int(created)
        total_mapped += int(mapped)

    print(f"\n  Summary: Created {total_created} privileges, mapped {total_mapped} to OWNER role")
    return total_created, total_mapped


async def create_platform_privileges():
    print("\nCreating platform privileges...")
    created_count = 0

    for priv_info in PLATFORM_PRIVILEGES:
        existing = await read_platform_privilege_by_code_query(priv_info.code)
        if existing:
            print(f"  - {priv_info.code} already exists")
        else:
            await create_platform_privilege_query(
                PlatformPrivilegeCreateRequest(
                    code=priv_info.code,
                    description=priv_info.description,
                    status="ACTIVE",
                )
            )
            created_count += 1
            print(f"  ✓ Created {priv_info.code}")

    print(f"  Summary: Created {created_count} platform privileges")
    return created_count


async def create_platform_privilege_sets():
    print("\nCreating platform privilege sets...")
    from app.utility.database import get_database

    created_sets = 0
    created_mappings = 0
    db = get_database()
    collection = db["platform_privilege_set"]

    for set_info in PLATFORM_PRIVILEGE_SETS:
        existing_record = await collection.find_one(
            {"name": set_info.name, "status": {"$ne": "DELETED"}}
        )

        if existing_record:
            privilege_set_id = PyObjectId(existing_record["_id"])
            print(f"  - Privilege set '{set_info.name}' already exists (ID: {privilege_set_id})")
        else:
            await create_platform_privilege_set_query(
                PlatformPrivilegeSetCreateRequest(name=set_info.name, status="ACTIVE")
            )
            created_sets += 1
            print(f"  ✓ Created privilege set: {set_info.name}")

            record = await collection.find_one(
                {"name": set_info.name, "status": {"$ne": "DELETED"}},
                sort=[("created_at", -1)],
            )
            if not record:
                print(f"    ⚠ Warning: Could not find created privilege set '{set_info.name}'")
                continue
            privilege_set_id = PyObjectId(record["_id"])

        for privilege_code in set_info.privileges:
            existing_mapping = await read_by_privilege_set_and_privilege_query(
                str(privilege_set_id), privilege_code
            )
            if existing_mapping:
                print(f"    - {privilege_code} already mapped to {set_info.name}")
            else:
                await create_platform_privilege_set_privilege_query(
                    PlatformPrivilegeSetPrivilegeCreateRequest(
                        privilege_set_id=privilege_set_id,
                        privilege_code=privilege_code,
                        status="ACTIVE",
                    )
                )
                created_mappings += 1
                print(f"    ✓ Mapped {privilege_code} to {set_info.name}")

    print(f"\n  Summary: Created {created_sets} privilege sets, created {created_mappings} mappings")
    return created_sets, created_mappings


async def seed_variant_vocabulary():
    from app.utility.database import get_database
    from datetime import datetime, timezone

    print("\nSeeding variant vocabulary...")
    db = get_database()
    type_collection = db["variant_type"]
    option_collection = db["variant_option"]
    now = datetime.now(timezone.utc)
    created_types = 0
    created_options = 0

    for type_name, options in VARIANT_TYPES.items():
        existing_type = await type_collection.find_one(
            {"name": type_name, "status": {"$ne": "DELETED"}}
        )
        if existing_type:
            type_id = existing_type["_id"]
            print(f"  - Variant type '{type_name}' already exists")
        else:
            result = await type_collection.insert_one(
                {
                    "name": type_name,
                    "status": "ACTIVE",
                    "created_at": now,
                    "updated_at": now,
                }
            )
            type_id = result.inserted_id
            created_types += 1
            print(f"  ✓ Created variant type: {type_name}")

        for value in options:
            existing_option = await option_collection.find_one(
                {
                    "variant_type_id": type_id,
                    "value": value,
                    "status": {"$ne": "DELETED"},
                }
            )
            if existing_option:
                print(f"    - Option '{value}' already exists")
            else:
                await option_collection.insert_one(
                    {
                        "variant_type_id": type_id,
                        "value": value,
                        "status": "ACTIVE",
                        "created_at": now,
                        "updated_at": now,
                    }
                )
                created_options += 1
                print(f"    ✓ Created option: {value}")

    print(f"  Summary: Created {created_types} variant types, {created_options} options")
    return created_types, created_options


async def main():
    print("=" * 60)
    print("Seeding Default Records")
    print("=" * 60)

    try:
        owner_role_id = await create_owner_role()
        await create_all_privileges(owner_role_id)
        await create_platform_privileges()
        await create_platform_privilege_sets()
        await seed_variant_vocabulary()

        print("\n" + "=" * 60)
        print("✓ Seeding completed successfully!")
        print("=" * 60)
    except Exception as e:
        print(f"\n✗ Error during seeding: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
