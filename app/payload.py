from pydantic import BaseModel
from datetime import datetime
from typing import List, Dict, Optional


class DataSourcePayload(BaseModel):
    path: str
    type: str
    description: Optional[str]

    class Config:
        orm_mode = True


class QuestionOut(BaseModel):
    id: int
    query: str
    options: List[str]
    description: Optional[str]

    class Config:
        orm_mode = True


class UserAnswerSubmission(BaseModel):
    answer: str

    class Config:
        orm_mode = True


class UserAnswerOut(BaseModel):
    question_id: int
    answer: str
    is_correct: bool
    similarity: float
    time_taken_ms: int
    not_answered_question_ids: list[int]

    class Config:
        orm_mode = True


class QueryAnswer(BaseModel):
    query: str
    options: List[str]
    answer: str
    description: Optional[str]


class ContestInfo(BaseModel):
    name: str
    description: Optional[str]

    class Config:
        orm_mode = True


class ContestIn(BaseModel):
    contest_info: ContestInfo
    data_sources: List[DataSourcePayload]
    query_answers: List[QueryAnswer]


class ContestOut(BaseModel):
    id: int
    name: str
    questions: List[int]
    description: Optional[str]
    start_at: Optional[datetime]
    end_at: Optional[datetime]
    data_sources: List[DataSourcePayload]

    class Config:
        orm_mode = True

