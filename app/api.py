from datetime import datetime
import os
from typing import List

import bcrypt

from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, HTTPException, Body, Depends, Security
from fastapi.responses import FileResponse
from fastapi.responses import HTMLResponse
from fastapi.security import APIKeyHeader
from fastapi.staticfiles import StaticFiles
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, insert
from sqlalchemy.orm import joinedload
import secrets

from model import User, Contest, Question, Answer, session_manager
from pydantic_model import ContestOut, QuestionOut, AnswerIn, AnswerOut


API_HEADER_NAME = "x-api-key"
api_key_header = APIKeyHeader(name=API_HEADER_NAME, auto_error=False)


async def get_db_session():
    async with session_manager.session() as session:
        yield session


def generate_api_key():
    return secrets.token_urlsafe(16)


async def get_user_by_api_key(
    api_key: str, session: AsyncSession = Depends(get_db_session)
) -> User:
    result = await session.execute(select(User).filter(User.api_key == api_key))
    return result.scalar_one_or_none()


async def get_validated_user(
    api_key_header: str = Security(api_key_header),
    session: AsyncSession = Depends(get_db_session),
    # user: User = Depends(get_user_by_api_key),
):
    user = await get_user_by_api_key(api_key_header, session)
    if user:
        return user
    else:
        raise HTTPException(status_code=403, detail="Invalid API Key")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # write startup event here
    # await session_manager.create_tables()
    yield
    # write shutdown event here


app = FastAPI(title="Rag Contest", lifespan=lifespan)
app.mount("/html", StaticFiles(directory="html"), name="html")


@app.get("/health")
async def health_check():
    return {"status": "UP"}


@app.get("/")
async def read_root():
    return FileResponse("./html/index.html", media_type="text/html")


@app.get("/api/contest/{contest_id}", response_model=ContestOut)
async def get_contest(
    contest_id: int,
    user: User = Security(get_validated_user),
    session: AsyncSession = Depends(get_db_session),
):
    result = await session.execute(
        select(Contest)
        .options(joinedload(Contest.data_sources))
        .filter(Contest.id == contest_id)
    )
    contest = result.scalars().first()

    if contest is None:
        raise HTTPException(status_code=404, detail="Contest not found")

    return contest


@app.get("/api/question/{question_id}", response_model=QuestionOut)
async def get_question(
    question_id: int,
    user: User = Security(get_validated_user),
    session: AsyncSession = Depends(get_db_session),
):
    result = await session.execute(select(Question).filter(Question.id == question_id))
    question = result.scalars().first()
    if question is None:
        raise HTTPException(status_code=404, detail="Question not found")

    return question


@app.get("/api/contest/{contest_id}/questions", response_model=List[QuestionOut])
async def get_questions(
    contest_id: int,
    user: User = Security(get_validated_user),
    session: AsyncSession = Depends(get_db_session),
):
    results = await session.execute(select(Question).filter(Contest.id == contest_id))
    questions = results.scalars().all()
    if questions is None:
        raise HTTPException(status_code=404, detail="Question not found")

    return questions


@app.post("/api/question/{question_id}", response_model=AnswerOut)
async def submit_answer(
    question_id: int,
    answer_submission: AnswerIn = Body(...),
    user: User = Security(get_validated_user),
    session: AsyncSession = Depends(get_db_session),
):
    """答え合わせの処理
    ユーザーの提出回答と正解を照合して正しいかどうか、かかった時間をデータベースに保存してメインページに表示"""
    # Fetch the question from the database
    result = await session.execute(select(Question).filter(Question.id == question_id))
    question = result.scalars().first()
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")

    # Check if the answer is correct
    is_correct = answer_submission.answer == question.right_answer
    solving_time_ms = 0

    # Create a new answer record
    new_answer = Answer(
        user_id=user.id,
        question_id=question_id,
        is_correct=is_correct,
        solving_time_ms=solving_time_ms,
        answered_at=datetime.now(),
    )
    answered_at = new_answer.answered_at.strftime("%Y-%m-%d %H:%M:%S")
    session.add(new_answer)
    await session.commit()

    return AnswerOut(
        question_id=question_id,
        answer=answer_submission.answer,
        is_correct=is_correct,
        solving_time_ms=solving_time_ms,
        answered_at=answered_at,
    )


@app.get("/signup")
async def signup_page():
    return FileResponse("./html/signup.html", media_type="text/html")


@app.post("/signup")
async def signup(
    username: str = Body(...),
    email: str = Body(...),
    password: str = Body(...),
    session: AsyncSession = Depends(get_db_session),
):
    hashed_password = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())
    new_api_key = generate_api_key()
    await session.execute(
        insert(User).values(
            username=username,
            email=email,
            password=hashed_password.decode("utf-8"),
            api_key=new_api_key,
        )
    )
    await session.commit()
    return {"api_key": new_api_key}
