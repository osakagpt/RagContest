from typing import List, Dict
from datetime import timedelta
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Response, HTTPException, Body, Depends, Security, status
from fastapi.responses import FileResponse, RedirectResponse
from fastapi.security import APIKeyHeader
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from jose import jwt
from jose.exceptions import JWTError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from sqlalchemy.orm import joinedload
import secrets

from config import jwt_settings
from database import get_db_session, get_session_manager
from embedding_api_client import OpenAIClient
from model import (
    Base,
    ContestStatus,
    User,
    TemporaryUser,
    Contest,
    ContestResult,
    DataSource,
    Question,
    AnswerEmbedding,
    AnswerOption,
    UserAnswer,
    ContestFirstDownloaded,
    QuestionFirstDownloaded,
)
from logger_config import logger
from payload import (
    ContestIn,
    ContestOut,
    DataSourcePayload,
    QuestionOut,
    UserAnswerSubmission,
    UserAnswerOut,
)
from utils import (
    verify_password,
    get_password_hash,
    create_access_token,
    fetch_access_token_from_cookie_header,
    format_millisec,
    authenticate_user,
)
from validate import UserAnswerScorer


API_HEADER_NAME = "x-api-key"
api_key_header = APIKeyHeader(name=API_HEADER_NAME, auto_error=False)


def generate_api_key():
    return secrets.token_urlsafe(16)


async def get_user_by_api_key(api_key: str, session: AsyncSession = Depends(get_db_session)) -> User:
    result = await session.execute(select(User).where(User.api_key == api_key))
    return result.scalar_one_or_none()


async def get_validated_user(
    api_key_header: str = Security(api_key_header),
    session: AsyncSession = Depends(get_db_session),
):
    user = await get_user_by_api_key(api_key_header, session)
    if user:
        return user
    else:
        raise HTTPException(status_code=403, detail="Invalid API Key")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # write startup event here
    await get_session_manager().create_tables(Base)
    yield
    # write shutdown event here


logger.info("API Server starting...")
app = FastAPI(title="Rag Contest", lifespan=lifespan)
logger.info("API Server started")
app.mount("/html", StaticFiles(directory="html"), name="html")
templates = Jinja2Templates(directory="template")


@app.get("/api/contests", response_model=Dict[int, str])
async def get_contests_list(
    user: User = Security(get_validated_user),
    session: AsyncSession = Depends(get_db_session),
):
    result = await session.execute(select(Contest).where(Contest.status != "Done"))
    contests = result.scalars().all()
    return {contest.id: contest.name for contest in contests}


@app.get("/api/contests/{contest_id}", response_model=ContestOut)
async def get_contest(
    contest_id: int,
    user: User = Security(get_validated_user),
    session: AsyncSession = Depends(get_db_session),
):
    result = await session.execute(
        select(Contest)
        .options(joinedload(Contest.data_sources), joinedload(Contest.questions))
        .where(Contest.id == contest_id)
    )
    contest = result.scalars().first()
    if contest is None:
        raise HTTPException(status_code=404, detail="Contest not found")

    result = ContestOut(
        id=contest.id,
        name=contest.name,
        questions=[question.id for question in contest.questions],
        description=contest.description,
        start_at=contest.start_at,
        end_at=contest.end_at,
        data_sources=[
            DataSourcePayload(
                path=data_source.path,
                type=data_source.type,
                description=data_source.description,
            )
            for data_source in contest.data_sources
        ],
    )

    new_record = ContestFirstDownloaded(user_id=user.id, contest_id=contest.id)
    session.add(new_record)
    try:
        await session.commit()
    finally:
        return result


