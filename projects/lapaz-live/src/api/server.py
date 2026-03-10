"""La Paz RAG API 테스트 서버.

실행:
    cd /Users/danghyeonsong/ai-dev-team/projects/lapaz-live
    python -m uvicorn src.api.server:app --reload --port 8000

POST /ask {"question": "브루노가 왜 내려와?", "match_context": null}
GET  /health
"""

import logging
import os
from contextlib import asynccontextmanager
from typing import Any

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# .env 로드 (프로젝트 루트)
load_dotenv(os.path.join(os.path.dirname(__file__), "..", "..", ".env"))

logger = logging.getLogger(__name__)


# --- Request / Response 스키마 ---

class AskRequest(BaseModel):
    question: str
    match_context: dict[str, Any] | None = None


class AskResponse(BaseModel):
    question: str
    category: str
    keywords: list[str]
    confidence: float
    answer: str
    source_docs: list[int]
    generation_time_ms: int
    total_time_ms: int


# --- Lifespan (환경변수 사전 검증) ---

@asynccontextmanager
async def lifespan(app: FastAPI):
    missing = [
        k for k in ("SUPABASE_URL", "SUPABASE_SERVICE_KEY", "ANTHROPIC_API_KEY")
        if not os.getenv(k)
    ]
    if missing:
        logger.warning("누락된 환경변수: %s", ", ".join(missing))

    if not os.getenv("OPENAI_API_KEY"):
        logger.warning("OPENAI_API_KEY 미설정 — 임베딩 검색이 실패할 수 있습니다.")

    logger.info("La Paz RAG API 시작")
    yield
    logger.info("La Paz RAG API 종료")


# --- FastAPI 앱 ---

app = FastAPI(
    title="La Paz RAG API",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- 엔드포인트 ---

@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/ask", response_model=AskResponse)
async def ask_endpoint(req: AskRequest):
    from src.rag.pipeline import ask

    match_context = ""
    if req.match_context:
        match_context = str(req.match_context)

    try:
        result = await ask(question=req.question, match_context=match_context)
    except Exception as exc:
        logger.exception("RAG 파이프라인 오류")
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    return result
