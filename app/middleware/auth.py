from fastapi import HTTPException
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from app.utility.authorization import get_token_payload

PUBLIC_EXACT_PATHS = (
    "/user/login",
    "/user/signup",
    "/platform-user/login",
    "/author/read",
    "/book/read",
)

PUBLIC_PATHS_PREFIX = (
    "/docs",
    "/openapi.json",
    "/redoc",
    "/platform-invite/validate",
    "/platform-invite/accept",
    "/platform-invite/reject",
)


def _is_public_path(path: str) -> bool:
    if path in PUBLIC_EXACT_PATHS:
        return True
    return any(path.startswith(prefix) for prefix in PUBLIC_PATHS_PREFIX)


class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        path = request.url.path

        # Skip auth for swagger and openapi
        if path.startswith(("/platform-docs", "/openapi-platform.json")):
            return await call_next(request)

        # Initialize user_data dict in app state if not present
        if not hasattr(request.app.state, "authenticated"):
            request.app.state.authenticated = {}

        if _is_public_path(request.url.path):
            # request.app.state.user = {"user":23}
            response = await call_next(request)
            return response

        # Extract and validate token (following MDC-BE-1: no database access)
        try:
            token_payload = await get_token_payload(request)

            # Store token payload in request state for use in controllers
            request.state.token_payload = token_payload
            request.state.user_id = token_payload.sub

            # For backward compatibility, store user_id in app state
            if not hasattr(request.app.state, "authenticated"):
                request.app.state.authenticated = {}
            request.app.state.authenticated[token_payload.sub] = True

        except HTTPException as e:
            print(f"========>  1: {str(e)}")
            # Return JSONResponse for middleware (can't raise HTTPException in middleware)
            return JSONResponse(status_code=e.status_code, content={"detail": str(e.detail)})
        except Exception as e:
            print(f"========> 2: {str(e)}")
            return JSONResponse(
                status_code=401,
                content={"detail": f"Authentication failed: {str(e)}"},
            )

        token_payload = request.state.token_payload
        if (
            token_payload.ctx == "PLATFORM"
            and token_payload.pwd_chg
            and not path.startswith("/password-reset/change")
        ):
            return JSONResponse(
                status_code=403,
                content={"detail": "Password change required before accessing platform resources"},
            )

        return await call_next(request)
