"""Vercel serverless entrypoint for FastAPI."""

import sys
from pathlib import Path

# backend/를 먼저 추가 (backend/config.py가 src/config.py보다 우선되어야 함)
_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_root / "src"))
sys.path.insert(0, str(_root / "backend"))

from main import app  # noqa: E402, F401
