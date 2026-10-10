import os
from pydantic import BaseModel

class Settings(BaseModel):
    PROJECT_NAME: str = "AI Consumer Research Simulator"
    API_V1_STR: str = "/api"
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    DEFAULT_GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-3.8-flash")
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./consumer_research.db")
    CORS_ORIGINS: list[str] = ["*"]
    
    # Google Cloud 実行環境情報
    GOOGLE_CLOUD_PROJECT: str = os.getenv("GOOGLE_CLOUD_PROJECT", os.getenv("GCP_PROJECT", "stable-century-479407-m7"))
    IS_CLOUD_RUN: bool = bool(os.getenv("K_SERVICE", ""))
    CLOUD_RUN_SERVICE: str = os.getenv("K_SERVICE", "local-dev")
    CLOUD_RUN_REVISION: str = os.getenv("K_REVISION", "rev-local")
    RESTRICT_PUBLIC_DATA_MODIFICATION: bool = bool(os.getenv("RESTRICT_PUBLIC_DATA_MODIFICATION", "") or os.getenv("K_SERVICE", ""))

settings = Settings()

def has_gemini_api_key() -> bool:
    return bool(settings.GEMINI_API_KEY and settings.GEMINI_API_KEY.strip())
