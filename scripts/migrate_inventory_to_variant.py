"""
Rename legacy MongoDB collections and fields after inventory_item → variant refactor.

Run with: python scripts/migrate_inventory_to_variant.py

Safe to run multiple times — skips steps when new names already exist.
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.utility.database import get_database


async def _rename_collection(db, old: str, new: str) -> None:
    old_names = await db.list_collection_names()
    if new in old_names:
        print(f"  - Collection '{new}' already exists, skipping rename from '{old}'")
        return
    if old not in old_names:
        print(f"  - Collection '{old}' not found, skipping")
        return
    await db[old].rename(new)
    print(f"  ✓ Renamed collection {old} → {new}")


async def _rename_field(db, collection: str, old_field: str, new_field: str) -> None:
    if collection not in await db.list_collection_names():
        return
    result = await db[collection].update_many(
        {old_field: {"$exists": True}},
        {"$rename": {old_field: new_field}},
    )
    if result.modified_count:
        print(f"  ✓ Renamed field {collection}.{old_field} → {new_field} ({result.modified_count} docs)")


async def main():
    print("Migrating inventory_item → variant …")
    db = get_database()

    await _rename_collection(db, "inventory_item", "variant")
    await _rename_collection(db, "item_attribute", "variant_config")
    await _rename_collection(db, "variant_selection", "variant_config")

    await _rename_field(db, "variant_config", "inventory_item_id", "variant_id")
    await _rename_field(db, "order_item", "inventory_item_id", "variant_id")

    if "entity_image" in await db.list_collection_names():
        result = await db["entity_image"].update_many(
            {"entity_name": "INVENTORY_ITEM"},
            {"$set": {"entity_name": "VARIANT"}},
        )
        if result.modified_count:
            print(f"  ✓ Updated entity_image entity_name ({result.modified_count} docs)")

    print("Done.")


if __name__ == "__main__":
    asyncio.run(main())
