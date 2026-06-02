from __future__ import annotations

import base64
import hashlib
import hmac
import os


def hash_password(password: str, salt: bytes | None = None) -> tuple[str, str]:
    if salt is None:
        salt = os.urandom(16)
    derived = hashlib.scrypt(
        password.encode("utf-8"),
        salt=salt,
        n=2**14,
        r=8,
        p=1,
    )
    return (
        base64.b64encode(salt).decode("ascii"),
        base64.b64encode(derived).decode("ascii"),
    )


def verify_password(password: str, salt_b64: str, digest_b64: str) -> bool:
    salt = base64.b64decode(salt_b64.encode("ascii"))
    _, candidate = hash_password(password, salt=salt)
    return hmac.compare_digest(candidate, digest_b64)
