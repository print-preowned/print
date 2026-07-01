"""
Seed Default Records Script

This script creates default records for:
1. Roles (OWNER role)
2. Privileges (for all modules)
3. Role-Privilege mappings (all privileges mapped to OWNER role)
4. Platform Privileges
5. Platform Privilege Sets
6. Platform Privilege Set-Privilege mappings

Run with: python scripts/seed_defaults.py
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path to import app modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.role.model import RoleCreateRequest, OWNER_ROLE_CODE
from app.role.query import create_query as create_role_query, read_by_code_query as read_role_by_code_query
from app.privilege.model import PrivilegeCreateRequest
from app.privilege.query import create_query as create_privilege_query, read_by_code_query as read_privilege_by_code_query
from app.role_privilege.model import RolePrivilegeCreateRequest
from app.role_privilege.query import create_query as create_role_privilege_query, read_by_role_and_privilege_query
from app.platform_privilege.model import PlatformPrivilegeCreateRequest
from app.platform_privilege.query import create_query as create_platform_privilege_query, read_by_code_query as read_platform_privilege_by_code_query
from app.platform_privilege_set.model import PlatformPrivilegeSetCreateRequest
from app.platform_privilege_set.query import create_query as create_platform_privilege_set_query, read_by_id_query as read_platform_privilege_set_by_id_query
from app.platform_privilege_set_privilege.model import PlatformPrivilegeSetPrivilegeCreateRequest
from app.platform_privilege_set_privilege.query import create_query as create_platform_privilege_set_privilege_query, read_by_privilege_set_and_privilege_query
from app.utility.model import PyObjectId


# Default variant vocabulary for pre-owned books
VARIANT_TYPES = {
    "Condition": ["New", "Like New", "Very Good", "Good", "Acceptable"],
    "Format": ["Hardcover", "Paperback", "Mass Market", "Other"],
}


# Define all modules that need privileges
# Based on the directory structure and authorization rules
MODULES = [
    "BOOK",
    "AUTHOR",
    "GENRE",
    "BOOK_GENRE",
    "BOOK_AUTHOR",
    "BOOK_RATING",
    "BUSINESS",
    "BUSINESS_BOOK",
    "BUSINESS_USER",
    "BUSINESS_RATING",
    "VARIANT",
    "ORDER",
    "ORDER_ITEM",
    "RATING",
    "USER",
    "ROLE",
    "PRIVILEGE",
    "ROLE_PRIVILEGE",
    "VARIANT_TYPE",
    "VARIANT_OPTION",
    "VARIANT_CONFIG",
    "ENTITY_IMAGE",
]

# Special cases: modules that don't have DELETE privilege
MODULES_WITHOUT_DELETE = [
    "AUTHOR",  # MDC-AUTHOR-2: authors_cannot_be_deleted
    "BOOK"
]

# Platform privileges for managing the platform
PLATFORM_PRIVILEGES = [
    {"code": "MANAGE_PLATFORM_USERS", "description": "Manage platform users"},
    {"code": "MANAGE_PLATFORM_PRIVILEGES", "description": "Manage platform privileges"},
    {"code": "MANAGE_PLATFORM_PRIVILEGE_SETS", "description": "Manage platform privilege sets"},
    {"code": "VIEW_PLATFORM_ANALYTICS", "description": "View platform analytics"},
    {"code": "MANAGE_BUSINESSES", "description": "Manage all businesses on the platform"},
    {"code": "MANAGE_USERS", "description": "Manage all users on the platform"},
    {"code": "MANAGE_BOOKS", "description": "Manage all books on the platform"},
    {"code": "MANAGE_AUTHORS", "description": "Manage all authors on the platform"},
    {"code": "VIEW_VARIANTS", "description": "View variants across the platform"},
    {"code": "MANAGE_PRIVILEGES", "description": "Manage all privileges on the platform"},
    {"code": "MANAGE_SYSTEM_SETTINGS", "description": "Manage system-wide settings"},
]

# Platform privilege sets
PLATFORM_PRIVILEGE_SETS = [
    {
        "name": "Super Admin",
        "privileges": [
            "MANAGE_PLATFORM_USERS",
            "MANAGE_PLATFORM_PRIVILEGES",
            "MANAGE_PLATFORM_PRIVILEGE_SETS",
            "VIEW_PLATFORM_ANALYTICS",
            "MANAGE_BUSINESSES",
            "MANAGE_USERS",
            "MANAGE_BOOKS",
            "MANAGE_AUTHORS",
            "VIEW_VARIANTS",
            "MANAGE_PRIVILEGES",
            "MANAGE_SYSTEM_SETTINGS",
        ]
    },
    {
        "name": "Admin",
        "privileges": [
            "MANAGE_PLATFORM_USERS",
            "VIEW_PLATFORM_ANALYTICS",
            "MANAGE_BUSINESSES",
            "MANAGE_USERS",
            "MANAGE_BOOKS",
            "MANAGE_AUTHORS",
            "VIEW_VARIANTS",
            "MANAGE_PRIVILEGES",
        ]
    },
    {
        "name": "Moderator",
        "privileges": [
            "VIEW_PLATFORM_ANALYTICS",  
            "MANAGE_BUSINESSES",
            "MANAGE_USERS",
            "MANAGE_BOOKS",
            "MANAGE_AUTHORS",
            "VIEW_VARIANTS",
        ]
    },
]


async def create_owner_role():
    """Create the OWNER role if it doesn't exist"""
    print("Creating OWNER role...")
    
    existing_role = await read_role_by_code_query(OWNER_ROLE_CODE)
    if existing_role:
        print(f"  ✓ OWNER role already exists (ID: {existing_role.id})")
        return existing_role.id
    
    role_data = RoleCreateRequest(
        name="Owner",
        code=OWNER_ROLE_CODE,
        description="Business owner role with full access to all privileges",
        status="ACTIVE"
    )
    
    role_id = await create_role_query(role_data)
    print(f"  ✓ Created OWNER role (ID: {role_id})")
    return role_id


