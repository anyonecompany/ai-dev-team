"""FastAPI 애플리케이션 엔트리포인트."""

import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

import config
from routers import ask, errors, health, match, questions
from services.question_service import init_db

# 구조화 JSON 로깅 초기화 (모든 로거에 적용)
from rag.logging_utils import setup_json_logging
setup_json_logging()

logger = logging.getLogger(__name__)


async def _warmup_data_cache() -> None:
    """서버 시작 시 football-data.org 데이터를 미리 캐시한다."""
    from services.football_data_service import get_match_preview
    try:
        preview = await get_match_preview(config.MANUTD_FD_ID, config.VILLA_FD_ID)
        teams = len(preview.get("standings", []))
        logger.info("데이터 캐시 워밍업 완료: %d팀 순위 로드", teams)
    except Exception as e:
        logger.warning("데이터 캐시 워밍업 실패 (서비스는 정상 시작): %s", e)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """앱 시작 시 DB 초기화 + 데이터 캐시 워밍업."""
    await init_db()
    if not os.getenv("VERCEL") and os.getenv("ENABLE_STARTUP_WARMUP", "1") == "1":
        await _warmup_data_cache()
    yield


app = FastAPI(
    title="La Paz Live Q&A Dashboard API",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.CORS_ORIGINS,
    allow_origin_regex=config.CORS_ORIGIN_REGEX,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health check (root-level for Fly.io / load-balancer probes)
@app.get("/health")
async def health_check() -> dict:
    """서비스 상태 확인용 엔드포인트."""
    return {"status": "ok"}


# 라우터 등록
app.include_router(ask.router, prefix="/api")
app.include_router(questions.router, prefix="/api")
app.include_router(match.router, prefix="/api")
app.include_router(errors.router, prefix="/api")
app.include_router(health.router)  # /health/data-sources (prefix 없이 루트에 등록)
