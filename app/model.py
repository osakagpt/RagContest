from datetime import datetime
import os
from contextlib import asynccontextmanager
from typing import Any, AsyncIterator

from sqlalchemy import (
    Column,
    Integer,
    String,
    Boolean,
    DateTime,
    ForeignKey,
)
from sqlalchemy.ext.asyncio import (
    AsyncConnection,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


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
    async def create_tables(self):
        async with self.connect() as conn:
            await conn.run_sync(Base.metadata.drop_all)
            await conn.run_sync(Base.metadata.create_all)


class User(Base):
    __tablename__ = "user"
    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    password = Column(String)
    api_key = Column(String, unique=True)
    answers = relationship("Answer", backref="user")


class Contest(Base):
    __tablename__ = "contest"
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    number_of_questions = Column(Integer, nullable=False)
    description = Column(String)
    start_at = Column(DateTime, nullable=True)
    end_at = Column(DateTime, nullable=True)
    data_sources = relationship("DataSource", backref="contest")
    questions = relationship("Question", backref="contest")


# Define the DataSource class
class DataSource(Base):
    __tablename__ = "data_source"
    id = Column(Integer, primary_key=True)
    contest_id = Column(Integer, ForeignKey("contest.id"), nullable=False)
    path = Column(String, nullable=False)
    type = Column(String, nullable=False)
    description = Column(String)


# Define the Question class
class Question(Base):
    __tablename__ = "question"
    id = Column(Integer, primary_key=True)
    contest_id = Column(Integer, ForeignKey("contest.id"), nullable=False)
    query = Column(String, nullable=False)
    right_answer = Column(String, nullable=False)
    description = Column(String)
    answers = relationship("Answer", backref="question")


# Define the Answer class
class Answer(Base):
    __tablename__ = "answer"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("user.id"), nullable=False)
    question_id = Column(Integer, ForeignKey("question.id"), nullable=False)
    is_correct = Column(Boolean, nullable=False)
    solving_time_ms = Column(Integer, nullable=True)
    answered_at = Column(DateTime, default=datetime.now(), nullable=True)


# Create the tables
async def create_tables(engine):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)


username = os.getenv("POSTGRES_USER")
passwd = os.getenv("POSTGRES_PASSWORD")
dbname = os.getenv("POSTGRES_DB")
DATABASE_URL = f"postgresql+asyncpg://{username}:{passwd}@postgres:5432/{dbname}"
print(DATABASE_URL)
# Create the engine and sessionmaker
session_manager = DatabaseSessionManager(DATABASE_URL, {"echo": True, "future": True})
