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
import uuid
from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.auth.privilege_catalog import (
    PLATFORM_PRIVILEGE_SETS,
    PLATFORM_PRIVILEGES,
    business_privilege_defs,
)
from app.platform_privilege.repository import PlatformPrivilegeRepository
from app.platform_privilege.schemas import PlatformPrivilegeCreate
from app.platform_privilege_set.repository import PlatformPrivilegeSetRepository
from app.platform_privilege_set.schemas import PlatformPrivilegeSetCreate
from app.platform_privilege_set_privilege.repository import PlatformPrivilegeSetPrivilegeRepository
from app.platform_privilege_set_privilege.schemas import PlatformPrivilegeSetPrivilegeCreate
from app.privilege.repository import PrivilegeRepository
from app.privilege.schemas import PrivilegeCreate
from app.role.model import OWNER_ROLE_CODE
from app.role.repository import RoleRepository
from app.role.schemas import RoleCreate
from app.role_privilege.repository import RolePrivilegeRepository
from app.role_privilege.schemas import RolePrivilegeCreate
from app.utility.postgres import get_sessionmaker
from app.variant_option.repository import VariantOptionRepository
from app.variant_option.schemas import ProductOptionValueCreate
from app.variant_type.repository import VariantTypeRepository
from app.variant_type.schemas import ProductOptionCreate

VARIANT_TYPES = {
    "Condition": ["New", "Like New", "Very Good", "Good", "Acceptable"],
    "Format": ["Hardcover", "Paperback", "Mass Market", "Other"],
}


async def create_owner_role(session: AsyncSession) -> uuid.UUID:
    print("Creating OWNER role...")
    existing_role = await RoleRepository(session).read_role_by_code(OWNER_ROLE_CODE)
    if existing_role:
        print(f"  ✓ OWNER role already exists (ID: {existing_role.id})")
        return existing_role.id

    role = await RoleRepository(session).create_role(
        RoleCreate(
            name="Owner",
            code=OWNER_ROLE_CODE,
            description="Business owner role with full access to all privileges",
        ),
    )
    print(f"  ✓ Created OWNER role (ID: {role.id})")
    return role.id


async def seed_business_privilege(
    session: AsyncSession, privilege_def, owner_role_id: uuid.UUID
) -> tuple[bool, bool]:
    created = False
    mapped = False

    existing_privilege = await PrivilegeRepository(session).read_privilege_by_code(
        privilege_def.code
    )
    if existing_privilege:
        print(f"    - {privilege_def.code} already exists")
    else:
        await PrivilegeRepository(session).create_privilege(
            PrivilegeCreate(
                code=privilege_def.code,
                name=privilege_def.name,
                module_name=privilege_def.module,
            ),
        )
        created = True
        print(f"    ✓ Created {privilege_def.code}")

    if not privilege_def.owner_default:
        return created, mapped

    existing_mapping = await RolePrivilegeRepository(session).read_role_privilege_by_role_and_code(
        owner_role_id, privilege_def.code
    )
    if existing_mapping:
        print(f"    - {privilege_def.code} already mapped to OWNER role")
    else:
        await RolePrivilegeRepository(session).create_role_privilege(
            RolePrivilegeCreate(
                role_id=owner_role_id,
                privilege_code=privilege_def.code,
            ),
        )
        mapped = True
        print(f"    ✓ Mapped {privilege_def.code} to OWNER role")

    return created, mapped


async def create_all_privileges(session: AsyncSession, owner_role_id: uuid.UUID):
    print("\nCreating business privileges from catalog...")
    total_created = 0
    total_mapped = 0

    for privilege_def in business_privilege_defs():
        created, mapped = await seed_business_privilege(session, privilege_def, owner_role_id)
        total_created += int(created)
        total_mapped += int(mapped)

    print(f"\n  Summary: Created {total_created} privileges, mapped {total_mapped} to OWNER role")
    return total_created, total_mapped


async def seed_business_auth():
    async with get_sessionmaker()() as session:
        owner_role_id = await create_owner_role(session)
        await create_all_privileges(session, owner_role_id)
        await session.commit()