@app.get("/api/questions/{question_id}", response_model=QuestionOut)
async def get_question(
    question_id: int,
    user: User = Security(get_validated_user),
    session: AsyncSession = Depends(get_db_session),
):
    result = await session.execute(
        select(Question).options(joinedload(Question.answer_options)).where(Question.id == question_id)
    )
    question = result.scalars().first()
    if question is None:
        raise HTTPException(status_code=404, detail="Question not found")

    questionOut = QuestionOut(
        id=question.id,
        query=question.query,
        options=[option.option_text for option in question.answer_options],
        description=question.description,
    )
    new_record = QuestionFirstDownloaded(user_id=user.id, question_id=question.id)
    session.add(new_record)
    try:
        await session.commit()
    finally:
        return questionOut


@app.get("/api/contests/{contest_id}/questions", response_model=List[QuestionOut])
async def get_questions(
    contest_id: int,
    user: User = Security(get_validated_user),
    session: AsyncSession = Depends(get_db_session),
):
    results = await session.execute(select(Question).where(Contest.id == contest_id))
    questions = results.scalars().all()
    if questions is None:
        raise HTTPException(status_code=404, detail="Question not found")

    return questions


@app.post("/api/questions/{question_id}", response_model=UserAnswerOut)
async def submit_answer(
    question_id: int,
    answer_submission: UserAnswerSubmission = Body(...),
    user: User = Security(get_validated_user),
    session: AsyncSession = Depends(get_db_session),
):
    """答え合わせの処理
    ユーザーの提出回答と正解を照合して正しいかどうか、かかった時間をデータベースに保存してメインページに表示"""
    # Fetch the question from the database
    result = await session.execute(select(Question).where(Question.id == question_id))
    question = result.scalars().first()
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")
    user_id = user.id
    contest_id = question.contest_id

    # Score the answer
    uas = await UserAnswerScorer.create(user_id, question_id, session)
    score = uas.get_score(answer_submission.answer)
    is_correct = uas.is_correct(score)
    time_taken_ms = uas.get_time()

    # Create a new answer record
    new_answer = UserAnswer(
        answer=answer_submission.answer,
        user_id=user_id,
        question_id=question_id,
        is_correct=is_correct,
        similarity=score,
        time_taken_ms=time_taken_ms,
    )
    session.add(new_answer)
    await session.commit()

    # check if all questions are answered
    result = await session.execute(
        select(UserAnswer).options(joinedload(UserAnswer.question)).where(UserAnswer.user_id == user_id)
    )
    answers = result.scalars().all()
    result = await session.execute(select(Question).where(Question.contest_id == contest_id))
    questions = result.scalars().all()
    all_questions = {question.id for question in questions}
    answered_questions = {answer.question_id for answer in answers}
    sum_time = sum([answer.time_taken_ms for answer in answers])
    number_of_correct_answers = sum([answer.is_correct for answer in answers])
    print("contest_id: ", contest_id)
    print("all_questions: ", all_questions)
    print("answered_questions: ", answered_questions)
    answers_remain = list(all_questions - answered_questions)
    # await session.commit()
    if not answers_remain:
        try:
            new_result = ContestResult(
                user_id=user_id,
                contest_id=contest_id,
                number_of_correct_answers=number_of_correct_answers,
                time_ms=sum_time,
            )
            session.add(new_result)
            await session.commit()
        except Exception:
            pass

    return UserAnswerOut(
        question_id=question_id,
        answer=answer_submission.answer,
        is_correct=is_correct,
        similarity=score,
        time_taken_ms=time_taken_ms,
        not_answered_question_ids=answers_remain,
    )


@app.get("/signup")
async def signup_page():
    return FileResponse("./html/signup.html", media_type="text/html")


