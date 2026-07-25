"""ConnectXperts NMS - Database Configuration"""
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from sqlalchemy import create_engine
from app.config import settings


def _is_sqlite(url: str) -> bool:
    """Check if the database URL is SQLite."""
    return url.startswith("sqlite")


# Shared engine kwargs (SQLite doesn't support pool_size/max_overflow/pool_pre_ping)
def _get_async_engine_kwargs():
    kwargs = {
        "echo": settings.DEBUG,
    }
    if not _is_sqlite(settings.DATABASE_URL):
        kwargs["pool_size"] = settings.DB_POOL_SIZE
        kwargs["max_overflow"] = settings.DB_MAX_OVERFLOW
        kwargs["pool_pre_ping"] = True
    return kwargs


def _get_sync_engine_kwargs():
    kwargs = {
        "echo": settings.DEBUG,
    }
    if not _is_sqlite(settings.DATABASE_URL_SYNC):
        kwargs["pool_size"] = settings.DB_POOL_SIZE
        kwargs["max_overflow"] = settings.DB_MAX_OVERFLOW
        kwargs["pool_pre_ping"] = True
    else:
        # SQLite needs check_same_thread=False for multi-threaded access
        kwargs["connect_args"] = {"check_same_thread": False}
    return kwargs


# Async engine for FastAPI
async_engine = create_async_engine(
    settings.DATABASE_URL,
    **_get_async_engine_kwargs(),
)

# Sync engine for Celery workers and scripts
sync_engine = create_engine(
    settings.DATABASE_URL_SYNC,
    **_get_sync_engine_kwargs(),
)

AsyncSessionLocal = async_sessionmaker(
    async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

SyncSessionLocal = sessionmaker(
    bind=sync_engine,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    pass


async def get_db():
    """Dependency to get database session."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


def get_sync_db():
    """Get sync database session for Celery tasks."""
    session = SyncSessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


async def init_db():
    """Initialize database - create all tables."""
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def close_db():
    """Close database connections."""
    await async_engine.dispose()
