"""
Shared test fixtures and configuration.
"""

import asyncio
import pytest
from typing import AsyncGenerator
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase

from app.database import Base, get_db
from app.main import app
from app.config import Settings


# Test database URL
TEST_DATABASE_URL = "postgresql+asyncpg://test:test@localhost:5433/test_db"


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def test_engine():
    """Create test database engine."""
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)

    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    # Drop all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest.fixture
async def test_session(test_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create test database session."""
    async_session = async_sessionmaker(test_engine, expire_on_commit=False)

    async with async_session() as session:
        yield session
        # Rollback any changes after test
        await session.rollback()


@pytest.fixture
async def client(test_session) -> AsyncGenerator[AsyncClient, None]:
    """Create test client with database session."""

    # Override the get_db dependency
    async def override_get_db():
        yield test_session

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(app=app, base_url="http://testserver") as client:
        yield client

    # Clean up overrides
    app.dependency_overrides.clear()


@pytest.fixture
def test_settings():
    """Test settings fixture."""
    return Settings(
        database_url=TEST_DATABASE_URL,
        debug=True,
        openai_api_key="test-key",
        cors_origins=["http://localhost:3000"]
    )