"""
Authorization utilities following PRINT Authorization & Context Model

Following MDC-BE-2: privilege_based_authorization, fail_closed
Following MDC-BE-1: no database access in middleware
"""

from typing import Literal, Optional, cast

import jwt
from fastapi import HTTPException, Request

from app.utility.redis import get_key
from app.utility.token import decode_token

TokenContext = Literal["CUSTOMER", "BUSINESS", "PLATFORM"]


class TokenPayload:
    """Decoded token payload with proper structure"""

    def __init__(self, payload: dict):
        self.iss = payload.get("iss")
        self.aud = payload.get("aud")
        self.sub: str = cast(str, payload.get("sub"))  # User ID
        self.iat = payload.get("iat")
        self.exp = payload.get("exp")
        self.jti = payload.get("jti")
        ctx_value = payload.get("ctx")
        if ctx_value not in ["CUSTOMER", "BUSINESS", "PLATFORM"]:
            raise ValueError(f"Invalid context: {ctx_value}")
        self.ctx: TokenContext = cast(TokenContext, ctx_value)
        self.business = payload.get("business")  # Only for BUSINESS context
        self.privileges = payload.get("privileges", [])  # For BUSINESS and PLATFORM contexts
        self.pwd_chg = payload.get("pwd_chg") is True


def extract_token_from_request(request: Request) -> str:
    """Extract Bearer token from request headers"""
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing bearer token")

    return auth_header.split(" ", 1)[1].strip()


async def get_token_payload(request: Request) -> TokenPayload:
    """
    Extract and decode token from request

    Following MDC-BE-1: No database access in middleware
    Token validation only - no DB queries
    """
    token = extract_token_from_request(request)

    try:
        # Decode token using utility (validates structure, expiration, audience)
        payload = decode_token(token)

        # Validate required fields
        required_fields = ["iss", "aud", "sub", "iat", "exp", "jti", "ctx"]
        for field in required_fields:
            if field not in payload:
                raise HTTPException(status_code=401, detail=f"Invalid token: missing {field}")

        # Validate context
        if payload["ctx"] not in ["CUSTOMER", "BUSINESS", "PLATFORM"]:
            raise HTTPException(status_code=401, detail="Invalid token: invalid context")

        # Validate BUSINESS token structure
        if payload["ctx"] == "BUSINESS":
            if "business" not in payload:
                raise HTTPException(
                    status_code=401,
                    detail="Invalid token: BUSINESS token missing business field",
                )

            if "privileges" not in payload:
                raise HTTPException(
                    status_code=401,
                    detail="Invalid token: BUSINESS token missing privileges field",
                )

            business = payload["business"]
            if not business.get("id") or "is_owner" not in business:
                raise HTTPException(
                    status_code=401,
                    detail="Invalid token: BUSINESS token missing required fields",
                )

        # Validate PLATFORM token structure
        if payload["ctx"] == "PLATFORM":
            if "business" in payload:
                raise HTTPException(
                    status_code=401,
                    detail="Invalid token: PLATFORM token must not have business field",
                )
            if "privileges" not in payload:
                raise HTTPException(
                    status_code=401,
                    detail="Invalid token: PLATFORM token missing privileges field",
                )

        # Validate CUSTOMER token prohibitions (has_business is allowed for UI)
        if payload["ctx"] == "CUSTOMER":
            if "business" in payload or "privileges" in payload:
                raise HTTPException(
                    status_code=401,
                    detail="Invalid token: CUSTOMER token contains forbidden fields",
                )

        # Check token revocation (jti in Redis)
        # Note: This is a lightweight check, not a DB query
        jti = payload.get("jti")
        if jti:
            revoked = get_key(f"revoked:{jti}")
            if revoked:
                raise HTTPException(status_code=401, detail="Token has been revoked")
        return TokenPayload(payload)

    except ValueError as e:
        # Token decode/validation errors
        raise HTTPException(status_code=401, detail=str(e))
    except jwt.InvalidTokenError as e:
        raise HTTPException(status_code=401, detail=f"Invalid token: {str(e)}")


async def get_optional_token_payload(request: Request) -> TokenPayload | None:
    """Return token payload when Authorization is present; otherwise None."""
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return None
    return await get_token_payload(request)


def _extract_manage_privilege(privilege: str) -> str | None:
    """
    Extract MANAGE_<RESOURCE> privilege from a resource privilege.

    Examples:
        CREATE_BOOK -> MANAGE_BOOKS
        READ_AUTHOR -> MANAGE_AUTHORS
        UPDATE_USER -> MANAGE_USERS

    Returns None if privilege doesn't match the pattern.
    """
    if "_" in privilege:
        parts = privilege.split("_", 1)
        if len(parts) == 2:
            resource = parts[1]
            # Convert to plural and uppercase for MANAGE privilege
            if not resource.endswith("S"):
                resource_plural = resource + "S"
            else:
                resource_plural = resource
            return f"MANAGE_{resource_plural}"
    return None


