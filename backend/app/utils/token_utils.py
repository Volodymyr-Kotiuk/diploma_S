import hashlib
import secrets


def generate_token() -> str:
    return f"aid_{secrets.token_urlsafe(32)}"


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def preview_token(token: str) -> str:
    return f"{token[:10]}...{token[-6:]}"
