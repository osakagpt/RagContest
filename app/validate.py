from datetime import datetime
import json, time

import numpy as np
from fastapi import FastAPI, Request, HTTPException, Body, Depends, Security
from sqlalchemy import select, insert
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload


from database import get_db_session
from embedding_api_client import OpenAIClient
from model import (
    Base,
    User,
    Contest,
    DataSource,
    Question,
    AnswerEmbedding,
    AnswerOption,
    UserAnswer,
    ContestFirstDownloaded,
    QuestionFirstDownloaded,
)


class UserAnswerScorer:
    def __init__(self, question: Question, time_taken_ms: int, right_answer_vector):
        self._query = question.query
        self._has_options = question.number_of_options > 0
        self._right_answer = question.right_answer
        self._time_taken_ms = time_taken_ms
        self._right_answer_vector = right_answer_vector
        self.threshold = 0.95

    @classmethod
    async def create(cls, user_id: int, question_id: int, session: AsyncSession):
        result = await session.execute(
            select(Question).options(joinedload(Question.right_answer)).filter(Question.id == question_id)
        )
        question = result.scalars().first()
        result = await session.execute(
            select(QuestionFirstDownloaded)
            .filter(QuestionFirstDownloaded.user_id == user_id)
            .filter(QuestionFirstDownloaded.question_id == question_id)
        )
        question_first_downloaded = result.scalars().first()
        time_taken_ms = (int)((datetime.now() - question_first_downloaded.downloaded_at).total_seconds() * 1000)

        return cls(question, time_taken_ms, question.right_answer.text_embedding_3_small)

    def get_score(self, user_answer: str) -> float:
        embedding = OpenAIClient().get_embedding(self._query, user_answer)
        self.similarity = self.__cosine_similarity(embedding, self._right_answer_vector)
        return self.similarity

    def is_correct(self, similarity: float) -> bool:
        if self._has_options:
            return similarity >= 0.999
        else:
            return similarity >= self.threshold

    def get_time(self):
        return self._time_taken_ms

    def __cosine_similarity(self, a, b):
        return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))
