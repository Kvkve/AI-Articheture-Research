# Follows backend/app/core/security.py in the official FastAPI full-stack
# template (MIT license): the password part, and create_access_token with
# ALGORITHM for the tokens. See docs/sources.md.
# Unlike the template, only Argon2 is used, because this project has no old
# bcrypt hashes to read, and plain verify is used, because nothing here
# upgrades old hashes.
from datetime import UTC, datetime, timedelta

import jwt
from pwdlib import PasswordHash
from pwdlib.hashers.argon2 import Argon2Hasher

password_hasher = PasswordHash((Argon2Hasher(),))

# A constant, not a setting: a setting could choose a weak algorithm, or
# "none", which turns the signature check off.
ALGORITHM = "HS256"


def hash_password(password: str) -> str:
    return password_hasher.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    return password_hasher.verify(password, password_hash)


def create_access_token(user_id: int, secret_key: str, lifetime: timedelta) -> str:
    expires_at = datetime.now(UTC) + lifetime
    # The JWT standard requires "sub" to be text, so the id is turned into text.
    payload = {"sub": str(user_id), "exp": expires_at}
    return jwt.encode(payload, secret_key, algorithm=ALGORITHM)


def read_access_token(token: str, secret_key: str) -> int | None:
    """Return the user id in the token, or None if the token is not valid."""
    try:
        # decode checks the signature and the expiry time. Only ALGORITHM is
        # accepted, whatever the token's own header says.
        payload = jwt.decode(
            token,
            secret_key,
            algorithms=[ALGORITHM],
            options={"require": ["exp", "sub"]},
        )
    except jwt.InvalidTokenError:
        return None

    user_id = payload["sub"]
    # int() alone would also accept text such as " 7" or "1_000".
    if not isinstance(user_id, str) or not (user_id.isascii() and user_id.isdigit()):
        return None
    return int(user_id)
