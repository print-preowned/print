from datetime import datetime
from typing import Literal, Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator
from app.variant.model import VariantWithConfig
from app.utility.model import BaseAppModel

BusinessBookListingStatus = Literal[
    "DRAFT", "ACTIVE", "INACTIVE", "SUSPENDED", "DELETED"
]
SELLER_MUTABLE_LISTING_STATUSES = frozenset({"DRAFT", "ACTIVE", "INACTIVE"})
# DRAFT is only set at create; sellers cannot revert a published listing to DRAFT.
SELLER_LISTING_STATUS_TRANSITIONS: dict[str, frozenset[str]] = {
    "DRAFT": frozenset({"DRAFT", "ACTIVE"}),
    "ACTIVE": frozenset({"ACTIVE", "INACTIVE"}),
    "INACTIVE": frozenset({"INACTIVE", "ACTIVE"}),
}


class BusinessBook(BaseAppModel):
    id: str
    book_id: str
    business_id: str
    synopsis: Optional[str] = None
    image: Optional[str] = None
    status: str
    created_at: datetime
    updated_at: datetime


class BusinessBookCreateRequest(BaseModel):
    book_id: str
    business_id: Optional[str] = None  # Injected by server from token
    synopsis: Optional[str] = None
    image: Optional[str] = None
    status: str = Field(default="DRAFT", exclude=True)


class BusinessBookUpdateRequest(BaseModel):
    book_id: Optional[str] = None
    business_id: Optional[str] = None
    synopsis: Optional[str] = None
    image: Optional[str] = None
    status: Optional[str] = None

    @field_validator("status")
    @classmethod
    def validate_update_status(cls, value: str | None) -> str | None:
        if value is not None and value not in SELLER_MUTABLE_LISTING_STATUSES:
            raise ValueError(
                "Listing status must be one of: DRAFT, ACTIVE, INACTIVE"
            )
        return value

    model_config = ConfigDict(extra="forbid")


class BusinessBookWithBook(BusinessBook):
    """Business book with book title (and image) for list display."""
    book_title: Optional[str] = None
    book_image: Optional[str] = None


class BusinessBookWithVariantSummary(BusinessBookWithBook):
    """Catalog listing with aggregated variant metrics."""
    variant_count: int = 0
    min_price: Optional[float] = None
    total_stock: int = 0


class BusinessBookWithVariants(BusinessBook):
    """Single listing with full variants and resolved config."""
    book_title: Optional[str] = None
    book_image: Optional[str] = None
    variants: list[VariantWithConfig] = []


