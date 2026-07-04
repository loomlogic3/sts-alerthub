from fastapi import HTTPException


def require_role(current_role: str, allowed_roles: set[str]) -> None:
    if current_role not in allowed_roles:
        raise HTTPException(
            status_code=403,
            detail="Permission denied",
        )


def require_admin(current_role: str) -> None:
    require_role(
        current_role=current_role,
        allowed_roles={"admin"},
    )


def require_operator(current_role: str) -> None:
    require_role(
        current_role=current_role,
        allowed_roles={"admin", "operator"},
    )
