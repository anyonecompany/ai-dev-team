"""애플리케이션 설정.

환경변수를 pydantic-settings로 관리합니다.
"""

import os
from typing import List
from dotenv import dotenv_values

# .env 파일 명시적 로드
env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")
if os.path.exists(env_path):
    env_values = dotenv_values(env_path)
    os.environ.update(env_values)

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """환경 설정 클래스."""

    # 서버 설정
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    DEBUG: bool = True

    # CORS
    CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://localhost:5174",
        "http://localhost:3000",
    ]

    # Supabase
    SUPABASE_URL: str = ""
    SUPABASE_KEY: str = ""

    # 프로젝트 설정
    PROJECT_NAME: str = "__PROJECT_NAME__"

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
