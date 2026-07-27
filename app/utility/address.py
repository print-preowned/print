"""Shared address validation for Nigeria-first addresses."""

from __future__ import annotations

import re
from typing import Mapping

from fastapi import HTTPException

DEFAULT_COUNTRY_CODE = "NG"
MAX_USER_ADDRESSES = 5
MAX_BUSINESS_ADDRESSES = 5
FULFILLMENT_TYPE_DELIVERY = "DELIVERY"
FULFILLMENT_TYPE_PICKUP = "PICKUP"

NIGERIAN_STATES: frozenset[str] = frozenset(
    {
        "Abia",
        "Adamawa",
        "Akwa Ibom",
        "Anambra",
        "Bauchi",
        "Bayelsa",
        "Benue",
        "Borno",
        "Cross River",
        "Delta",
        "Ebonyi",
        "Edo",
        "Ekiti",
        "Enugu",
        "FCT",
        "Gombe",
        "Imo",
        "Jigawa",
        "Kaduna",
        "Kano",
        "Katsina",
        "Kebbi",
        "Kogi",
        "Kwara",
        "Lagos",
        "Nasarawa",
        "Niger",
        "Ogun",
        "Ondo",
        "Osun",
        "Oyo",
        "Plateau",
        "Rivers",
        "Sokoto",
        "Taraba",
        "Yobe",
        "Zamfara",
    }
)

_NG_LOCAL_MOBILE_RE = re.compile(r"^0[789]\d{9}$")
_NG_COUNTRY_NO_PLUS_RE = re.compile(r"^234[789]\d{9}$")
_E164_RE = re.compile(r"^\+[1-9]\d{6,14}$")


def normalize_whitespace(value: str | None) -> str | None:
    if value is None:
        return None
    trimmed = value.strip()
    return trimmed or None


def normalize_phone_input(value: str | None) -> str | None:
    normalized = normalize_whitespace(value)
    if normalized is None:
        return None
    return normalized.replace(" ", "").replace("-", "")


def normalize_phone_to_e164(compact: str) -> str:
    if _NG_LOCAL_MOBILE_RE.match(compact):
        return f"+234{compact[1:]}"
    if _NG_COUNTRY_NO_PLUS_RE.match(compact):
        return f"+{compact}"
    if compact.startswith("+"):
        if not _E164_RE.match(compact):
            raise HTTPException(status_code=422, detail="Invalid phone number")
        return compact
    raise HTTPException(
        status_code=422,
        detail="Phone number must use + for international numbers or Nigerian local format (080…)",
    )


def validate_phone_number(value: str | None, *, required: bool = False) -> str | None:
    compact = normalize_phone_input(value)
    if compact is None:
        if required:
            raise HTTPException(status_code=422, detail="Phone number is required")
        return None
    return normalize_phone_to_e164(compact)


def validate_nigeria_address_fields(
    *,
    line1: str,
    line2: str | None = None,
    city: str,
    state: str,
    postal_code: str | None = None,
    country_code: str = DEFAULT_COUNTRY_CODE,
    phone_number: str | None = None,
    require_phone: bool = False,
) -> dict[str, str | None]:
    normalized_line1 = normalize_whitespace(line1)
    normalized_city = normalize_whitespace(city)
    normalized_state = normalize_whitespace(state)
    normalized_country = (normalize_whitespace(country_code) or DEFAULT_COUNTRY_CODE).upper()

    if not normalized_line1:
        raise HTTPException(status_code=422, detail="Address line1 is required")
    if not normalized_city:
        raise HTTPException(status_code=422, detail="City is required")
    if not normalized_state:
        raise HTTPException(status_code=422, detail="State is required")
    if normalized_country != DEFAULT_COUNTRY_CODE:
        raise HTTPException(status_code=422, detail="Only NG addresses are supported currently")
    if normalized_state not in NIGERIAN_STATES:
        raise HTTPException(status_code=422, detail="Invalid Nigerian state")

    return {
        "line1": normalized_line1,
        "line2": normalize_whitespace(line2),
        "city": normalized_city,
        "state": normalized_state,
        "postal_code": normalize_whitespace(postal_code),
        "country_code": normalized_country,
        "phone_number": validate_phone_number(phone_number, required=require_phone),
    }


def apply_address_updates(
    target: Mapping[str, str | None],
    updates: Mapping[str, str | None],
) -> dict[str, str | None]:
    merged = dict(target)
    merged.update({k: v for k, v in updates.items() if v is not None or k in updates})
    return validate_nigeria_address_fields(
        line1=merged.get("line1") or "",
        line2=merged.get("line2"),
        city=merged.get("city") or "",
        state=merged.get("state") or "",
        postal_code=merged.get("postal_code"),
        country_code=merged.get("country_code") or DEFAULT_COUNTRY_CODE,
        phone_number=merged.get("phone_number"),
    )


def fulfillment_snapshot_from_user_address(row) -> dict[str, str | None]:
    """Map a user address row to order fulfillment snapshot columns."""
    return {
        "fulfillment_type": FULFILLMENT_TYPE_DELIVERY,
        "recipient_name": row.recipient_name,
        "address_label": normalize_whitespace(row.label),
        "phone_number": row.phone_number,
        "line1": row.line1,
        "line2": row.line2,
        "city": row.city,
        "state": row.state,
        "postal_code": row.postal_code,
        "country_code": row.country_code,
    }


def fulfillment_snapshot_from_business_address(row) -> dict[str, str | None]:
    """Map a business pickup location row to order fulfillment snapshot columns."""
    return {
        "fulfillment_type": FULFILLMENT_TYPE_PICKUP,
        "recipient_name": "",
        "address_label": normalize_whitespace(row.label),
        "phone_number": row.phone_number,
        "line1": row.line1,
        "line2": row.line2,
        "city": row.city,
        "state": row.state,
        "postal_code": row.postal_code,
        "country_code": row.country_code,
    }
