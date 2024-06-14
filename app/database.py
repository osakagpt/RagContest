from datetime import datetime
import os
from contextlib import asynccontextmanager
from typing import Any, AsyncIterator

from fastapi import Depends
from sqlalchemy.ext.asyncio import (
    AsyncConnection,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from logger_config import logger


class DatabaseSessionManager:
    def __init__(self, host: str, engine_kwargs: dict[str, Any] = {}):
        self._engine = create_async_engine(host, **engine_kwargs)
        self._sessionmaker = async_sessionmaker(autocommit=False, bind=self._engine)

    async def close(self):
        if self._engine is None:
            raise Exception("DatabaseSessionManager is not initialized")
        await self._engine.dispose()

        self._engine = None
        self._sessionmaker = None

    @asynccontextmanager
    async def connect(self) -> AsyncIterator[AsyncConnection]:
        if self._engine is None:
            raise Exception("DatabaseSessionManager is not initialized")

        async with self._engine.begin() as connection:
            try:
                yield connection
            except Exception:
                await connection.rollback()
                raise

    @asynccontextmanager
    async def session(self) -> AsyncIterator[AsyncSession]:
        if self._sessionmaker is None:
            raise Exception("DatabaseSessionManager is not initialized")

        session = self._sessionmaker()
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

    # Create the tables
    async def create_tables(self, Base):
        async with self.connect() as conn:
            # await conn.run_sync(Base.metadata.drop_all)
            await conn.run_sync(Base.metadata.create_all)


def get_database_url():
    username = os.getenv("POSTGRES_USER")
    passwd = os.getenv("POSTGRES_PASSWORD")
    dbname = os.getenv("POSTGRES_DB")
    logger.info(f"username:: {username}")
    return f"postgresql+asyncpg://{username}:{passwd}@postgres:5432/{dbname}"


def get_session_manager() -> DatabaseSessionManager:
    return DatabaseSessionManager(get_database_url(), {"echo": True, "future": True})


async def get_db_session(dbsm: DatabaseSessionManager = Depends(get_session_manager)):
    async with dbsm.session() as session:
        yield session
