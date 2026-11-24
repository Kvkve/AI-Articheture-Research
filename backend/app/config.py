import secrets
from functools import lru_cache
from pathlib import Path

from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# The default is worked out from this file's place, not from the current
# working directory, so the server and the script find the same file
# wherever they are started.
BACKEND_FOLDER = Path(__file__).resolve().parent.parent

# HS256 needs a key of at least 32 bytes to be as strong as its hash.
SHORTEST_TOKEN_SECRET_KEY = 32


def make_random_token_secret_key() -> SecretStr:
    return SecretStr(secrets.token_urlsafe(32))


class Settings(BaseSettings):
    # Every field is read from an environment variable named POC_ plus the
    # field name in capitals, for example POC_DATABASE_FILE.
    # hide_input_in_errors keeps a refused secret key out of error messages.
    model_config = SettingsConfigDict(env_prefix="POC_", hide_input_in_errors=True)

    database_file: Path = BACKEND_FOLDER / "data" / "app.db"

    # The key that signs the tokens. When POC_TOKEN_SECRET_KEY is not set, a
    # new random key is made, so a restart of the backend signs every user
    # out. SecretStr keeps the key out of printed settings.
    token_secret_key: SecretStr = Field(default_factory=make_random_token_secret_key)

    # 8 days, as in the FastAPI full-stack template.
    token_expire_minutes: int = Field(default=60 * 24 * 8, gt=0)

    @field_validator("token_secret_key")
    @classmethod
    def refuse_a_short_key(cls, key: SecretStr) -> SecretStr:
        if len(key.get_secret_value()) < SHORTEST_TOKEN_SECRET_KEY:
            raise ValueError(
                "POC_TOKEN_SECRET_KEY must have at least "
                f"{SHORTEST_TOKEN_SECRET_KEY} characters."
            )
        return key


# With a random key, every new Settings object has a different key. So the
# application makes the settings once per process and shares that one
# object. Tests clear this cache to give each test its own settings.
@lru_cache
def get_settings() -> Settings:
    return Settings()
