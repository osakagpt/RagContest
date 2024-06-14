from datetime import datetime
from enum import Enum

from pgvector.sqlalchemy import Vector
from sqlalchemy import (
    Column,
    Integer,
    Float,
    String,
    Boolean,
    DateTime,
    Enum as EnumType,
    ForeignKey,
    UniqueConstraint,
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class ContestStatus(Enum):
    Registered = "Registered"
    Scheduled = "Scheduled"
    Running = "Running"
    Done = "Done"


class DataSourceType(Enum):
    """未使用"""

    TEXT = "TEXT"
    PDF = "PDF"
    EXCEL = "EXCEL"
    WORD = "WORD"
    PPT = "PPT"
    IMAGE = "IMAGE"
    AUDIO = "AUDIO"
    UNKNOWN = "UNKNOWN"


class User(Base):
    __tablename__ = "user"
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    password = Column(String)
    api_key = Column(String, unique=True)
    registered_at = Column(DateTime, default=datetime.now, nullable=False)
    is_admin = Column(Boolean, default=False, nullable=False)

    user_answers = relationship("UserAnswer", back_populates="user")
    contests_downloaded = relationship("ContestFirstDownloaded", back_populates="user")
    questions_downloaded = relationship("QuestionFirstDownloaded", back_populates="user")
    contest_results = relationship("ContestResult", back_populates="user")


class Contest(Base):
    __tablename__ = "contest"
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)
    number_of_questions = Column(Integer, nullable=False)
    description = Column(String)
    status = Column(EnumType(ContestStatus), default=ContestStatus.Registered, nullable=False)
    start_at = Column(DateTime)
    end_at = Column(DateTime)

    data_sources = relationship("DataSource", back_populates="contest")
    questions = relationship("Question", back_populates="contest")
    contests_downloaded = relationship("ContestFirstDownloaded", back_populates="contest")
    contest_results = relationship("ContestResult", back_populates="contest")


# Define the DataSource class
class DataSource(Base):
    __tablename__ = "data_source"
    id = Column(Integer, primary_key=True)
    contest_id = Column(Integer, ForeignKey("contest.id", ondelete="CASCADE"), nullable=False)
    path = Column(String, nullable=False)
    type = Column(String, nullable=False)
    description = Column(String)

    contest = relationship("Contest", back_populates="data_sources")


# Define the Question class
class Question(Base):
    __tablename__ = "question"
    id = Column(Integer, primary_key=True)
    contest_id = Column(Integer, ForeignKey("contest.id", ondelete="CASCADE"), nullable=False)
    query = Column(String, nullable=False)
    number_of_options = Column(Integer, nullable=False)
    description = Column(String)

    contest = relationship("Contest", back_populates="questions")
    right_answer = relationship("AnswerEmbedding", back_populates="question", uselist=False)
    user_answers = relationship("UserAnswer", back_populates="question")
    answer_options = relationship("AnswerOption", back_populates="question")
    questions_downloaded = relationship("QuestionFirstDownloaded", back_populates="question")


class AnswerEmbedding(Base):
    __tablename__ = "answer_embedding"
    id = Column(Integer, primary_key=True)
    question_id = Column(Integer, ForeignKey("question.id", ondelete="CASCADE"), nullable=False, unique=True)
    answer = Column(String, nullable=False)
    text_embedding_3_small = Column(Vector(1536), nullable=True)

    question = relationship("Question", back_populates="right_answer")


class AnswerOption(Base):
    __tablename__ = "answer_option"
    id = Column(Integer, primary_key=True)
    question_id = Column(Integer, ForeignKey("question.id", ondelete="CASCADE"), nullable=False)
    option_text = Column(String, nullable=False)

    question = relationship("Question", back_populates="answer_options")


# Define the Answer class
class UserAnswer(Base):
    __tablename__ = "user_answer"
    id = Column(Integer, primary_key=True)
    answer = Column(String, nullable=False)
    user_id = Column(Integer, ForeignKey("user.id", ondelete="CASCADE"), nullable=False)
    question_id = Column(Integer, ForeignKey("question.id", ondelete="CASCADE"), nullable=False)
    is_correct = Column(Boolean, nullable=False)
    similarity = Column(Float, nullable=False)
    submitted_at = Column(DateTime, default=datetime.now, nullable=False)
    time_taken_ms = Column(Integer, nullable=False)

    user = relationship("User", back_populates="user_answers")
    question = relationship("Question", back_populates="user_answers")


class ContestFirstDownloaded(Base):
    __tablename__ = "contest_first_downloaded"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("user.id", ondelete="CASCADE"), nullable=False)
    contest_id = Column(Integer, ForeignKey("contest.id", ondelete="CASCADE"), nullable=False)
    downloaded_at = Column(DateTime, default=datetime.now, nullable=False)

    user = relationship("User", back_populates="contests_downloaded")
    contest = relationship("Contest", back_populates="contests_downloaded")
    __table_args__ = (UniqueConstraint("user_id", "contest_id", name="uq_user_contest"),)


class QuestionFirstDownloaded(Base):
    __tablename__ = "question_first_downloaded"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("user.id", ondelete="CASCADE"), nullable=False)
    question_id = Column(Integer, ForeignKey("question.id", ondelete="CASCADE"), nullable=False)
    downloaded_at = Column(DateTime, default=datetime.now, nullable=False)

    user = relationship("User", back_populates="questions_downloaded")
    question = relationship("Question", back_populates="questions_downloaded")
    __table_args__ = (UniqueConstraint("user_id", "question_id", name="uq_user_question"),)


class ContestResult(Base):
    __tablename__ = "contest_result"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("user.id", ondelete="CASCADE"), nullable=False)
    contest_id = Column(Integer, ForeignKey("contest.id", ondelete="CASCADE"), nullable=False)
    number_of_correct_answers = Column(Integer, nullable=False)
    time_ms = Column(Integer, nullable=False)

    user = relationship("User", back_populates="contest_results")
    contest = relationship("Contest", back_populates="contest_results")
    __table_args__ = (UniqueConstraint("user_id", "contest_id", name="uq_user_contest_result"),)
