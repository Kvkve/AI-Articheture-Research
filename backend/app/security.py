# Follows the password part of backend/app/core/security.py in the official
# FastAPI full-stack template (MIT license). See docs/sources.md.
# Unlike the template, only Argon2 is used, because this project has no old
# bcrypt hashes to read, and plain verify is used, because nothing here
# upgrades old hashes.
from pwdlib import PasswordHash
from pwdlib.hashers.argon2 import Argon2Hasher

password_hasher = PasswordHash((Argon2Hasher(),))


def hash_password(password: str) -> str:
    return password_hasher.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    return password_hasher.verify(password, password_hash)