async def create_platform_privileges(session: AsyncSession) -> int:
    print("\nCreating platform privileges...")
    created_count = 0

    for priv_info in PLATFORM_PRIVILEGES:
        existing = await PlatformPrivilegeRepository(session).read_platform_privilege_by_code(
            priv_info.code
        )
        if existing:
            print(f"  - {priv_info.code} already exists")
        else:
            await PlatformPrivilegeRepository(session).create_platform_privilege(
                PlatformPrivilegeCreate(
                    code=priv_info.code,
                    description=priv_info.description,
                ),
            )
            created_count += 1
            print(f"  ✓ Created {priv_info.code}")

    print(f"  Summary: Created {created_count} platform privileges")
    return created_count


async def create_platform_privilege_sets(session: AsyncSession) -> tuple[int, int]:
    print("\nCreating platform privilege sets...")
    created_sets = 0
    created_mappings = 0

    for set_info in PLATFORM_PRIVILEGE_SETS:
        existing_record = await PlatformPrivilegeSetRepository(
            session
        ).read_platform_privilege_set_by_name(set_info.name)

        if existing_record:
            privilege_set_id = existing_record.id
            print(f"  - Privilege set '{set_info.name}' already exists (ID: {privilege_set_id})")
        else:
            created = await PlatformPrivilegeSetRepository(session).create_platform_privilege_set(
                PlatformPrivilegeSetCreate(name=set_info.name),
            )
            privilege_set_id = created.id
            created_sets += 1
            print(f"  ✓ Created privilege set: {set_info.name}")

        for privilege_code in set_info.privileges:
            existing_mapping = await PlatformPrivilegeSetPrivilegeRepository(
                session
            ).read_by_privilege_set_and_code(privilege_set_id, privilege_code)
            if existing_mapping:
                print(f"    - {privilege_code} already mapped to {set_info.name}")
            else:
                await PlatformPrivilegeSetPrivilegeRepository(
                    session
                ).create_platform_privilege_set_privilege(
                    PlatformPrivilegeSetPrivilegeCreate(
                        privilege_set_id=privilege_set_id,
                        privilege_code=privilege_code,
                    ),
                )
                created_mappings += 1
                print(f"    ✓ Mapped {privilege_code} to {set_info.name}")

    print(
        f"\n  Summary: Created {created_sets} privilege sets, created {created_mappings} mappings"
    )
    return created_sets, created_mappings


async def seed_platform_auth():
    async with get_sessionmaker()() as session:
        await create_platform_privileges(session)
        await create_platform_privilege_sets(session)
        await session.commit()


async def seed_variant_vocabulary():
    print("\nSeeding variant vocabulary...")
    created_types = 0
    created_options = 0

    async with get_sessionmaker()() as session:
        for type_name, options in VARIANT_TYPES.items():
            existing_type = await VariantTypeRepository(session).read_product_option_by_name(
                type_name
            )
            if existing_type:
                type_id = existing_type.id
                print(f"  - Variant type '{type_name}' already exists")
            else:
                created = await VariantTypeRepository(session).create_product_option(
                    ProductOptionCreate(name=type_name)
                )
                type_id = created.id
                created_types += 1
                print(f"  ✓ Created variant type: {type_name}")

            for value in options:
                existing_option = await VariantOptionRepository(
                    session
                ).read_product_option_value_by_option_and_value(type_id, value)
                if existing_option:
                    print(f"    - Option '{value}' already exists")
                else:
                    await VariantOptionRepository(session).create_product_option_value(
                        ProductOptionValueCreate(
                            product_option_id=type_id,
                            value=value,
                        ),
                    )
                    created_options += 1
                    print(f"    ✓ Created option: {value}")

        await session.commit()

    print(f"  Summary: Created {created_types} variant types, {created_options} options")
    return created_types, created_options


async def main():
    print("=" * 60)
    print("Seeding Default Records")
    print("=" * 60)

    try:
        await seed_business_auth()
        await seed_platform_auth()
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
