from datetime import datetime
import os

from sqlalchemy import (
    Column,
    Integer,
    String,
    Boolean,
    DateTime,
    ForeignKey,
    UniqueConstraint,
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class User(Base):
    __tablename__ = "user"
    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    password = Column(String)
    api_key = Column(String, unique=True)
    registered_at = Column(DateTime, default=datetime.now(), nullable=False)

    user_answers = relationship("UserAnswer", backref="user")
    contests_downloaded = relationship("ContestFirstDownloaded", backref="user")
    questions_downloaded = relationship("QuestionFirstDownloaded", backref="user")


class Contest(Base):
    __tablename__ = "contest"
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)
    number_of_questions = Column(Integer, nullable=False)
    description = Column(String)
    start_at = Column(DateTime, nullable=True)
    end_at = Column(DateTime, nullable=True)

    data_sources = relationship("DataSource", backref="contest")
    questions = relationship("Question", backref="contest")
    contests_downloaded = relationship("ContestFirstDownloaded", backref="contest")


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
    number_of_options = Column(Integer, nullable=False)
    description = Column(String)

    user_answers = relationship("UserAnswer", backref="question")
    answer_options = relationship("AnswerOption", back_populates="question")
    questions_downloaded = relationship("QuestionFirstDownloaded", backref="question")


class AnswerOption(Base):
    __tablename__ = "answer_option"
    id = Column(Integer, primary_key=True)
    question_id = Column(
        Integer,
        ForeignKey("question.id", ondelete="CASCADE"),
        nullable=False,
    )
    option_text = Column(String, nullable=False)

    question = relationship("Question", back_populates="answer_options")


# Define the Answer class
class UserAnswer(Base):
    __tablename__ = "user_answer"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("user.id"), nullable=False)
    question_id = Column(Integer, ForeignKey("question.id"), nullable=False)
    is_correct = Column(Boolean, nullable=False)
    submitted_at = Column(DateTime, default=datetime.now(), nullable=False)


class ContestFirstDownloaded(Base):
    __tablename__ = "contest_first_downloaded"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("user.id"), nullable=False)
    contest_id = Column(Integer, ForeignKey("contest.id"), nullable=False)
    downloaded_at = Column(DateTime, default=datetime.now(), nullable=False)
    __table_args__ = (
        UniqueConstraint("user_id", "contest_id", name="uq_user_contest"),
    )


class QuestionFirstDownloaded(Base):
    __tablename__ = "question_first_downloaded"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("user.id"), nullable=False)
    question_id = Column(Integer, ForeignKey("question.id"), nullable=False)
    downloaded_at = Column(DateTime, default=datetime.now(), nullable=False)
    __table_args__ = (
        UniqueConstraint("user_id", "question_id", name="uq_user_question"),
    )
