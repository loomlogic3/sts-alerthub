import hashlib
import secrets


def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)

    password_hash = hashlib.sha256(
        f"{salt}:{password}".encode("utf-8")
    ).hexdigest()

    return f"{salt}:{password_hash}"


def verify_password(
    password: str,
    stored_password_hash: str,
) -> bool:
    try:
        salt, expected_hash = stored_password_hash.split(":", 1)
    except ValueError:
        return False

    actual_hash = hashlib.sha256(
        f"{salt}:{password}".encode("utf-8")
    ).hexdigest()

    return secrets.compare_digest(
        actual_hash,
        expected_hash,
    )
