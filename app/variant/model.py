from datetime import datetime
from typing import Optional

from pydantic import ConfigDict

from app.utility.model import BaseAppModel


class Variant(BaseAppModel):
    id: str
    business_book_id: str
    description: Optional[str] = None
    stock: int
    price: float
    currency: str
    discount: Optional[float] = None
    sku: Optional[str] = None
    image: Optional[str] = None
    status: str
    created_at: datetime
    updated_at: datetime


class VariantCreateRequest(BaseAppModel):
    """Create sellable variant with option config (one per variant type)."""

    variant_option_ids: list[str]
    description: Optional[str] = None
    stock: int
    price: float
    discount: Optional[float] = None
    sku: Optional[str] = None
    image: Optional[str] = None


class VariantUpdateRequest(BaseAppModel):
    """Mutable fields only — business_book_id and config are set at create."""

    description: Optional[str] = None
    stock: Optional[int] = None
    price: Optional[float] = None
    currency: Optional[str] = None
    discount: Optional[float] = None
    sku: Optional[str] = None
    image: Optional[str] = None

    model_config = ConfigDict(extra="forbid")


class ResolvedConfig(BaseAppModel):
    """Resolved variant type + option for display."""

    variant_type_id: str
    variant_type_name: str
    variant_option_id: str
    variant_option_value: str


class VariantWithConfig(Variant):
    config: list[ResolvedConfig] = []


class PublicCatalogVariant(BaseAppModel):
    """Customer-facing sellable variant with joined book and business data."""

    id: str
    business_book_id: str
    book_id: str
    book_title: str
    book_image: Optional[str] = None
    business_id: str
    business_name: str
    price: float
    currency: str
    discount: Optional[float] = None
    stock: int
    image: Optional[str] = None
    config: list[ResolvedConfig] = []
