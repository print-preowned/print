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
    from app.variant_option import orm as variant_option_orm  # noqa: F401
    from app.variant_type import orm as variant_type_orm  # noqa: F401
    from app.book import orm as book_orm  # noqa: F401
    from app.business_book import orm as business_book_orm  # noqa: F401
    from app.variant import orm as variant_orm  # noqa: F401
    from app.variant_config import orm as variant_config_orm  # noqa: F401
    from app.author import orm as author_orm  # noqa: F401
    from app.book_author import orm as book_author_orm  # noqa: F401
    from app.book_genre import orm as book_genre_orm  # noqa: F401
    from app.order import orm as order_orm  # noqa: F401
    from app.order_item import orm as order_item_orm  # noqa: F401
    from app.book_rating import orm as book_rating_orm  # noqa: F401
    from app.business_rating import orm as business_rating_orm  # noqa: F401
    from app.password_reset_token import orm as password_reset_token_orm  # noqa: F401

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


async def get_db() -> AsyncIterator[AsyncSession]:
    """Request-scoped session for mutating routes; commits on success, rolls back on error."""
    async with get_sessionmaker()() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def dispose_postgres_engine() -> None:
    global _engine, _sessionmaker
    if _engine is not None:
        await _engine.dispose()
    _engine = None
    _sessionmaker = None
