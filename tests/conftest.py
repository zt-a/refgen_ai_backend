import uuid

from contextlib import asynccontextmanager

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from src.auth.services import get_current_user, get_current_user_refresh
from src.auth.utils import hash_password
from src.database import get_async_session
from src.db_base import Base
from src.main import app
from src.models.profile import Profile
from src.models.users import User


engine = create_engine(
    "sqlite+pysqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
    future=True,
)
SessionFactory = sessionmaker(bind=engine, expire_on_commit=False, autoflush=False)


class AsyncSessionStub:
    def __init__(self, sync_session: Session):
        self._session = sync_session

    def add(self, instance):
        self._session.add(instance)

    def add_all(self, instances):
        self._session.add_all(instances)

    async def flush(self):
        self._session.flush()

    async def execute(self, *args, **kwargs):
        return self._session.execute(*args, **kwargs)

    async def commit(self):
        self._session.commit()

    async def rollback(self):
        self._session.rollback()

    async def refresh(self, instance, attribute_names=None):
        self._session.refresh(instance, attribute_names=attribute_names)

    async def delete(self, instance):
        self._session.delete(instance)

    async def get(self, *args, **kwargs):
        return self._session.get(*args, **kwargs)

    async def close(self):
        self._session.close()

    def expire_all(self):
        self._session.expire_all()

    def __getattr__(self, item):
        return getattr(self._session, item)


@pytest.fixture(scope="session")
def anyio_backend() -> str:
    return "asyncio"


@pytest.fixture
async def db_session():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    sync_session = SessionFactory()
    async_session = AsyncSessionStub(sync_session)
    try:
        yield async_session
    finally:
        await async_session.close()


@pytest.fixture
async def client(db_session) -> AsyncClient: # type: ignore
    async def _get_session():
        yield db_session

    app.dependency_overrides[get_async_session] = _get_session
    
    @asynccontextmanager
    async def _lifespan(app_instance):
        yield

    app.router.lifespan_context = _lifespan

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as test_client:
        yield test_client

    app.dependency_overrides.pop(get_async_session, None)


@pytest.fixture
def auth_override():
    def _apply(user: User):
        async def _get_current_user():
            return user

        app.dependency_overrides[get_current_user] = _get_current_user
        app.dependency_overrides[get_current_user_refresh] = _get_current_user

    yield _apply

    app.dependency_overrides.pop(get_current_user, None)
    app.dependency_overrides.pop(get_current_user_refresh, None)


@pytest.fixture
def user_factory(db_session):
    async def _create_user(
        *,
        with_profile: bool = True,
        password: str = "secret123",
        profile_overrides: dict | None = None,
    ) -> User:
        suffix = uuid.uuid4().hex[:6]
        user = User(
            username=f"user_{suffix}",
            email=f"{suffix}@example.com",
            hashed_password=hash_password(password),
        )
        db_session.add(user)
        await db_session.flush()

        if with_profile:
            defaults = {
                "name": "Ivan",
                "surname": "Petrov",
                "patronymic": "Ivanovich",
                "university": "Test University",
                "faculty": "Computer Science",
                "course": 1,
                "group": "A1",
                "city": "Moscow",
                "phone_number": "1234567890",
                "avatar_url": None,
            }
            if profile_overrides:
                defaults.update(profile_overrides)

            profile = Profile(user_id=user.id, **defaults)
            db_session.add(profile)

        await db_session.commit()
        await db_session.refresh(user)

        if with_profile:
            await db_session.refresh(user, attribute_names=["profile"])

        return user

    return _create_user
