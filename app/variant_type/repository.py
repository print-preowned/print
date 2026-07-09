from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import Select, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.variant_type.orm import ProductOptionOrm
from app.variant_type.schemas import ProductOptionCreate, ProductOptionUpdate


class VariantTypeRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create_product_option(self, payload: ProductOptionCreate) -> ProductOptionOrm:
        row = ProductOptionOrm(**payload.model_dump())
        self._session.add(row)
        await self._session.flush()
        return row

    async def update_product_option(
        self, product_option_id: uuid.UUID, payload: ProductOptionUpdate
    ) -> ProductOptionOrm | None:
        row = await self.read_product_option_by_id(product_option_id)
        if row is None:
            return None
        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(row, field, value)
        await self._session.flush()
        return row

    async def soft_delete_product_option(self, product_option_id: uuid.UUID) -> bool:
        deleted_id = await self._session.scalar(
            update(ProductOptionOrm)
            .where(ProductOptionOrm.id == product_option_id, ProductOptionOrm.deleted_at.is_(None))
            .values(deleted_at=datetime.now(UTC), status="DELETED")
            .returning(ProductOptionOrm.id)
        )
        return deleted_id is not None

    async def read_product_option_by_id(
        self, product_option_id: uuid.UUID
    ) -> ProductOptionOrm | None:
        return await self._session.scalar(
            select(ProductOptionOrm).where(
                ProductOptionOrm.id == product_option_id, ProductOptionOrm.deleted_at.is_(None)
            )
        )

    async def read_product_option_by_name(self, name: str) -> ProductOptionOrm | None:
        return await self._session.scalar(
            select(ProductOptionOrm).where(
                ProductOptionOrm.name == name, ProductOptionOrm.deleted_at.is_(None)
            )
        )

    async def count_product_options(self) -> int:
        total = await self._session.scalar(
            select(func.count())
            .select_from(ProductOptionOrm)
            .where(ProductOptionOrm.deleted_at.is_(None))
        )
        return int(total or 0)

    async def list_product_options(self, *, offset: int, limit: int) -> list[ProductOptionOrm]:
        statement: Select[tuple[ProductOptionOrm]] = (
            select(ProductOptionOrm)
            .where(ProductOptionOrm.deleted_at.is_(None))
            .order_by(ProductOptionOrm.name)
            .offset(offset)
            .limit(limit)
        )
        result = await self._session.scalars(statement)
        return list(result)
