"""AI 브리핑 생성 서비스 — Gemini API 연동.

Gemini API 호출은 동기 I/O이므로 asyncio.to_thread()로 스레드 풀에서 실행하여
이벤트 루프 블로킹을 방지한다. 12초 타임아웃을 적용한다.

핵심 설계 원칙:
- API 응답은 항상 2초 이내 (캐시/mock에서 즉시 반환)
- Gemini API 호출은 백그라운드에서만 수행 (요청 시점이 아님)
- 스케줄러가 미리 생성한 브리핑을 캐시에서 반환
"""

from __future__ import annotations

import asyncio
import json
import logging
from datetime import datetime, timezone

from google import genai

from config import settings
from models.schemas import BriefingResponse, ETFChange
from prompts.briefing import MORNING_PROMPT, NIGHT_PROMPT

logger = logging.getLogger(__name__)

_GEMINI_MODEL = settings.GEMINI_MODEL
_GEMINI_TIMEOUT = 12  # Gemini API 호출 타임아웃 (초)

_gemini_client: genai.Client | None = None

# 마지막으로 성공한 브리핑 저장 (캐시 만료 후에도 반환 가능)
_last_morning_briefing: BriefingResponse | None = None
_last_night_briefing: BriefingResponse | None = None


def _get_gemini_client() -> genai.Client:
    """Return a lazily-initialised Gemini client."""
    global _gemini_client
    if _gemini_client is None:
        _gemini_client = genai.Client(api_key=settings.GEMINI_API_KEY)
    return _gemini_client


def _call_gemini_sync(prompt: str) -> dict | None:
    """Gemini API 동기 호출 + JSON 파싱 (스레드 풀에서 실행).

    Args:
        prompt: The formatted prompt to send to Gemini.

    Returns:
        Parsed JSON dict on success, None on failure.
    """
    try:
        client = _get_gemini_client()
        response = client.models.generate_content(
            model=_GEMINI_MODEL,
            contents=prompt,
        )
        text = response.text or ""
        # Extract JSON from response
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0]
        elif "```" in text:
            text = text.split("```")[1].split("```")[0]
        return json.loads(text.strip())
    except Exception as e:
        logger.error("Gemini API 호출 실패: %s", e)
        return None


async def _call_gemini(prompt: str) -> dict | None:
    """Gemini API 비동기 호출 — 스레드 풀 + 타임아웃.

    Args:
        prompt: The formatted prompt to send to Gemini.

    Returns:
        Parsed JSON dict on success, None on failure/timeout.
    """
    try:
        return await asyncio.wait_for(
            asyncio.to_thread(_call_gemini_sync, prompt),
            timeout=_GEMINI_TIMEOUT,
        )
    except asyncio.TimeoutError:
        logger.warning("Gemini API 타임아웃 (%ds)", _GEMINI_TIMEOUT)
        return None
    except Exception as e:
        logger.error("Gemini API 호출 실패: %s", e)
        return None


def _build_briefing_from_ai(data: dict, briefing_type: str) -> BriefingResponse:
    """Convert AI JSON output into a BriefingResponse.

    Args:
        data: Parsed JSON dict from AI.
        briefing_type: "morning" or "night".

    Returns:
        A validated BriefingResponse.
    """
    etf_changes = [
        ETFChange(
            ticker=c.get("ticker", ""),
            change_pct=c.get("change_pct", 0.0),
            direction=c.get("direction", "flat"),
            cause=c.get("cause", ""),
        )
        for c in data.get("etf_changes", [])
    ]

    # Morning uses key_events, night uses checkpoints
    checkpoints: list[str] = []
    if briefing_type == "morning":
        checkpoints = data.get("key_events", [])
    else:
        raw_checkpoints = data.get("checkpoints", [])
        for cp in raw_checkpoints:
            if isinstance(cp, dict):
                event = cp.get("event", "")
                time_ = cp.get("time", "")
                impact = cp.get("impact", "")
                checkpoints.append(f"{time_} — {event}: {impact}" if time_ else f"{event}: {impact}")
            else:
                checkpoints.append(str(cp))

    return BriefingResponse(
        type=briefing_type,
        title=data.get("title", f"{'모닝' if briefing_type == 'morning' else '나이트'} 브리핑"),
        summary=data.get("summary", ""),
        etf_changes=etf_changes,
        checkpoints=checkpoints,
        generated_at=datetime.now(timezone.utc).isoformat(),
    )


