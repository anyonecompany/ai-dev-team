"""백엔드 설정: 환경변수, DB 경로, RAG 파이프라인 경로, 외부 API 설정."""

import os
import sys
from pathlib import Path

from dotenv import load_dotenv

# 프로젝트 경로
BACKEND_DIR = Path(__file__).resolve().parent
PROJECT_DIR = BACKEND_DIR.parent

# .env 로드 (통합 프로젝트 루트)
_env_path = PROJECT_DIR / ".env"
if _env_path.exists():
    load_dotenv(_env_path)

# RAG 파이프라인 경로를 sys.path에 추가 (같은 프로젝트 내 src/)
RAG_SRC_DIR = str(PROJECT_DIR / "src")
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

# --- football-data.org ---
FOOTBALL_DATA_TOKEN: str = os.getenv("FOOTBALL_DATA_TOKEN", "")
FOOTBALL_DATA_BASE: str = "https://api.football-data.org/v4"
MATCH_ID_FD: int = 538082  # 3/15 Man Utd vs Aston Villa
MANUTD_FD_ID: int = 66
VILLA_FD_ID: int = 58

# --- API-Football (라이브 이벤트 전용) ---
API_FOOTBALL_KEY: str = os.getenv("API_FOOTBALL_KEY", "")
API_FOOTBALL_BASE: str = "https://v3.football.api-sports.io"
