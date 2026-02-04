import asyncio
import uuid
from collections.abc import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import settings
from app.core.dependencies import get_db
from app.db.base import Base
from app.main import app

# Use a separate test database
TEST_DATABASE_URL = settings.DATABASE_URL.replace("/epistratify", "/epistratify_test")

test_engine = create_async_engine(TEST_DATABASE_URL, echo=False)
test_session_factory = async_sessionmaker(
    test_engine, class_=AsyncSession, expire_on_commit=False
)


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    # Import all models so tables are registered
    import app.models  # noqa: F401

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with test_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def authenticated_client(
    client: AsyncClient, db_session: AsyncSession
) -> AsyncClient:
    # Register a test user
    register_data = {
        "email": f"test-{uuid.uuid4().hex[:8]}@test.com",
        "password": "testpassword123",
        "full_name": "Test User",
        "organization": "Test Org",
    }
    await client.post("/api/v1/auth/register", json=register_data)

    # Login
    login_data = {
        "email": register_data["email"],
        "password": register_data["password"],
    }
    response = await client.post("/api/v1/auth/login", json=login_data)
    token = response.json()["access_token"]

    client.headers["Authorization"] = f"Bearer {token}"
    return client
