"""error_logs 테이블에 에러 로그를 저장하는 서비스.

이 서비스의 핵심 원칙: **절대로 원래 에러 응답 흐름을 막지 않는다.**
log_error() 자체가 실패해도 조용히 로그만 남기고 넘어간다.
"""

import asyncio
import logging
import os
from concurrent.futures import ThreadPoolExecutor
from typing import Optional

from supabase import create_client

logger = logging.getLogger(__name__)

_executor = ThreadPoolExecutor(max_workers=2)

# 에러 타입 매핑 (예외 클래스명 → DB에 저장할 값)
ERROR_TYPE_MAP: dict[str, str] = {
    "RateLimitError": "rate_limit",
    "PipelineTimeoutError": "timeout",
    "DataSourceError": "data_source",
    "GenerationError": "generation",
}


def _get_supabase_client():
    """Supabase 클라이언트를 생성한다.

    환경변수 미설정 시 None을 반환한다.
    """
    url = os.environ.get("SUPABASE_URL", "")
    key = os.environ.get("SUPABASE_SERVICE_KEY", "")
    if not url or not key:
        return None
    return create_client(url, key)


def _insert_error_log(
    request_id: str,
    question: str,
    error_type: str,
    pipeline_stage: str,
    error_message: str,
    latency_ms: Optional[int] = None,
    match_id: Optional[str] = None,
) -> None:
    """동기 함수: Supabase에 에러 로그를 insert한다."""
    client = _get_supabase_client()
    if client is None:
        logger.warning("Supabase 미설정 — 에러 로그 저장 건너뜀")
        return

    row = {
        "request_id": request_id,
        "question": question[:2000],  # 질문 길이 제한
        "error_type": error_type,
        "pipeline_stage": pipeline_stage,
        "error_message": error_message[:5000],  # 에러 메시지 길이 제한
    }
    if latency_ms is not None:
        row["latency_ms"] = latency_ms
    if match_id is not None:
        row["match_id"] = match_id

    client.table("error_logs").insert(row).execute()


async def log_error(
    request_id: str,
    question: str,
    error_type: str,
    pipeline_stage: str,
    error_message: str,
    latency_ms: Optional[int] = None,
    match_id: Optional[str] = None,
) -> None:
    """에러 로그를 Supabase error_logs 테이블에 비동기로 저장한다.

    이 함수는 실패해도 예외를 발생시키지 않는다.
    원래 에러 응답 흐름을 절대 막지 않기 위해 try/except로 감싼다.

    Args:
        request_id: 요청 추적 ID.
        question: 사용자 질문 (원문).
        error_type: 에러 유형 (rate_limit / timeout / data_source / generation / unknown).
        pipeline_stage: 에러 발생 파이프라인 단계.
        error_message: 에러 메시지 (str(exc)).
        latency_ms: 에러 발생까지의 응답 시간 (밀리초).
        match_id: 경기 ID (있을 경우).
    """
    try:
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            _executor,
            _insert_error_log,
            request_id,
            question,
            error_type,
            pipeline_stage,
            error_message,
            latency_ms,
            match_id,
        )
    except Exception as e:
        # 에러 로그 저장 실패 — 조용히 로그만 남김
        logger.warning("에러 로그 Supabase 저장 실패 (무시): %s", e)


def resolve_error_type(exc: Exception) -> str:
    """예외 클래스명에서 error_type 문자열을 반환한다."""
    return ERROR_TYPE_MAP.get(type(exc).__name__, "unknown")


async def get_error_summary(hours: int = 24) -> dict:
    """최근 N시간 에러 유형별 카운트를 조회한다.

    Args:
        hours: 조회 범위 (시간, 기본 24).

    Returns:
        {"total": int, "by_type": {"rate_limit": n, ...}, "by_stage": {"router": n, ...}}
    """
    try:
        client = _get_supabase_client()
        if client is None:
            return {"total": 0, "by_type": {}, "by_stage": {}, "error": "Supabase 미설정"}

        loop = asyncio.get_event_loop()
        # created_at 기준 최근 N시간 필터링
        from datetime import datetime, timedelta, timezone
        since = (datetime.now(timezone.utc) - timedelta(hours=hours)).isoformat()

        result = await loop.run_in_executor(
            _executor,
            lambda: client.table("error_logs")
                .select("error_type, pipeline_stage")
                .gte("created_at", since)
                .execute(),
        )

        rows = result.data or []
        by_type: dict[str, int] = {}
        by_stage: dict[str, int] = {}
        for row in rows:
            et = row.get("error_type", "unknown")
            ps = row.get("pipeline_stage", "unknown")
            by_type[et] = by_type.get(et, 0) + 1
            by_stage[ps] = by_stage.get(ps, 0) + 1

        return {
            "total": len(rows),
            "by_type": by_type,
            "by_stage": by_stage,
            "period_hours": hours,
        }
    except Exception as e:
        logger.warning("에러 요약 조회 실패: %s", e)
        return {"total": 0, "by_type": {}, "by_stage": {}, "error": str(e)[:200]}