@app.post("/signup")
async def signup(
    json_data: dict,
    session: AsyncSession = Depends(get_db_session),
):
    username = json_data["username"]
    email = json_data["email"]
    password = json_data["password"]
    result = await session.execute(select(User).where((User.name == username) | (User.email == email)))
    existing_user = result.scalars().first()

    if existing_user:
        if existing_user.name == username:
            raise HTTPException(status_code=400, detail="Username already registered")
        elif existing_user.email == email:
            raise HTTPException(status_code=400, detail="Email already registered")

    temp_result = await session.execute(
        select(TemporaryUser).where((TemporaryUser.name == username) | (TemporaryUser.email == email))
    )
    existing_temp_user = temp_result.scalars().first()

    if existing_temp_user:
        if existing_temp_user.name == username:
            raise HTTPException(status_code=400, detail="Username already temporarily registered")
        elif existing_temp_user.email == email:
            raise HTTPException(status_code=400, detail="Email already temporarily registered")

    hashed_password = get_password_hash(password)
    new_user = TemporaryUser(
        id=str(uuid.uuid4()),
        name=username,
        email=email,
        password=hashed_password,
    )
    session.add(new_user)
    await session.commit()
    return {"message": "Temporarily registered. Please check out your email registered."}


@app.get("/authenticate/{user_id}")
async def authenticate_user_by_email(user_id: str, session: AsyncSession = Depends(get_db_session)):
    result = await session.execute(select(TemporaryUser).where(TemporaryUser.id == user_id))
    tmp_user = result.scalars().first()
    if not tmp_user:
        raise HTTPException(status_code=404, detail="User not found")
    new_api_key = generate_api_key()
    new_user = User(
        name=tmp_user.name,
        email=tmp_user.email,
        password=tmp_user.password,
        api_key=new_api_key,
    )
    session.add(new_user)
    await session.delete(tmp_user)
    await session.commit()
    return {"api_key": new_user.api_key}


@app.get("/login")
async def login_page(request: Request, session: AsyncSession = Depends(get_db_session)):
    try:
        token = fetch_access_token_from_cookie_header(request)
        user = await get_current_user(token, session)
        return RedirectResponse(url="/dashboard", status_code=303)
    except Exception:
        return FileResponse("./html/login.html", media_type="text/html")


@app.post("/login")
async def login(
    response: Response,
    json_data: dict,
    session: AsyncSession = Depends(get_db_session),
):
    email = json_data["email"]
    password = json_data["password"]
    user = await authenticate_user(email, password, session)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if not verify_password(password, user.password):
        raise HTTPException(status_code=403, detail="Invalid password")

    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=timedelta(minutes=jwt_settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )

    response = RedirectResponse(url="/dashboard", status_code=status.HTTP_303_SEE_OTHER)
    response.set_cookie(
        key="access_token",
        value=f"{access_token}",
        httponly=True,
        max_age=jwt_settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        expires=jwt_settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        samesite="lax",
    )
    return response


@app.post("/logout")
async def logout():
    response = RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)
    response.delete_cookie(key="access_token")
    return response


