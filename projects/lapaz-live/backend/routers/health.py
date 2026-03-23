"""헬스체크 라우터: 주요 의존성 상태를 점검하여 반환한다."""

from __future__ import annotations

import asyncio
import logging
import os
import time
from typing import Any

import httpx
from fastapi import APIRouter

router = APIRouter(tags=["health"])

logger = logging.getLogger(__name__)

_PING_TIMEOUT = 2.0  # 각 서비스 ping 타임아웃 (초)


def _status_from_latency(latency_ms: float) -> str:
    """응답 시간 기반 상태 판정.

    Args:
        latency_ms: 응답 시간 (밀리초).

    Returns:
        "ok" (< 1000ms), "degraded" (< 2000ms), 또는 "down" (타임아웃).
    """
    if latency_ms < 1000:
        return "ok"
    return "degraded"


async def _ping_gemini() -> dict[str, Any]:
    """Gemini API ping: 모델 목록 조회로 연결 확인."""
    start = time.monotonic()
    try:
        from google import genai

        api_key = os.getenv("GEMINI_API_KEY")
        client = genai.Client(api_key=api_key)

        # 모델 목록 조회 (가장 가벼운 호출)
        result = await asyncio.wait_for(
            asyncio.get_event_loop().run_in_executor(
                None, lambda: list(client.models.list())
            ),
            timeout=_PING_TIMEOUT,
        )
        latency_ms = round((time.monotonic() - start) * 1000)
        return {"status": _status_from_latency(latency_ms), "latency_ms": latency_ms}
    except asyncio.TimeoutError:
        return {"status": "down", "latency_ms": None, "error": "timeout"}
    except Exception as e:
        latency_ms = round((time.monotonic() - start) * 1000)
        logger.warning("Gemini ping 실패: %s", e)
        return {"status": "down", "latency_ms": latency_ms, "error": str(e)[:100]}


async def _ping_voyage() -> dict[str, Any]:
    """Voyage AI ping: 짧은 텍스트 임베딩 호출로 연결 확인."""
    start = time.monotonic()
    try:
        import voyageai

        api_key = os.environ.get("VOYAGE_API_KEY", "")
        client = voyageai.Client(api_key=api_key)

        result = await asyncio.wait_for(
            asyncio.get_event_loop().run_in_executor(
                None,
                lambda: client.embed(["ping"], model="voyage-3-lite"),
            ),
            timeout=_PING_TIMEOUT,
        )
        latency_ms = round((time.monotonic() - start) * 1000)
        return {"status": _status_from_latency(latency_ms), "latency_ms": latency_ms}
    except asyncio.TimeoutError:
        return {"status": "down", "latency_ms": None, "error": "timeout"}
    except Exception as e:
        latency_ms = round((time.monotonic() - start) * 1000)
        logger.warning("Voyage ping 실패: %s", e)
        return {"status": "down", "latency_ms": latency_ms, "error": str(e)[:100]}


async def _ping_supabase() -> dict[str, Any]:
    """Supabase ping: 간단한 쿼리로 연결 확인."""
    start = time.monotonic()
    try:
        from supabase import create_client

        url = os.environ.get("SUPABASE_URL", "")
        key = os.environ.get("SUPABASE_SERVICE_KEY", "")
        if not url or not key:
            return {"status": "down", "latency_ms": None, "error": "credentials not configured"}

        client = create_client(url, key)

        # 가장 가벼운 쿼리: 테이블에서 1행만 조회
        result = await asyncio.wait_for(
            asyncio.get_event_loop().run_in_executor(
                None,
                lambda: client.table("documents").select("id").limit(1).execute(),
            ),
            timeout=_PING_TIMEOUT,
        )
        latency_ms = round((time.monotonic() - start) * 1000)
        return {"status": _status_from_latency(latency_ms), "latency_ms": latency_ms}
    except asyncio.TimeoutError:
        return {"status": "down", "latency_ms": None, "error": "timeout"}
    except Exception as e:
        latency_ms = round((time.monotonic() - start) * 1000)
        logger.warning("Supabase ping 실패: %s", e)
        return {"status": "down", "latency_ms": latency_ms, "error": str(e)[:100]}


async def _ping_football_data() -> dict[str, Any]:
    """football-data.org ping: competitions 엔드포인트 호출로 연결 확인."""
    start = time.monotonic()
    try:
        headers: dict[str, str] = {}
        token = os.getenv("FOOTBALL_DATA_TOKEN", "")
        if token:
            headers["X-Auth-Token"] = token

        async with httpx.AsyncClient(
            timeout=httpx.Timeout(_PING_TIMEOUT),
            headers=headers,
        ) as client:
            resp = await client.get("https://api.football-data.org/v4/competitions/PL")
            resp.raise_for_status()

        latency_ms = round((time.monotonic() - start) * 1000)
        return {"status": _status_from_latency(latency_ms), "latency_ms": latency_ms}
    except (httpx.TimeoutException, asyncio.TimeoutError):
        return {"status": "down", "latency_ms": None, "error": "timeout"}
    except Exception as e:
        latency_ms = round((time.monotonic() - start) * 1000)
        logger.warning("Football Data ping 실패: %s", e)
        return {"status": "down", "latency_ms": latency_ms, "error": str(e)[:100]}


@router.get("/health/data-sources")
async def health_data_sources() -> dict[str, Any]:
    """주요 외부 의존성 상태를 병렬로 점검하여 반환한다.

    각 서비스에 2초 타임아웃을 적용하며, 전체를 asyncio.gather로 병렬 실행한다.

    Returns:
        각 서비스의 status ("ok" | "degraded" | "down"), latency_ms, error 정보.
    """
    gemini_task = _ping_gemini()
    voyage_task = _ping_voyage()
    supabase_task = _ping_supabase()
    football_task = _ping_football_data()

    results = await asyncio.gather(
        gemini_task, voyage_task, supabase_task, football_task,
        return_exceptions=True,
    )

    def _safe_result(result: Any, name: str) -> dict[str, Any]:
        """gather에서 예외가 반환된 경우 안전하게 처리."""
        if isinstance(result, Exception):
            logger.warning("%s health check 예외: %s", name, result)
            return {"status": "down", "latency_ms": None, "error": str(result)[:100]}
        return result

    return {
        "gemini": _safe_result(results[0], "Gemini"),
        "voyage": _safe_result(results[1], "Voyage"),
        "supabase": _safe_result(results[2], "Supabase"),
        "football_data": _safe_result(results[3], "Football Data"),
    }
