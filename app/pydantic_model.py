from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional


class DataSourceOut(BaseModel):
    path: str
    type: str
    description: Optional[str]

    class Config:
        orm_mode = True


class QuestionOut(BaseModel):
    id: int
    query: str
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
    solving_time_ms: int

    class Config:
        orm_mode = True


class ContestOut(BaseModel):
    id: int
    name: str
    number_of_questions: int
    description: Optional[str]
    start_at: Optional[datetime]
    end_at: Optional[datetime]
    data_sources: List[DataSourceOut]

    class Config:
        orm_mode = True
