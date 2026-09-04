import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    APP_NAME: str = "VeerSense API"
    ENV: str = os.getenv("ENV", "development")

    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./veersense.db")

    JWT_SECRET: str = os.getenv("JWT_SECRET", "change-this-in-production-please")
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 12

    ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")
    CLAUDE_MODEL: str = os.getenv("CLAUDE_MODEL", "claude-sonnet-4-6")

    ALLOWED_ORIGINS: list = os.getenv("ALLOWED_ORIGINS", "*").split(",")

    MODEL_PATH: str = os.getenv("MODEL_PATH", "./ml/stress_model.pkl")


settings = Settings()