from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.config import Settings
from app.database import connect, create_tables


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    # Runs once when the application starts. CREATE TABLE IF NOT EXISTS makes
    # the tables on the first start and leaves the data alone on later starts.
    settings = Settings()
    connection = connect(settings.database_file)
    try:
        create_tables(connection)
    finally:
        connection.close()
    yield


app = FastAPI(title="AI Agent Platform", lifespan=lifespan)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