# ──────────────────────────────────────────────
# Mock briefing data (fallback)
# ──────────────────────────────────────────────

_MOCK_MORNING = BriefingResponse(
    type="morning",
    is_mock=True,
    title="3월 10일 모닝 브리핑",
    summary="FOMC 금리 동결 이후 기술주 반등세가 이어지고 있습니다. NVIDIA 실적 호조로 반도체 섹터 강세, 배당주는 보합세를 유지하고 있습니다.",
    etf_changes=[
        ETFChange(ticker="QQQ", change_pct=1.2, direction="up", cause="FOMC 금리 동결 + 기술주 반등"),
        ETFChange(ticker="VOO", change_pct=0.8, direction="up", cause="S&P 500 전반적 상승 흐름"),
        ETFChange(ticker="SCHD", change_pct=-0.3, direction="down", cause="성장주 대비 배당주 자금 이탈"),
        ETFChange(ticker="SOXL", change_pct=3.5, direction="up", cause="NVIDIA 실적 기대감 반영"),
        ETFChange(ticker="ARKK", change_pct=1.8, direction="up", cause="금리 하락 기대 + Tesla 매수세"),
        ETFChange(ticker="TLT", change_pct=0.5, direction="up", cause="국채 금리 하락으로 채권 가격 상승"),
    ],
    checkpoints=[
        "NVIDIA 실적 발표 후 시간외 거래 반응 확인",
        "FOMC 의사록 세부 내용 분석 필요",
        "유가 $85 돌파에 따른 에너지 섹터 모멘텀 체크",
    ],
    generated_at=datetime.now(timezone.utc).isoformat(),
)

_MOCK_NIGHT = BriefingResponse(
    type="night",
    is_mock=True,
    title="3월 10일 나이트 체크포인트",
    summary="오늘 하루 기술주 중심 강세 마감. 야간에 발표될 3가지 이벤트에 주목하세요.",
    etf_changes=[
        ETFChange(ticker="QQQ", change_pct=1.5, direction="up", cause="기술주 매수세 지속"),
        ETFChange(ticker="VOO", change_pct=0.9, direction="up", cause="S&P 500 +0.9% 마감"),
        ETFChange(ticker="SOXL", change_pct=4.2, direction="up", cause="반도체 섹터 랠리"),
    ],
    checkpoints=[
        "21:30 — 미국 소비자물가지수(CPI) 발표 예정",
        "22:00 — 연준 이사 월러 연설: 금리 전망 힌트 가능성",
        "익일 장전 — 유럽중앙은행(ECB) 금리 결정 영향 체크",
    ],
    generated_at=datetime.now(timezone.utc).isoformat(),
)

# Default ETF list for mock/fallback
_DEFAULT_ETFS = ["QQQ", "VOO", "SCHD", "SOXL", "ARKK", "TLT"]


