import base64
import hashlib
import hmac
import secrets
import time

from app.core.config import get_settings


def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 200_000)
    return f"pbkdf2_sha256${salt}${base64.b64encode(digest).decode()}"


def verify_password(password: str, encoded: str) -> bool:
    try:
        scheme, salt, digest = encoded.split("$", 2)
        if scheme != "pbkdf2_sha256":
            return False
        candidate = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 200_000)
        return hmac.compare_digest(candidate, base64.b64decode(digest))
    except (ValueError, UnicodeDecodeError):
        return False


def _sign(payload: str) -> str:
    secret = get_settings().auth_secret.encode()
    return hmac.new(secret, payload.encode(), hashlib.sha256).hexdigest()


def create_access_token(subject: str) -> str:
    settings = get_settings()
    expires = int(time.time()) + settings.access_token_minutes * 60
    payload = f"{subject}.{expires}"
    encoded = base64.urlsafe_b64encode(payload.encode()).decode().rstrip("=")
    return f"{encoded}.{_sign(payload)}"


def verify_access_token(token: str) -> str | None:
    try:
        encoded, signature = token.rsplit(".", 1)
        padding = "=" * (-len(encoded) % 4)
        payload = base64.urlsafe_b64decode(encoded + padding).decode()
        subject, expires_text = payload.rsplit(".", 1)
        if not hmac.compare_digest(signature, _sign(payload)):
            return None
        if int(expires_text) < int(time.time()):
            return None
        return subject
    except (ValueError, UnicodeDecodeError):
        return None


def create_refresh_token() -> str:
    return secrets.token_urlsafe(48)


def hash_refresh_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()