async def create_privileges_for_module(module_name: str, owner_role_id: PyObjectId):
    """Create standard CRUD privileges for a module and map them to OWNER role"""
    print(f"  Creating privileges for module: {module_name}")
    
    # Standard privilege operations
    operations = [
        ("CREATE", f"Create {module_name.lower()}"),
        ("READ", f"Read {module_name.lower()}"),
        ("UPDATE", f"Update {module_name.lower()}"),
    ]
    
    # Add DELETE if module allows it
    if module_name not in MODULES_WITHOUT_DELETE:
        operations.append(("DELETE", f"Delete {module_name.lower()}"))
    
    created_count = 0
    mapped_count = 0
    
    for operation, name in operations:
        privilege_code = f"{operation}_{module_name}"
        
        # Check if privilege already exists
        existing_privilege = await read_privilege_by_code_query(privilege_code)
        if existing_privilege:
            print(f"    - {privilege_code} already exists")
        else:
            privilege_data = PrivilegeCreateRequest(
                code=privilege_code,
                name=name,
                module_name=module_name,
                status="ACTIVE"
            )
            await create_privilege_query(privilege_data)
            created_count += 1
            print(f"    ✓ Created {privilege_code}")
        
        # Map privilege to OWNER role
        role_id_str = str(owner_role_id)
        existing_mapping = await read_by_role_and_privilege_query(role_id_str, privilege_code)
        if existing_mapping:
            print(f"    - {privilege_code} already mapped to OWNER role")
        else:
            mapping_data = RolePrivilegeCreateRequest(
                role_id=owner_role_id,
                privilege_code=privilege_code,
                status="ACTIVE"
            )
            await create_role_privilege_query(mapping_data)
            mapped_count += 1
            print(f"    ✓ Mapped {privilege_code} to OWNER role")
    

    return created_count, mapped_count


