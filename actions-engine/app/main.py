"""FastAPI application entry point for actions-engine."""

from __future__ import annotations

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.catalogue import load_catalogue
from app.config import settings
from app.models import Base
from app.router import _get_session, router

engine = create_async_engine(settings.database_url, echo=False)
async_session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Yield an async DB session, commit on success, rollback on error."""
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Startup: create tables + load catalogue. Shutdown: dispose engine."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    load_catalogue(settings.catalogue_path)
    app.dependency_overrides[_get_session] = get_session
    yield
    await engine.dispose()


app = FastAPI(
    title="EcoSignal Actions Engine",
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(router, prefix="/api/v1")


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "version": "1.0.0"}


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})
