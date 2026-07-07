from collections.abc import AsyncIterator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.utility.config import get_settings

_engine: AsyncEngine | None = None
_sessionmaker: async_sessionmaker[AsyncSession] | None = None
_orm_models_loaded: bool = False


def _load_orm_models() -> None:
    """Import ORM modules so FK targets exist on Base.metadata before first flush."""
    global _orm_models_loaded
    if _orm_models_loaded:
        return

    from app.business import orm as business_orm  # noqa: F401
    from app.business_user import orm as business_user_orm  # noqa: F401
    from app.genre import orm as genre_orm  # noqa: F401
    from app.privilege import orm as privilege_orm  # noqa: F401
    from app.role import orm as role_orm  # noqa: F401
    from app.role_privilege import orm as role_privilege_orm  # noqa: F401
    from app.platform_invite import orm as platform_invite_orm  # noqa: F401
    from app.platform_privilege import orm as platform_privilege_orm  # noqa: F401
    from app.platform_privilege_set import orm as platform_privilege_set_orm  # noqa: F401
    from app.platform_privilege_set_privilege import orm as platform_privilege_set_privilege_orm  # noqa: F401
    from app.platform_user import orm as platform_user_orm  # noqa: F401
    from app.user import orm as user_orm  # noqa: F401

    _orm_models_loaded = True


def get_postgres_engine() -> AsyncEngine:
    global _engine
    if _engine is None:
        settings = get_settings()
        _engine = create_async_engine(
            settings.postgres_dsn,
            echo=settings.postgres_echo,
            pool_size=settings.postgres_pool_size,
            max_overflow=settings.postgres_max_overflow,
            pool_pre_ping=True,
        )
    return _engine


def get_sessionmaker() -> async_sessionmaker[AsyncSession]:
    global _sessionmaker
    if _sessionmaker is None:
        _load_orm_models()
        _sessionmaker = async_sessionmaker(
            bind=get_postgres_engine(),
            expire_on_commit=False,
            autoflush=False,
        )
    return _sessionmaker


async def get_session() -> AsyncIterator[AsyncSession]:
    async with get_sessionmaker()() as session:
        yield session


async def dispose_postgres_engine() -> None:
    global _engine, _sessionmaker
    if _engine is not None:
        await _engine.dispose()
    _engine = None
    _sessionmaker = None
