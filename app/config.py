from pydantic_settings import BaseSettings


class JWTSettings(BaseSettings):
    SECRET_KEY: str = "Hello FastAPI"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30


jwt_settings = JWTSettings()
