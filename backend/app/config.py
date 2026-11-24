from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# The default is worked out from this file's place, not from the current
# working directory, so the server and the script find the same file
# wherever they are started.
BACKEND_FOLDER = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    # Every field is read from an environment variable named POC_ plus the
    # field name in capitals, for example POC_DATABASE_FILE.
    model_config = SettingsConfigDict(env_prefix="POC_")

    database_file: Path = BACKEND_FOLDER / "data" / "app.db"
