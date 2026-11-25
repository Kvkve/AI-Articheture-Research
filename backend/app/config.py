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

# One year. A much larger lifetime puts the expiry time past the largest date
# that Python can hold, and then every sign-in answers 500.
LONGEST_TOKEN_EXPIRE_MINUTES = 60 * 24 * 365


DEFAULT_SYSTEM_PROMPT = (
    "You are a helpful assistant in a chat application. "
    "Answer in the language the user writes in. "
    "Use Markdown when it makes the answer easier to read. "
    "You have no tools: you cannot browse the web, read files or run code. "
    "If you do not know something, say so."
)


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
    token_expire_minutes: int = Field(
        default=60 * 24 * 8, gt=0, le=LONGEST_TOKEN_EXPIRE_MINUTES
    )

    # The key of the model provider, from POC_MODEL_API_KEY. With no key the
    # backend still starts, and sending a message is refused with a clear
    # error. SecretStr keeps the key out of printed settings.
    model_api_key: SecretStr | None = None

    # The model name sent to the provider, the provider type that the SDK is
    # given, and the provider's address.
    model_name: str = "claude-haiku-5-5"
    model_provider_type: str = "anthropic"
    model_provider_address: str = "https://api.anthropic.com"

    # The folder that holds the SDK's session files: the conversation
    # history, as plain text.
    session_directory: Path = BACKEND_FOLDER / "data" / "sessions"

    # The system prompt of every conversation. It replaces the runtime's own
    # prompt, which is written for a coding agent.
    system_prompt: str = DEFAULT_SYSTEM_PROMPT

    # The longest time, in seconds, to wait for the next event of an answer.
    # When it runs out, the answer ends with an error and the conversation
    # is freed, so a provider that stops answering cannot block it for ever.
    answer_wait_seconds: float = Field(default=120, gt=0)

    # The longest message a user may send, in characters. The SDK stores each
    # message and sends it again with every later message of the
    # conversation, so one very long message would cost much at every turn.
    longest_message_characters: int = Field(default=20_000, gt=0)

    # How many characters of the first message become the conversation's
    # title.
    title_characters: int = Field(default=50, gt=0)

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
# The start-up step in backend/app/main.py calls it before the first request
# is served, so two first requests cannot each make their own settings.
@lru_cache
def get_settings() -> Settings:
    return Settings()
