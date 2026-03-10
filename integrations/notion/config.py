"""Notion + Slack 환경변수 로드."""

import os
from pathlib import Path

from dotenv import load_dotenv

# 루트 .env 로드
_root = Path(__file__).resolve().parent.parent.parent
load_dotenv(_root / ".env")

NOTION_API_KEY: str = os.environ.get("NOTION_API_KEY", "")
TASK_DB_ID: str = os.environ.get("NOTION_TASK_DB_ID", "")
PROJECT_DB_ID: str = os.environ.get("NOTION_PROJECT_DB_ID", "")
DECISION_DB_ID: str = os.environ.get("NOTION_DECISION_DB_ID", "")
TECHREF_DB_ID: str = os.environ.get("NOTION_TECHREF_DB_ID", "")
SLACK_WEBHOOK_URL: str = os.environ.get("SLACK_WEBHOOK_URL", "")
