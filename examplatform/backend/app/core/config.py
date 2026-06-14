from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_NAME: str = "Secure Exam Platform"
    DATABASE_URL: str = "postgresql://exam_user:exam_pass@db:5432/exam_db"
    SECRET_KEY: str = "CHANGE_ME_IN_PRODUCTION_SECRET_KEY"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 8
    CORS_ORIGINS: list[str] = ["http://localhost:3000", "http://localhost:5173"]

    class Config:
        env_file = ".env"


settings = Settings()
