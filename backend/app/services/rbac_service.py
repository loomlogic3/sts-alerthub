ROLE_PERMISSIONS = {
    "admin": {
        "users:manage",
        "websites:manage",
        "monitors:run",
        "incidents:view",
        "dashboard:view",
    },
    "operator": {
        "websites:manage",
        "monitors:run",
        "incidents:view",
        "dashboard:view",
    },
    "viewer": {
        "incidents:view",
        "dashboard:view",
    },
}


def get_role_permissions(role: str) -> list[str]:
    return sorted(ROLE_PERMISSIONS.get(role, set()))


def role_has_permission(role: str, permission: str) -> bool:
    return permission in ROLE_PERMISSIONS.get(role, set())
