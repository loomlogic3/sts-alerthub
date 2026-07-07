import base64
import hashlib
import hmac
import json
import os
import time


def _b64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("utf-8")


def _b64url_decode(data: str) -> bytes:
    padding = "=" * (-len(data) % 4)
    return base64.urlsafe_b64decode(data + padding)


def _get_secret() -> str:
    secret = os.getenv("ALERTHUB_JWT_SECRET", "dev-only-change-this-secret")

    if secret == "dev-only-change-this-secret":
        print("WARNING: Using development JWT secret. Set ALERTHUB_JWT_SECRET in production.")

    return secret


def create_access_token(payload: dict, expires_in_seconds: int = 3600) -> str:
    header = {
        "alg": "HS256",
        "typ": "JWT",
    }

    body = {
        **payload,
        "exp": int(time.time()) + expires_in_seconds,
    }

    header_b64 = _b64url_encode(json.dumps(header, separators=(",", ":")).encode())
    body_b64 = _b64url_encode(json.dumps(body, separators=(",", ":")).encode())

    signing_input = f"{header_b64}.{body_b64}".encode()
    signature = hmac.new(
        _get_secret().encode(),
        signing_input,
        hashlib.sha256,
    ).digest()

    signature_b64 = _b64url_encode(signature)

    return f"{header_b64}.{body_b64}.{signature_b64}"


def verify_access_token(token: str) -> dict | None:
    try:
        header_b64, body_b64, signature_b64 = token.split(".")
        signing_input = f"{header_b64}.{body_b64}".encode()

        expected_signature = hmac.new(
            _get_secret().encode(),
            signing_input,
            hashlib.sha256,
        ).digest()

        received_signature = _b64url_decode(signature_b64)

        if not hmac.compare_digest(expected_signature, received_signature):
            return None

        payload = json.loads(_b64url_decode(body_b64))

        if int(payload.get("exp", 0)) < int(time.time()):
            return None

        return payload

    except Exception:
        return None