def require_context(context: TokenContext):
    """
    FastAPI dependency to require specific context

    Usage:
        @router.get("/books")
        async def read_books(token: TokenPayload = Depends(require_context("BUSINESS"))):
            ...
    """

    async def dependency(request: Request) -> TokenPayload:
        token_payload = await get_token_payload(request)

        if token_payload.ctx != context:
            raise HTTPException(
                status_code=403,
                detail=(
                    f"Endpoint requires {context} context, "
                    f"but token has {token_payload.ctx} context"
                ),
            )

        return token_payload

    return dependency


def require_privilege(privilege: str):
    """
    FastAPI dependency to require specific privilege (BUSINESS or PLATFORM context)

    For PLATFORM context: Also allows access if user has MANAGE_<RESOURCE> privilege
    For example: CREATE_BOOK, READ_BOOK, UPDATE_BOOK, DELETE_BOOK -> MANAGE_BOOKS

    Usage:
        @router.post("/books")
        async def create_book(token: TokenPayload = Depends(require_privilege("CREATE_BOOK"))):
            ...
    """

    async def dependency(request: Request) -> TokenPayload:
        token_payload = await get_token_payload(request)

        # Must be BUSINESS or PLATFORM context
        if token_payload.ctx not in ["BUSINESS", "PLATFORM"]:
            raise HTTPException(
                status_code=403,
                detail=f"Privilege '{privilege}' requires BUSINESS or PLATFORM context",
            )

        privileges = token_payload.privileges

        # Check if user has the required privilege
        has_privilege = privilege in privileges

        # For PLATFORM context, also check for MANAGE_<RESOURCE> privilege
        if not has_privilege and token_payload.ctx == "PLATFORM":
            manage_privilege = _extract_manage_privilege(privilege)
            if manage_privilege:
                has_privilege = manage_privilege in privileges

        if not has_privilege:
            raise HTTPException(status_code=403, detail="User unauthorized to access this resource")

        return token_payload

    return dependency


def require_owner():
    """
    FastAPI dependency to require owner status (BUSINESS context only)

    Usage:
        @router.delete("/books/{id}")
        async def delete_book(token: TokenPayload = Depends(require_owner())):
            ...
    """

    async def dependency(request: Request) -> TokenPayload:
        token_payload = await get_token_payload(request)

        # Must be BUSINESS context
        if token_payload.ctx != "BUSINESS":
            raise HTTPException(status_code=403, detail="Owner actions require BUSINESS context")

        # Check ownership
        if not token_payload.business.get("is_owner", False) if token_payload.business else False:
            raise HTTPException(status_code=403, detail="This action requires owner privileges")

        return token_payload

    return dependency


def require_privilege_and_owner(privilege: str):
    """
    FastAPI dependency to require both privilege AND owner status (BUSINESS context)
    OR MANAGE_<RESOURCE> privilege (PLATFORM context)

    Usage:
        @router.delete("/books/{id}")
        async def delete_book(
            token: TokenPayload = Depends(require_privilege_and_owner("DELETE_BOOK"))
        ):
            ...
    """

    async def dependency(request: Request) -> TokenPayload:
        token_payload = await get_token_payload(request)

        # Must be BUSINESS or PLATFORM context
        if token_payload.ctx not in ["BUSINESS", "PLATFORM"]:
            raise HTTPException(
                status_code=403,
                detail=f"Privilege '{privilege}' requires BUSINESS or PLATFORM context",
            )

        if token_payload.ctx == "PLATFORM":
            # For PLATFORM context, check for MANAGE_<RESOURCE> privilege
            privileges = token_payload.privileges

            manage_privilege = _extract_manage_privilege(privilege)
            if manage_privilege and manage_privilege in privileges:
                return token_payload

            raise HTTPException(status_code=403, detail="User unauthorized to access this resource")
        else:
            # BUSINESS context: require privilege AND owner status
            if privilege not in token_payload.privileges:
                raise HTTPException(
                    status_code=403, detail=f"Insufficient privileges: '{privilege}' required"
                )

            # Check ownership
            is_owner = (
                token_payload.business.get("is_owner", False) if token_payload.business else False
            )
            if not is_owner:
                raise HTTPException(status_code=403, detail="This action requires owner privileges")

        return token_payload

    return dependency


def get_business_id(token_payload: TokenPayload) -> Optional[str]:
    """Get business ID from token payload (BUSINESS context only)"""
    if token_payload.ctx == "BUSINESS" and token_payload.business:
        return token_payload.business.get("id")
    return None
