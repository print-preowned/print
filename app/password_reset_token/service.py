from datetime import datetime, timezone, timedelta
from fastapi import HTTPException, Response
from pwdlib import PasswordHash
import secrets
from app.password_reset_token.model import (
    PasswordChangeRequest,
    PasswordResetRequest,
    PasswordResetValidateResponse,
    PasswordResetCompleteRequest,
)
from app.password_reset_token.query import (
    create_query,
    read_by_token_hash_query,
    mark_as_used_query,
    hash_token,
)
from app.user.query import read_by_email_query, update_query
from app.user.model import UserUpdateRequest


def generate_reset_token() -> str:
    """Generate a random token for password reset"""
    return secrets.token_urlsafe(32)  # 32 bytes = 43 characters URL-safe


async def request_password_reset_service(request: PasswordResetRequest) -> dict:
    """
    Request a password reset
    
    - Find user by email
    - Generate random token
    - Store hash in password_reset_token
    - Return raw token (should be sent via email)
    """
    # Find user by email
    user = await read_by_email_query(request.email)
    if not user:
        # Don't reveal if user exists or not (security best practice)
        # Return success even if user doesn't exist
        return {
            "message": "If an account with that email exists, a password reset link has been sent."
        }
    
    # Generate random token
    raw_token = generate_reset_token()
    token_hash = hash_token(raw_token)
    
    # Calculate expiration (1 hour)
    expires_at = datetime.now(timezone.utc) + timedelta(hours=1)
    
    # Create reset token with hashed token
    token_id = await create_query(
        user.id,
        token_hash,
        expires_at
    )
    
    # TODO: Send raw token via email
    # For now, return it in the response (should be removed in production)
    return {
        "message": "If an account with that email exists, a password reset link has been sent.",
        "token": raw_token,  # Only returned for development - should be sent via email
        "expires_at": expires_at.isoformat(),
    }


async def validate_reset_token_service(token: str) -> PasswordResetValidateResponse:
    """
    Validate a password reset token
    
    - Hash token
    - Find token by hash
    - Ensure not expired
    - Ensure not used
    """
    # Hash the token
    token_hash = hash_token(token)
    
    # Find token by hash
    reset_token = await read_by_token_hash_query(token_hash)
    
    if not reset_token:
        return PasswordResetValidateResponse(
            valid=False,
            message="Invalid or expired reset token"
        )
    
    # Check if already used
    if reset_token.used:
        return PasswordResetValidateResponse(
            valid=False,
            message="This reset token has already been used"
        )
    
    # Check expiration
    if reset_token.expires_at < datetime.now(timezone.utc):
        return PasswordResetValidateResponse(
            valid=False,
            message="This reset token has expired"
        )
    
    return PasswordResetValidateResponse(
        valid=True,
        message="Token is valid"
    )


async def complete_password_reset_service(complete_request: PasswordResetCompleteRequest) -> Response:
    """
    Complete password reset
    
    - Validate token
    - Update user password
    - Mark token as used
    """
    # Validate token
    validation = await validate_reset_token_service(complete_request.token)
    if not validation.valid:
        raise HTTPException(
            status_code=400,
            detail=validation.message or "Invalid or expired reset token"
        )
    
    # Get the token record
    token_hash = hash_token(complete_request.token)
    reset_token = await read_by_token_hash_query(token_hash)
    if not reset_token:
        raise HTTPException(status_code=400, detail="Invalid reset token")
    
    # Hash new password
    password_hash = PasswordHash.recommended()
    hashed_password = password_hash.hash(complete_request.new_password)
    
    # Update user password
    update_data = UserUpdateRequest(password=hashed_password)
    await update_query(str(reset_token.user_id), update_data)
    
    # Mark token as used
    await mark_as_used_query(str(reset_token.id))
    
    return Response(status_code=200)


async def change_password_service(user_id: str, change_request: PasswordChangeRequest):
    """
    Change password (authenticated user)
    
    - Verify current password
    - Update to new password
    """
    from app.user.query import read_by_id_query
    from app.user.model import User
    from app.platform_user.query import read_by_user_id_query as read_platform_user_by_user_id_query
    from app.platform_privilege_set_privilege.query import read_by_privilege_set_id_query
    from app.utility.token import create_platform_token
    from app.password_reset_token.model import PasswordChangeResponse
    
    # Get user
    user = await read_by_id_query(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Verify current password
    password_hash = PasswordHash.recommended()
    is_valid = password_hash.verify(change_request.current_password, user.password)
    if not is_valid:
        raise HTTPException(status_code=403, detail="Current password is incorrect")
    
    was_new = user.status == "NEW"

    # Hash new password
    hashed_password = password_hash.hash(change_request.new_password)
    
    # Update user password
    update_data = UserUpdateRequest(password=hashed_password)
    await update_query(user_id, update_data)
    
    # If user status is "NEW", update to "ACTIVE" (password change completed)
    if was_new:
        await update_query(user_id, UserUpdateRequest(status="ACTIVE"))

    new_token: str | None = None
    if was_new:
        platform_user = await read_platform_user_by_user_id_query(user_id)
        if platform_user:
            privilege_mappings = await read_by_privilege_set_id_query(
                str(platform_user.platform_privilege_set_id)
            )
            privileges = [mapping.privilege_code for mapping in privilege_mappings]
            updated_user = await read_by_id_query(user_id)
            if updated_user:
                new_token = create_platform_token(
                    User.model_validate(updated_user),
                    privileges,
                    password_change_required=False,
                )

    return PasswordChangeResponse(token=new_token)