class BriefingService:
    """Generates personalized ETF briefings using Gemini API with mock fallback."""

    async def get_morning_briefing(self, device_id: str) -> BriefingResponse:
        """Return morning briefing for the device.

        Never blocks on Gemini API calls. Returns in priority order:
        1. TTL cache (15분)
        2. Last successfully generated briefing (_last_morning_briefing)
        3. Mock data (즉시 반환)

        Args:
            device_id: The requesting device identifier.

        Returns:
            A BriefingResponse with morning briefing content.
        """
        global _last_morning_briefing
        from services.cache import get_cached, set_cached

        cache_key = "briefing_morning"
        cached = get_cached(cache_key)
        if cached is not None:
            logger.debug("Cache hit for %s", cache_key)
            return cached

        if _last_morning_briefing is not None:
            logger.info("TTL 캐시 만료, last_morning_briefing 반환 (stale)")
            set_cached(cache_key, _last_morning_briefing)
            return _last_morning_briefing

        logger.info("브리핑 미생성 — mock morning briefing 즉시 반환")
        return _MOCK_MORNING.model_copy(
            update={"generated_at": datetime.now(timezone.utc).isoformat()}
        )

    async def get_night_briefing(self, device_id: str) -> BriefingResponse:
        """Return night checkpoint for the device.

        Never blocks on Gemini API calls. Returns in priority order:
        1. TTL cache (15분)
        2. Last successfully generated briefing (_last_night_briefing)
        3. Mock data (즉시 반환)

        Args:
            device_id: The requesting device identifier.

        Returns:
            A BriefingResponse with night checkpoint content.
        """
        global _last_night_briefing
        from services.cache import get_cached, set_cached

        cache_key = "briefing_night"
        cached = get_cached(cache_key)
        if cached is not None:
            logger.debug("Cache hit for %s", cache_key)
            return cached

        if _last_night_briefing is not None:
            logger.info("TTL 캐시 만료, last_night_briefing 반환 (stale)")
            set_cached(cache_key, _last_night_briefing)
            return _last_night_briefing

        logger.info("브리핑 미생성 — mock night briefing 즉시 반환")
        return _MOCK_NIGHT.model_copy(
            update={"generated_at": datetime.now(timezone.utc).isoformat()}
        )

    async def generate_briefing(self, device_id: str) -> BriefingResponse:
        """Manually trigger briefing generation.

        Args:
            device_id: The requesting device identifier.

        Returns:
            A BriefingResponse (morning or night based on time).
        """
        logger.info("Manual briefing generation triggered for device %s", device_id)
        return await self.generate_morning_briefing_background(device_id)

    async def generate_morning_briefing_background(self, device_id: str) -> BriefingResponse:
        """실제로 Gemini API를 호출하여 모닝 브리핑을 생성한다.

        스케줄러 또는 수동 트리거에서 호출한다. API 엔드포인트에서 직접 호출하지 않는다.

        Args:
            device_id: The requesting device identifier.

        Returns:
            A BriefingResponse with morning briefing content.
        """
        global _last_morning_briefing
        from services.cache import set_cached

        if not settings.GEMINI_API_KEY:
            logger.warning("GEMINI_API_KEY 미설정 — mock 데이터 반환")
            return _MOCK_MORNING.model_copy(
                update={"generated_at": datetime.now(timezone.utc).isoformat(), "is_mock": True}
            )

        etf_list = ", ".join(_DEFAULT_ETFS)
        news_summary = (
            "FOMC 금리 동결, NVIDIA 분기 실적 매출 260% 급증, "
            "국제유가 WTI $85 돌파, 미 국채 10년물 금리 4.1%로 하락"
        )

        prompt = MORNING_PROMPT.format(etf_list=etf_list, news_summary=news_summary)
        data = await _call_gemini(prompt)

        if data is None:
            logger.warning("Gemini API 실패 — mock morning briefing 반환")
            return _MOCK_MORNING.model_copy(
                update={"generated_at": datetime.now(timezone.utc).isoformat(), "is_mock": True}
            )

        result = _build_briefing_from_ai(data, "morning")
        _last_morning_briefing = result
        set_cached("briefing_morning", result)
        return result

    async def generate_night_briefing_background(self, device_id: str) -> BriefingResponse:
        """실제로 Gemini API를 호출하여 나이트 브리핑을 생성한다.

        스케줄러 또는 수동 트리거에서 호출한다. API 엔드포인트에서 직접 호출하지 않는다.

        Args:
            device_id: The requesting device identifier.

        Returns:
            A BriefingResponse with night checkpoint content.
        """
        global _last_night_briefing
        from services.cache import set_cached

        if not settings.GEMINI_API_KEY:
            logger.warning("GEMINI_API_KEY 미설정 — mock 데이터 반환")
            return _MOCK_NIGHT.model_copy(
                update={"generated_at": datetime.now(timezone.utc).isoformat(), "is_mock": True}
            )

        etf_list = ", ".join(_DEFAULT_ETFS)
        news_summary = (
            "오늘 밤 CPI 발표 예정, 연준 이사 월러 연설 예정, "
            "유럽중앙은행 금리 결정 대기 중"
        )

        prompt = NIGHT_PROMPT.format(etf_list=etf_list, news_summary=news_summary)
        data = await _call_gemini(prompt)

        if data is None:
            logger.warning("Gemini API 실패 — mock night briefing 반환")
            return _MOCK_NIGHT.model_copy(
                update={"generated_at": datetime.now(timezone.utc).isoformat(), "is_mock": True}
            )

        result = _build_briefing_from_ai(data, "night")
        _last_night_briefing = result
        set_cached("briefing_night", result)
        return result


briefing_service = BriefingService()
