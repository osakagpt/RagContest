from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional


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


class UserAnswerIn(BaseModel):
    answer: str

    class Config:
        orm_mode = True


class UserAnswerOut(BaseModel):
    question_id: int
    answer: str
    is_correct: bool
    time_taken_ms: int
    is_all_submitted: bool

    class Config:
        orm_mode = True


class QueryAnswer(BaseModel):
    query: str
    options: List[str]
    answer: str


class ContestIn(BaseModel):
    contest_name: str
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


class ResultPayload(BaseModel):
    user: str
    contest: str
    query: str
    answer: str
    is_correct: bool
    time: int
