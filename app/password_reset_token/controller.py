from fastapi import APIRouter, Depends, Response

from app.password_reset_token.model import (
    PasswordChangeRequest,
    PasswordChangeResponse,
    PasswordResetCompleteRequest,
    PasswordResetRequest,
    PasswordResetValidateResponse,
)
from app.password_reset_token.service import (
    ReadablePasswordResetTokenService,
    WritablePasswordResetTokenService,
)
from app.utility.authorization import TokenPayload, get_token_payload

router = APIRouter(prefix="/password-reset", tags=["password-reset"])


@router.post("/request", status_code=200)
async def request_password_reset(
    request: PasswordResetRequest,
    service: WritablePasswordResetTokenService = Depends(),
) -> dict:
    """
    Request a password reset (public endpoint)

    - User provides email
    - System generates reset token
    - Returns token (should be sent via email)
    """
    return await service.request_password_reset(request)


@router.get("/validate", status_code=200)
async def validate_reset_token(
    token: str,
    service: ReadablePasswordResetTokenService = Depends(),
) -> PasswordResetValidateResponse:
    """
    Validate a password reset token (public endpoint)

    - Checks if token is valid, not expired, and not used
    """
    return await service.validate_reset_token(token)


@router.post("/complete", status_code=200)
async def complete_password_reset(
    complete_request: PasswordResetCompleteRequest,
    service: WritablePasswordResetTokenService = Depends(),
) -> Response:
    """
    Complete password reset (public endpoint)

    - Validates token
    - Updates user password
    - Marks token as used
    """
    return await service.complete_password_reset(complete_request)


@router.post("/change", status_code=200, tags=["client", "platform"])
async def change_password(
    change_request: PasswordChangeRequest,
    token: TokenPayload = Depends(get_token_payload),
    service: WritablePasswordResetTokenService = Depends(),
) -> PasswordChangeResponse:
    """
    Change password (authenticated endpoint)

    - Requires authentication
    - Verifies current password
    - Updates to new password
    - If user status is "NEW", updates to "ACTIVE"
    - Works for both client and platform users
    """
    return await service.change_password(token, change_request)
