# Server-Side Privilege-Based Authorization

## Overview

This document describes the server-side authorization implementation following the PRINT Authorization & Context Model (MDC-BE-2: `privilege_based_authorization`, `fail_closed`).

## Architecture

### 1. Authorization Utilities (`app/utility/authorization.py`)

Provides FastAPI dependencies for privilege-based authorization:

- **`require_context(context)`**: Requires specific context (CUSTOMER or BUSINESS)
- **`require_privilege(privilege)`**: Requires specific privilege (BUSINESS context only)
- **`require_owner()`**: Requires owner status (BUSINESS context only)
- **`require_privilege_and_owner(privilege)`**: Requires both privilege AND owner status

### 2. Token Validation (`get_token_payload`)

Following MDC-BE-1: **No database access in middleware**

- Validates token structure (required fields: `iss`, `aud`, `sub`, `iat`, `exp`, `jti`, `ctx`)
- Validates context (CUSTOMER or BUSINESS)
- Validates BUSINESS token structure (privileges, business.id, business.is_owner)
- Checks token revocation (jti in Redis - lightweight, not DB query)
- Returns `TokenPayload` object with decoded token data

### 3. Middleware (`app/middleware/auth.py`)

- Extracts and validates tokens for all protected routes
- Stores token payload in `request.state.token_payload` for use in controllers
- Follows MDC-BE-1: No database access, only token validation

## Implementation Examples

### Books Controller

```python
from app.utility.authorization import require_privilege, require_privilege_and_owner, TokenPayload
from fastapi import Depends

@router.post("/create")
async def create(
    payload: BookCreateRequest,
    token: TokenPayload = Depends(require_privilege("CREATE_BOOK"))
) -> Response:
    """Requires BUSINESS context and CREATE_BOOK privilege"""
    return await create_service(payload)

@router.delete("/delete/{id}")
async def delete(
    id: str,
    token: TokenPayload = Depends(require_privilege_and_owner("DELETE_BOOK"))
) -> Response:
    """Requires BUSINESS context, DELETE_BOOK privilege, AND owner status"""
    return await delete_service(id)
```

### Authors Controller

```python
@router.post("/create")
async def create(
    payload: AuthorCreateRequest,
    token: TokenPayload = Depends(require_privilege("CREATE_AUTHOR"))
) -> Response:
    """Requires BUSINESS context and CREATE_AUTHOR privilege"""
    return await create_service(payload)

# Following MDC-AUTHOR-2: authors_cannot_be_deleted
# No delete endpoint for authors
```

## Security Principles

### 1. Fail-Closed (MDC-BE-2)

- **Default: Deny** - If authority is not explicitly present in the token, it must be treated as denied
- All authorization checks raise `HTTPException(403)` if requirements are not met
- No implicit permissions or role-based inference

### 2. Privilege-Based (MDC-BE-2)

- Authorization is based on **materialized privileges** in the token
- No database queries to check permissions
- Privileges are resolved at token generation time
- Token contains all necessary authorization information

### 3. No Database Access in Middleware (MDC-BE-1)

- Middleware only validates token structure
- No role lookups, no privilege queries, no user checks
- Token is the single source of truth for authorization

## Authorization Flow

```
1. Request arrives with Bearer token
   ↓
2. AuthMiddleware extracts token
   ↓
3. get_token_payload() validates:
   - Token structure (iss, aud, sub, iat, exp, jti, ctx)
   - Context (CUSTOMER or BUSINESS)
   - BUSINESS token structure (privileges, business.id, business.is_owner)
   - Token revocation (jti check)
   ↓
4. TokenPayload stored in request.state
   ↓
5. Controller endpoint dependency checks:
   - require_privilege("CREATE_BOOK") → Checks privilege in token
   - require_owner() → Checks is_owner in token
   - require_privilege_and_owner("DELETE_BOOK") → Checks both
   ↓
6. If authorized: Execute controller logic
   If not authorized: HTTPException(403)
```

## Error Responses

### 401 Unauthorized
- Missing bearer token
- Invalid token structure
- Token expired
- Token revoked

### 403 Forbidden
- Wrong context (e.g., CUSTOMER token on BUSINESS endpoint)
- Missing privilege
- Not owner (when owner required)

## Compliance with Rules

### ✅ MDC-BE-1: Backend Middleware Prohibitions
- ✅ No database access in middleware
- ✅ No role-based checks
- ✅ No route context inference

### ✅ MDC-BE-2: Backend Middleware Requirements
- ✅ Privilege-based authorization
- ✅ Fail-closed (default deny)

### ✅ MDC-BOOK-2: Deleting Book Requires Owner
- `DELETE /book/delete/{id}` uses `require_privilege_and_owner("DELETE_BOOK")`

### ✅ MDC-AUTHOR-2: Authors Cannot Be Deleted
- No delete endpoint for authors

## Testing Authorization

### Test Scenarios

1. **Missing Token**: Should return 401
2. **Invalid Token**: Should return 401
3. **CUSTOMER Token on BUSINESS Endpoint**: Should return 403
4. **Missing Privilege**: Should return 403
5. **Not Owner (Owner Required)**: Should return 403
6. **Valid Token with Privilege**: Should succeed

### Example Test

```python
def test_create_book_requires_privilege():
    # Token without CREATE_BOOK privilege
    response = client.post("/book/create", headers={"Authorization": "Bearer invalid_token"})
    assert response.status_code == 403
    assert "CREATE_BOOK" in response.json()["detail"]
```

## Future Enhancements

1. **Business Scope Validation**: Check that entity belongs to business (for business-scoped entities)
2. **Public Endpoints**: Separate public read endpoints (READ_PUBLIC_BOOK for CUSTOMER context)
3. **Token Refresh**: Implement token refresh mechanism
4. **Audit Logging**: Log authorization decisions for audit purposes

