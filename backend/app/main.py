from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app import login, protected
from app.config import get_settings
from app.database import connect, create_tables


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    # Runs once when the application starts. CREATE TABLE IF NOT EXISTS makes
    # the tables on the first start and leaves the data alone on later starts.
    settings = get_settings()
    connection = connect(settings.database_file)
    try:
        create_tables(connection)
    finally:
        connection.close()
    yield


app = FastAPI(title="AI Agent Platform", lifespan=lifespan)

# Open endpoints: /health and the sign-in endpoint. FastAPI also adds the
# pages of the generated API documentation, which are open too.
app.include_router(login.router)
# Every endpoint on this router needs a token.
app.include_router(protected.router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
