"""대시보드 라우터.

대시보드 데이터 API.
"""

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from datetime import datetime, timedelta
import random

from core.logging import get_logger

router = APIRouter(prefix="/dashboard", tags=["dashboard"])
logger = get_logger("dashboard")


class DashboardStats(BaseModel):
    """대시보드 통계."""
    total_users: int
    active_users: int
    total_revenue: float
    growth_rate: float


class ChartData(BaseModel):
    """차트 데이터."""
    labels: list[str]
    values: list[float]


@router.get("/stats", response_model=DashboardStats)
async def get_stats():
    """대시보드 통계 조회.

    TODO: 실제 데이터 조회 구현
    """
    # 샘플 데이터
    return DashboardStats(
        total_users=1234,
        active_users=567,
        total_revenue=12345.67,
        growth_rate=15.3,
    )


@router.get("/chart/users")
async def get_user_chart() -> ChartData:
    """사용자 증가 차트 데이터.

    최근 7일간 일별 사용자 수.
    TODO: 실제 데이터 조회 구현
    """
    today = datetime.now()
    labels = [(today - timedelta(days=i)).strftime("%m/%d") for i in range(6, -1, -1)]
    values = [random.randint(50, 150) for _ in range(7)]

    return ChartData(labels=labels, values=values)


@router.get("/chart/revenue")
async def get_revenue_chart() -> ChartData:
    """매출 차트 데이터.

    최근 7일간 일별 매출.
    TODO: 실제 데이터 조회 구현
    """
    today = datetime.now()
    labels = [(today - timedelta(days=i)).strftime("%m/%d") for i in range(6, -1, -1)]
    values = [random.uniform(500, 2000) for _ in range(7)]

    return ChartData(labels=labels, values=[round(v, 2) for v in values])


@router.get("/recent-activity")
async def get_recent_activity():
    """최근 활동 조회.

    TODO: 실제 데이터 조회 구현
    """
    # 샘플 데이터
    return {
        "activities": [
            {"type": "signup", "user": "user1@example.com", "time": "5분 전"},
            {"type": "purchase", "user": "user2@example.com", "time": "15분 전"},
            {"type": "login", "user": "user3@example.com", "time": "30분 전"},
            {"type": "signup", "user": "user4@example.com", "time": "1시간 전"},
            {"type": "purchase", "user": "user5@example.com", "time": "2시간 전"},
        ]
    }
