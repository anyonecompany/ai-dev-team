"""환경변수 및 Notion DB ID 설정."""

import os
from pathlib import Path

from dotenv import load_dotenv

# .env 파일 로드 (프로젝트 루트 기준)
_env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(_env_path)

NOTION_API_KEY: str = os.environ["NOTION_API_KEY"]
TASK_DB_ID: str = os.environ["NOTION_TASK_DB_ID"]
PROJECT_DB_ID: str = os.environ["NOTION_PROJECT_DB_ID"]
DECISION_DB_ID: str = os.environ["NOTION_DECISION_DB_ID"]
TECHREF_DB_ID: str = os.environ["NOTION_TECHREF_DB_ID"]
