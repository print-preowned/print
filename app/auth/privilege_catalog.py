"""
Canonical business and platform privilege catalog.

Design:
- Business privileges are generated from CRUD per resource module.
- Lifecycle actions (refund, moderate, status change) do NOT get separate codes.
  Pair CRUD + context (+ owner when required) at the route instead:
    - order status change  -> require_privilege(UPDATE_ORDER)
    - order refund           -> require_privilege_and_owner(UPDATE_ORDER)
    - rating moderation      -> require_privilege(UPDATE_RATING)
- Customer public catalog uses GET /variants with context-implicit READ_PUBLIC_VARIANTS.
  Privileges and paths use VARIANT (sellable SKU). "Inventory" is UI-only.
- Platform admin uses MANAGE_* umbrella privileges (manual catalog section).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final


@dataclass(frozen=True, slots=True)
class PrivilegeDef:
    code: str
    name: str
    module: str
    owner_default: bool = True
    platform_only: bool = False


@dataclass(frozen=True, slots=True)
class CrudResourceDef:
    resource: str
    module: str
    include_delete: bool = True
    include_update: bool = True


@dataclass(frozen=True, slots=True)
class PlatformPrivilegeDef:
    code: str
    description: str


@dataclass(frozen=True, slots=True)
class PlatformPrivilegeSetDef:
    name: str
    privileges: tuple[str, ...]


CRUD_OPERATIONS: Final[tuple[str, ...]] = ("CREATE", "READ", "UPDATE", "DELETE")

# Resources with standard CRUD business privileges.
BUSINESS_CRUD_RESOURCES: Final[tuple[CrudResourceDef, ...]] = (
    CrudResourceDef("BOOK", "BOOK", include_delete=True),
    CrudResourceDef("AUTHOR", "AUTHOR", include_delete=False),
    CrudResourceDef("GENRE", "GENRE"),
    CrudResourceDef("BOOK_GENRE", "BOOK_GENRE"),
    CrudResourceDef("BOOK_AUTHOR", "BOOK_AUTHOR"),
    CrudResourceDef("BOOK_RATING", "BOOK_RATING"),
    CrudResourceDef("BUSINESS", "BUSINESS"),
    CrudResourceDef("BUSINESS_BOOK", "BUSINESS_BOOK"),
    CrudResourceDef("BUSINESS_USER", "BUSINESS_USER"),
    CrudResourceDef("BUSINESS_RATING", "BUSINESS_RATING"),
    CrudResourceDef("ORDER", "ORDER"),
    CrudResourceDef("ORDER_ITEM", "ORDER_ITEM"),
    CrudResourceDef("RATING", "RATING"),
    CrudResourceDef("USER", "USER"),
    CrudResourceDef("ROLE", "ROLE"),
    CrudResourceDef("PRIVILEGE", "PRIVILEGE"),
    CrudResourceDef("ROLE_PRIVILEGE", "ROLE_PRIVILEGE", include_update=False),
    CrudResourceDef("VARIANT", "VARIANT"),
    CrudResourceDef("VARIANT_TYPE", "VARIANT_TYPE"),
    CrudResourceDef("VARIANT_OPTION", "VARIANT_OPTION"),
    CrudResourceDef("VARIANT_CONFIG", "VARIANT_CONFIG"),
)

PLATFORM_PRIVILEGES: Final[tuple[PlatformPrivilegeDef, ...]] = (
    PlatformPrivilegeDef("MANAGE_PLATFORM_USERS", "Manage platform users"),
    PlatformPrivilegeDef("MANAGE_PLATFORM_PRIVILEGES", "Manage platform privileges"),
    PlatformPrivilegeDef("MANAGE_PLATFORM_PRIVILEGE_SETS", "Manage platform privilege sets"),
    PlatformPrivilegeDef("VIEW_PLATFORM_ANALYTICS", "View platform analytics"),
    PlatformPrivilegeDef("MANAGE_BUSINESSES", "Manage all businesses on the platform"),
    PlatformPrivilegeDef("MANAGE_USERS", "Manage all users on the platform"),
    PlatformPrivilegeDef("MANAGE_BOOKS", "Manage all books on the platform"),
    PlatformPrivilegeDef("MANAGE_AUTHORS", "Manage all authors on the platform"),
    PlatformPrivilegeDef("READ_VARIANT", "Read variants across the platform"),
    PlatformPrivilegeDef("MANAGE_PRIVILEGES", "Manage all privileges on the platform"),
    PlatformPrivilegeDef("MANAGE_SYSTEM_SETTINGS", "Manage system-wide settings"),
)

PLATFORM_PRIVILEGE_SETS: Final[tuple[PlatformPrivilegeSetDef, ...]] = (
    PlatformPrivilegeSetDef(
        "Super Admin",
        (
            "MANAGE_PLATFORM_USERS",
            "MANAGE_PLATFORM_PRIVILEGES",
            "MANAGE_PLATFORM_PRIVILEGE_SETS",
            "VIEW_PLATFORM_ANALYTICS",
            "MANAGE_BUSINESSES",
            "MANAGE_USERS",
            "MANAGE_BOOKS",
            "MANAGE_AUTHORS",
            "READ_VARIANT",
            "MANAGE_PRIVILEGES",
            "MANAGE_SYSTEM_SETTINGS",
        ),
    ),
    PlatformPrivilegeSetDef(
        "Admin",
        (
            "MANAGE_PLATFORM_USERS",
            "VIEW_PLATFORM_ANALYTICS",
            "MANAGE_BUSINESSES",
            "MANAGE_USERS",
            "MANAGE_BOOKS",
            "MANAGE_AUTHORS",
            "READ_VARIANT",
            "MANAGE_PRIVILEGES",
        ),
    ),
    PlatformPrivilegeSetDef(
        "Moderator",
        (
            "VIEW_PLATFORM_ANALYTICS",
            "MANAGE_BUSINESSES",
            "MANAGE_USERS",
            "MANAGE_BOOKS",
            "MANAGE_AUTHORS",
            "READ_VARIANT",
        ),
    ),
)

# Retired privilege codes — must not appear in route dependencies.
DEPRECATED_PRIVILEGE_CODES: Final[frozenset[str]] = frozenset(
    {
        "VIEW_VARIANTS",
        "REFUND_ORDER",
        "UPDATE_ORDER_STATUS",
        "MODERATE_RATING",
        "READ_INVENTORY",
        "CREATE_INVENTORY",
        "UPDATE_INVENTORY",
        "DELETE_INVENTORY",
        "UPDATE_ROLE_PRIVILEGE",
    }
)


def crud_privilege_defs(resource: CrudResourceDef) -> list[PrivilegeDef]:
    operations = list(CRUD_OPERATIONS)
    if not resource.include_update:
        operations.remove("UPDATE")
    if not resource.include_delete:
        operations.remove("DELETE")
    return [
        PrivilegeDef(
            code=f"{op}_{resource.resource}",
            name=f"{op.title()} {resource.resource.lower().replace('_', ' ')}",
            module=resource.module,
        )
        for op in operations
    ]


def business_privilege_defs() -> list[PrivilegeDef]:
    defs: list[PrivilegeDef] = []
    for resource in BUSINESS_CRUD_RESOURCES:
        defs.extend(crud_privilege_defs(resource))
    return defs


def all_business_privilege_codes() -> frozenset[str]:
    return frozenset(p.code for p in business_privilege_defs())


def all_platform_privilege_codes() -> frozenset[str]:
    return frozenset(p.code for p in PLATFORM_PRIVILEGES)


def all_catalog_privilege_codes() -> frozenset[str]:
    return all_business_privilege_codes() | all_platform_privilege_codes()


def owner_default_privilege_codes() -> frozenset[str]:
    return frozenset(p.code for p in business_privilege_defs() if p.owner_default)


class Privilege:
    """Stable privilege code constants for route dependencies."""

    # Book
    CREATE_BOOK: Final = "CREATE_BOOK"
    READ_BOOK: Final = "READ_BOOK"
    UPDATE_BOOK: Final = "UPDATE_BOOK"
    DELETE_BOOK: Final = "DELETE_BOOK"

    # Author
    CREATE_AUTHOR: Final = "CREATE_AUTHOR"
    READ_AUTHOR: Final = "READ_AUTHOR"
    UPDATE_AUTHOR: Final = "UPDATE_AUTHOR"

    # Variant (sellable SKU; public catalog at GET /variants)
    READ_VARIANT: Final = "READ_VARIANT"
    CREATE_VARIANT: Final = "CREATE_VARIANT"
    UPDATE_VARIANT: Final = "UPDATE_VARIANT"
    DELETE_VARIANT: Final = "DELETE_VARIANT"

    # Orders — refund/status use UPDATE_ORDER + owner where required
    READ_ORDER: Final = "READ_ORDER"
    UPDATE_ORDER: Final = "UPDATE_ORDER"

    # Ratings — moderation uses UPDATE_RATING
    READ_RATING: Final = "READ_RATING"
    UPDATE_RATING: Final = "UPDATE_RATING"

    # Platform
    MANAGE_PLATFORM_USERS: Final = "MANAGE_PLATFORM_USERS"
    MANAGE_PLATFORM_PRIVILEGES: Final = "MANAGE_PLATFORM_PRIVILEGES"
    MANAGE_PLATFORM_PRIVILEGE_SETS: Final = "MANAGE_PLATFORM_PRIVILEGE_SETS"
