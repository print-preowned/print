"""
Token generation utility following PRINT Authorization & Context Model

Token structure requirements:
- Required base fields: iss, aud, sub, iat, exp, jti, ctx
- Context: CUSTOMER or BUSINESS
- BUSINESS tokens require: privileges, business.id, business.is_owner
"""

import uuid
from datetime import datetime, timedelta, timezone
from typing import Literal

import jwt

from app.user.schemas import UserRead
from app.utility.config import get_settings

JWT_ALGORITHM = "HS256"
TOKEN_ISSUER = "print-api"
TOKEN_AUDIENCE = "print-web"
TOKEN_TTL_MINUTES = 60 * 24  # 24 hours as per rules

TokenContext = Literal["CUSTOMER", "BUSINESS", "PLATFORM"]


def generate_jti() -> str:
    """Generate a unique JWT ID (jti)"""
    return str(uuid.uuid4())


def create_customer_token(user: UserRead, has_business: bool = False) -> str:
    """
    Create a CUSTOMER context token

    has_business: True if the user has a linked business (can switch to BUSINESS context).
    Set at login/context-switch so the client can show "Switch to Business" without a round trip.

    Following MDC-TOKEN-C-1: Customer tokens must NOT have:
    - business (object)
    - privileges
    - role
    """
    now = datetime.now(timezone.utc)
    exp = now + timedelta(minutes=TOKEN_TTL_MINUTES)

    payload = {
        "iss": TOKEN_ISSUER,
        "aud": TOKEN_AUDIENCE,
        "sub": str(user.id),
        "iat": int(now.timestamp()),
        "exp": int(exp.timestamp()),
        "jti": generate_jti(),
        "ctx": "CUSTOMER",
        "has_business": has_business,
        # Customer tokens must NOT include: business, privileges, role
    }

    return jwt.encode(payload, get_settings().jwt_secret, algorithm=JWT_ALGORITHM)


def create_business_token(
    user_id: str,
    business_id: str,
    role_id: str,
    role_name: str,
    is_system_role: bool,
    is_owner: bool,
    privileges: list[str],
) -> str:
    """
    Create a BUSINESS context token

    Following MDC-TOKEN-B-1: Business tokens must have:
    - privileges (top-level, materialized)
    - business.id
    - business.is_owner
    - business.role (id, name, is_system)

    Following MDC-TOKEN-B-2: Privileges must be materialized at top level
    """
    now = datetime.now(timezone.utc)
    exp = now + timedelta(minutes=TOKEN_TTL_MINUTES)

    payload = {
        "iss": TOKEN_ISSUER,
        "aud": TOKEN_AUDIENCE,
        "sub": user_id,
        "iat": int(now.timestamp()),
        "exp": int(exp.timestamp()),
        "jti": generate_jti(),
        "ctx": "BUSINESS",
        "privileges": privileges,
        "business": {
            "id": business_id,
            "role": {
                "id": role_id,
                "name": role_name,
                "is_system": is_system_role,
            },
            "is_owner": is_owner,
        },
    }

    return jwt.encode(payload, get_settings().jwt_secret, algorithm=JWT_ALGORITHM)


def create_platform_token(
    user: UserRead,
    privileges: list[str],
    *,
    password_change_required: bool = False,
) -> str:
    """
    Create a PLATFORM context token

    Following MDC-PLATFORM-2: Platform context has no business scope
    Platform tokens contain privileges but no business information
    """
    now = datetime.now(timezone.utc)
    exp = now + timedelta(minutes=TOKEN_TTL_MINUTES)

    payload = {
        "iss": TOKEN_ISSUER,
        "aud": TOKEN_AUDIENCE,
        "sub": str(user.id),
        "iat": int(now.timestamp()),
        "exp": int(exp.timestamp()),
        "jti": generate_jti(),
        "ctx": "PLATFORM",
        "privileges": privileges,  # Materialized privileges for platform operations
        # Platform tokens must NOT include: business
    }
    if password_change_required:
        payload["pwd_chg"] = True

    return jwt.encode(payload, get_settings().jwt_secret, algorithm=JWT_ALGORITHM)


def decode_token(token: str) -> dict:
    """Decode and validate a JWT token"""
    try:
        payload = jwt.decode(
            token,
            get_settings().jwt_secret,
            algorithms=[JWT_ALGORITHM],
            audience=TOKEN_AUDIENCE,
        )
        return payload
    except jwt.ExpiredSignatureError:
        raise ValueError("Token has expired")
    except jwt.InvalidTokenError as e:
        raise ValueError(f"Invalid token: {str(e)}")
