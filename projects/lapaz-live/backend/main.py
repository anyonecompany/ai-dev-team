"""FastAPI 애플리케이션 엔트리포인트."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

import config
from routers import ask, match, questions
from services.question_service import init_db

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
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 라우터 등록
app.include_router(ask.router, prefix="/api")
app.include_router(questions.router, prefix="/api")
app.include_router(match.router, prefix="/api")
