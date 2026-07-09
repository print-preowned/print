from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import Select, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.variant_option.orm import ProductOptionValueOrm
from app.variant_option.schemas import ProductOptionValueCreate, ProductOptionValueUpdate


class VariantOptionRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create_product_option_value(
        self, payload: ProductOptionValueCreate
    ) -> ProductOptionValueOrm:
        row = ProductOptionValueOrm(**payload.model_dump())
        self._session.add(row)
        await self._session.flush()
        return row

    async def update_product_option_value(
        self, product_option_value_id: uuid.UUID, payload: ProductOptionValueUpdate
    ) -> ProductOptionValueOrm | None:
        row = await self.read_product_option_value_by_id(product_option_value_id)
        if row is None:
            return None
        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(row, field, value)
        await self._session.flush()
        return row

    async def soft_delete_product_option_value(self, product_option_value_id: uuid.UUID) -> bool:
        deleted_id = await self._session.scalar(
            update(ProductOptionValueOrm)
            .where(
                ProductOptionValueOrm.id == product_option_value_id,
                ProductOptionValueOrm.deleted_at.is_(None),
            )
            .values(deleted_at=datetime.now(UTC), status="DELETED")
            .returning(ProductOptionValueOrm.id)
        )
        return deleted_id is not None

    async def read_product_option_value_by_id(
        self, product_option_value_id: uuid.UUID
    ) -> ProductOptionValueOrm | None:
        return await self._session.scalar(
            select(ProductOptionValueOrm).where(
                ProductOptionValueOrm.id == product_option_value_id,
                ProductOptionValueOrm.deleted_at.is_(None),
            )
        )

    async def read_product_option_value_by_option_and_value(
        self, product_option_id: uuid.UUID, value: str
    ) -> ProductOptionValueOrm | None:
        return await self._session.scalar(
            select(ProductOptionValueOrm).where(
                ProductOptionValueOrm.product_option_id == product_option_id,
                ProductOptionValueOrm.value == value,
                ProductOptionValueOrm.deleted_at.is_(None),
            )
        )

    async def count_product_option_values(
        self, *, product_option_id: uuid.UUID | None = None
    ) -> int:
        statement = (
            select(func.count())
            .select_from(ProductOptionValueOrm)
            .where(ProductOptionValueOrm.deleted_at.is_(None))
        )
        if product_option_id is not None:
            statement = statement.where(
                ProductOptionValueOrm.product_option_id == product_option_id
            )
        total = await self._session.scalar(statement)
        return int(total or 0)

    async def list_product_option_values(
        self, *, offset: int, limit: int, product_option_id: uuid.UUID | None = None
    ) -> list[ProductOptionValueOrm]:
        statement: Select[tuple[ProductOptionValueOrm]] = (
            select(ProductOptionValueOrm)
            .where(ProductOptionValueOrm.deleted_at.is_(None))
            .order_by(ProductOptionValueOrm.value)
            .offset(offset)
            .limit(limit)
        )
        if product_option_id is not None:
            statement = statement.where(
                ProductOptionValueOrm.product_option_id == product_option_id
            )
        result = await self._session.scalars(statement)
        return list(result)