async def create_all_privileges(owner_role_id: PyObjectId):
    """Create privileges for all modules"""
    print("\nCreating privileges for all modules...")
    
    total_created = 0
    total_mapped = 0
    
    for module_name in MODULES:
        created, mapped = await create_privileges_for_module(module_name, owner_role_id)
        total_created += created
        total_mapped += mapped
    
    print(f"\n  Summary: Created {total_created} privileges, mapped {total_mapped} to OWNER role")
    return total_created, total_mapped


async def create_platform_privileges():
    """Create platform privileges"""
    print("\nCreating platform privileges...")
    
    created_count = 0
    
    for priv_info in PLATFORM_PRIVILEGES:
        existing = await read_platform_privilege_by_code_query(priv_info["code"])
        if existing:
            print(f"  - {priv_info['code']} already exists")
        else:
            platform_priv_data = PlatformPrivilegeCreateRequest(
                code=priv_info["code"],
                description=priv_info["description"],
                status="ACTIVE"
            )
            await create_platform_privilege_query(platform_priv_data)
            created_count += 1
            print(f"  ✓ Created {priv_info['code']}")
    
    print(f"  Summary: Created {created_count} platform privileges")
    return created_count


async def create_platform_privilege_sets():
    """Create platform privilege sets and map privileges"""
    print("\nCreating platform privilege sets...")
    
    from app.utility.database import get_database
    from bson import ObjectId
    
    created_sets = 0
    created_mappings = 0
    
    db = get_database()
    collection = db["platform_privilege_set"]
    
    for set_info in PLATFORM_PRIVILEGE_SETS:
        # Check if privilege set already exists by name
        existing_record = await collection.find_one(
            {"name": set_info["name"], "status": {"$ne": "DELETED"}}
        )
        
        if existing_record:
            privilege_set_id = PyObjectId(existing_record["_id"])
            print(f"  - Privilege set '{set_info['name']}' already exists (ID: {privilege_set_id})")
        else:
            set_data = PlatformPrivilegeSetCreateRequest(
                name=set_info["name"],
                status="ACTIVE"
            )
            await create_platform_privilege_set_query(set_data)
            created_sets += 1
            print(f"  ✓ Created privilege set: {set_info['name']}")
            
            # Get the created set ID
            record = await collection.find_one(
                {"name": set_info["name"], "status": {"$ne": "DELETED"}},
                sort=[("created_at", -1)]
            )
            if record:
                privilege_set_id = PyObjectId(record["_id"])
            else:
                print(f"    ⚠ Warning: Could not find created privilege set '{set_info['name']}'")
                continue
        
        # Map privileges to this set
        for privilege_code in set_info["privileges"]:
            existing_mapping = await read_by_privilege_set_and_privilege_query(
                str(privilege_set_id), privilege_code
            )
            if existing_mapping:
                print(f"    - {privilege_code} already mapped to {set_info['name']}")
            else:
                mapping_data = PlatformPrivilegeSetPrivilegeCreateRequest(
                    privilege_set_id=privilege_set_id,
                    privilege_code=privilege_code,
                    status="ACTIVE"
                )
                await create_platform_privilege_set_privilege_query(mapping_data)
                created_mappings += 1
                print(f"    ✓ Mapped {privilege_code} to {set_info['name']}")
    
    print(f"\n  Summary: Created {created_sets} privilege sets, created {created_mappings} mappings")
    return created_sets, created_mappings


async def seed_variant_vocabulary():
    """Seed default Condition and Format variant types and options."""
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

    print(
        f"  Summary: Created {created_types} variant types, {created_options} options"
    )
    return created_types, created_options


async def main():
    """Main function to seed all default records"""
    print("=" * 60)
    print("Seeding Default Records")
    print("=" * 60)
    
    try:
        # 1. Create OWNER role
        owner_role_id = await create_owner_role()
        
        # 2. Create privileges for all modules and map to OWNER role
        await create_all_privileges(owner_role_id)
        
        # 3. Create platform privileges
        await create_platform_privileges()
        
        # 4. Create platform privilege sets and mappings
        await create_platform_privilege_sets()

        # 5. Seed variant vocabulary (Condition, Format)
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
