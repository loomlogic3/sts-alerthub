from fastapi import Header, HTTPException

from backend.app.services.token_service import verify_access_token


def get_current_user(
    authorization: str = Header(default=""),
) -> dict:
    """
    Authenticate a request using a Bearer token.

    Returns the decoded user payload.
    """

    if not authorization:
        raise HTTPException(
            status_code=401,
            detail="Missing Authorization header",
        )

    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=401,
            detail="Invalid Authorization header",
        )

    token = authorization.removeprefix("Bearer ").strip()

    payload = verify_access_token(token)

    if payload is None:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired token",
        )

    return payload
