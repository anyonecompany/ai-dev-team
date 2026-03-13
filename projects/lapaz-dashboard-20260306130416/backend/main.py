"""FastAPI 애플리케이션 엔트리포인트."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

import config
from routers import ask, match, questions
from services.question_service import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    """앱 시작 시 DB를 초기화한다."""
    await init_db()
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