async def get_current_user(
    token: str,
    session: AsyncSession = Depends(get_db_session),
) -> User:
    credentials_exception = HTTPException(
        status_code=401,
        detail="認証情報を検証できませんでした",
        headers={"cookie": ""},
    )
    try:
        payload = jwt.decode(token, jwt_settings.SECRET_KEY, algorithms=[jwt_settings.ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    result = await session.execute(select(User).where(User.email == email))
    user = result.scalars().first()
    if user is None:
        raise credentials_exception
    return user


@app.get("/dashboard")
async def dashboard_page(request: Request, session: AsyncSession = Depends(get_db_session)):
    token = fetch_access_token_from_cookie_header(request)
    await get_current_user(token, session)
    return FileResponse("./html/dashboard.html", media_type="text/html")


@app.get("/results")
async def get_results_page(request: Request, session: AsyncSession = Depends(get_db_session)):
    result = await session.execute(
        select(Contest)
        # .where(Contest.status == ContestStatus.Done)
    )
    contests = result.scalars().all()
    return templates.TemplateResponse("results.html", {"request": request, "contests": contests})


# @app.post("/token")
# async def login_for_access_token(email: str, password: str):
#     user = authenticate_user(email, password)  # Your authentication logic here
#     if not user:
#         raise HTTPException(status_code=401, detail="Incorrect username or password")

#     access_token = create_access_token(data={"sub": user.email})
#     return {"access_token": access_token, "token_type": "bearer"}


@app.get("/results/{contest_id}")
async def get_result_page(request: Request, contest_id: int, session: AsyncSession = Depends(get_db_session)):
    result = await session.execute(select(Contest).where(Contest.id == contest_id))
    contest = result.scalars().first()
    if not contest:
        raise HTTPException(status_code=404, detail="Contest not found")
    contest_name = contest.name

    result = await session.execute(
        select(ContestResult)
        .options(joinedload(ContestResult.user))
        .where(ContestResult.contest_id == contest_id)
        .order_by(desc(ContestResult.number_of_correct_answers))
    )
    contest_results = result.scalars().all()

    response = []
    for idx, contest_result in enumerate(contest_results):
        username = contest_result.user.name
        response.append(
            {
                "ranking": idx + 1,
                "user_name": username,
                "number_of_correct_answers": contest_result.number_of_correct_answers,
                "total_score": 100,
                "total_time_ms": format_millisec(contest_result.time_ms),
            }
        )

    return templates.TemplateResponse(
        "result.html",
        {"request": request, "contest_name": contest_name, "response": response},
    )


@app.get("/results/{contest_id}/details")
async def get_result_details_page(request: Request, contest_id: int, session: AsyncSession = Depends(get_db_session)):
    result = await session.execute(
        select(UserAnswer)
        .options(joinedload(UserAnswer.user), joinedload(UserAnswer.question))
        .where(Contest.id == contest_id)
    )
    user_answers = result.scalars().all()

    result = await session.execute(select(Contest).where(Contest.id == contest_id))
    contest = result.scalars().first()
    if not contest:
        raise HTTPException(status_code=404, detail="Contest not found")
    contest_name = contest.name

    response = []
    for answer in user_answers:
        username = answer.user.name
        query = answer.question.query
        response.append(
            {
                "user_name": username,
                "query": query,
                "user_answer": answer.answer,
                "similarity": answer.similarity,
                "pass_fail": "Pass" if answer.is_correct else "Fail",
                "time": format_millisec(answer.time_taken_ms),
            }
        )

    return templates.TemplateResponse(
        "result.html",
        {"request": request, "contest_name": contest_name, "response": response},
    )


@app.get("/register_contest")
async def register_contest_page():
    return FileResponse("./html/register_contest.html", media_type="text/html")


@app.post("/register_contest")
async def register_contest(
    contest_submission: ContestIn = Body(...),
    session: AsyncSession = Depends(get_db_session),
):
    # Contest, DataSource, Question, AnswerEmbedding, AnswerOption テーブルに格納
    new_contest = Contest(
        name=contest_submission.contest_info.name,
        description=contest_submission.contest_info.description,
        number_of_questions=len(contest_submission.query_answers),
    )
    session.add(new_contest)
    await session.flush()

    for data_source in contest_submission.data_sources:
        new_data_source = DataSource(
            contest_id=new_contest.id,
            path=data_source.path,
            type=data_source.type,
            description=data_source.description,
        )
        session.add(new_data_source)
        await session.flush()

    for qa in contest_submission.query_answers:
        new_qa = Question(
            contest_id=new_contest.id,
            query=qa.query,
            number_of_options=len(qa.options),
            description=qa.description,
        )
        session.add(new_qa)
        await session.flush()

        emb = OpenAIClient().get_embedding(qa.query, qa.answer)
        new_answer = AnswerEmbedding(question_id=new_qa.id, answer=qa.answer, text_embedding_3_small=emb)
        session.add(new_answer)
        await session.flush()

        for option in qa.options:
            new_option = AnswerOption(question_id=new_qa.id, option_text=option)
            session.add(new_option)
            await session.flush()

    await session.commit()
    # [疑問]何を返せばいいのか
    # return {"status": "success", "contest_id": new_contest.id}
