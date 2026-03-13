"""백엔드 설정: 환경변수, DB 경로, RAG 파이프라인 경로."""

import os
import sys
from pathlib import Path

from dotenv import load_dotenv

# 프로젝트 경로
BACKEND_DIR = Path(__file__).resolve().parent
PROJECT_DIR = BACKEND_DIR.parent

# 기존 RAG 프로젝트의 .env 로드
RAG_PROJECT_DIR = BACKEND_DIR.parent.parent / "lapaz-crawl-20260305170615"
_env_path = RAG_PROJECT_DIR / ".env"
if _env_path.exists():
    load_dotenv(_env_path)

# RAG 파이프라인 경로를 sys.path에 추가
RAG_SRC_DIR = str(RAG_PROJECT_DIR / "src")
if RAG_SRC_DIR not in sys.path:
    sys.path.insert(0, RAG_SRC_DIR)

# SQLite DB 경로
DB_DIR = BACKEND_DIR / "data"
DB_DIR.mkdir(exist_ok=True)
DB_PATH = str(DB_DIR / "questions.db")

# CORS 허용 origins
CORS_ORIGINS: list[str] = [
    "http://localhost:3000",
]
