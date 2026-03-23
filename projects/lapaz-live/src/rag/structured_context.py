"""구조화 데이터 컨텍스트: 백엔드 API에서 실시간 데이터를 가져와 자연어로 변환."""

from __future__ import annotations

import asyncio
import logging
import os
import time
from typing import Any, Callable, Optional, TYPE_CHECKING

import httpx

if TYPE_CHECKING:
    from .logging_utils import PipelineLogger

from .exceptions import DataSourceError

# error_log_fn 콜백 타입 (pipeline.py와 동일 패턴)
ErrorLogFn = Optional[Callable[..., "asyncio.coroutines"]]

# 백엔드 API 베이스 URL (환경변수 우선)
_default_base_url = "http://localhost:8000"
if os.environ.get("VERCEL_URL"):
    _default_base_url = f"https://{os.environ['VERCEL_URL']}"
_API_BASE_URL = os.environ.get("LAPAZ_API_BASE_URL", _default_base_url)

logger = logging.getLogger(__name__)

# -- 간단 캐시 (2분 TTL) --

_cache: dict[str, Any] = {}
_cache_ts: float = 0.0
_CACHE_TTL = 120  # 2분 (라이브 경기 대응)


def _form_to_korean(form: list[str]) -> str:
    """최근 폼 리스트를 한국어로 변환한다.

    Args:
        form: ["W", "W", "D", "L", "W"] 형태의 폼 리스트.

    Returns:
        "승-승-무-패-승" 형태의 한국어 문자열.
    """
    mapping = {"W": "승", "D": "무", "L": "패"}
    return "-".join(mapping.get(f, f) for f in form)


def _format_standings(standings: list[dict]) -> str:
    """리그 순위 데이터를 자연어로 포맷한다.

    Args:
        standings: 순위 리스트 (각 항목에 rank, name, pts, played, wins, draws, losses, form 등).

    Returns:
        한국어 순위표 문자열.
    """
    if not standings:
        return ""

    lines = ["=== 현재 EPL 순위 (실시간) ==="]
    for team in standings:
        rank = team.get("rank", "?")
        name = team.get("team_name", team.get("name", "?"))
        pts = team.get("points", team.get("pts", 0))
        played = team.get("played", 0)
        wins = team.get("wins", 0)
        draws = team.get("draws", 0)
        losses = team.get("losses", 0)

        base = f"{rank}위: {name} ({pts}pts, {played}경기 {wins}승 {draws}무 {losses}패"

        form = team.get("form", [])
        if form:
            base += f", 최근 폼: {_form_to_korean(form)}"

        base += ")"
        lines.append(base)

    return "\n".join(lines)


def _format_squad(team_name: str, players: list[dict]) -> str:
    """선수 명단을 자연어로 포맷한다.

    Args:
        team_name: 팀 이름.
        players: 선수 리스트 (각 항목에 position, name, number 등).

    Returns:
        한국어 선수 명단 문자열.
    """
    if not players:
        return ""

    lines = [f"\n=== {team_name} 주요 선수 ==="]

    # 포지션 매핑 (football-data.org 세부 포지션 -> 약어)
    pos_map = {
        # 기본
        "Keeper": "GK", "Defender": "DF", "Midfielder": "MF", "Attacker": "FW",
        "GK": "GK", "DF": "DF", "MF": "MF", "FW": "FW",
        # football-data.org 세부 포지션
        "Goalkeeper": "GK",
        "Centre-Back": "DF", "Left-Back": "DF", "Right-Back": "DF",
        "Defensive Midfield": "MF", "Central Midfield": "MF",
        "Attacking Midfield": "MF",
        "Left Midfield": "MF", "Right Midfield": "MF",
        "Left Winger": "FW", "Right Winger": "FW",
        "Centre-Forward": "FW",
    }
    grouped: dict[str, list[str]] = {"GK": [], "DF": [], "MF": [], "FW": []}

    for player in players:
        raw_pos = player.get("position", "")
        pos = pos_map.get(raw_pos, "")
        name = player.get("name", "?")
        number = player.get("number")
        label = f"{name} (#{number})" if number else name

        if pos in grouped:
            grouped[pos].append(label)

    for pos, pos_players in grouped.items():
        if pos_players:
            lines.append(f"{pos}: {', '.join(pos_players)}")

    return "\n".join(lines)


def _format_match_info(match_info: dict) -> str:
    """경기 정보를 자연어로 포맷한다.

    Args:
        match_info: 경기 정보 딕셔너리 (home, away, date, venue 등).

    Returns:
        한국어 경기 정보 문자열.
    """
    if not match_info:
        return ""

    home = match_info.get("home", "")
    away = match_info.get("away", "")
    date = match_info.get("date", "")
    venue = match_info.get("venue", "")

    parts = [f"\n=== 다음 경기 정보 ==="]
    if home and away:
        parts.append(f"{home} vs {away}")
    if date:
        parts.append(f"일시: {date}")
    if venue:
        parts.append(f"장소: {venue}")

    return "\n".join(parts)


def _has_lineup_data(lineups: dict) -> bool:
    """라인업 데이터에 실제 선발 명단이 존재하는지 확인한다.

    Args:
        lineups: {home: {team, formation, start_xi, substitutes}, away: ...}.

    Returns:
        home 또는 away에 start_xi가 1명 이상이면 True.
    """
    if not lineups:
        return False
    for side in ("home", "away"):
        team_data = lineups.get(side, {})
        if team_data.get("start_xi"):
            return True
    return False


def _format_lineups(lineups: dict) -> str:
    """API-Football 라인업 데이터를 자연어로 포맷한다.

    Args:
        lineups: {home: {team, formation, start_xi, substitutes}, away: ...}.

    Returns:
        한국어 라인업 문자열. 공식 라인업 미발표 시 경고 문구 포함.
    """
    if not _has_lineup_data(lineups):
        return (
            "\n=== 라인업 정보 ===\n"
            "⚠️ 공식 라인업은 아직 발표되지 않았습니다. "
            "아래 정보는 프리뷰/예상이며 확정이 아닙니다."
        )

    parts: list[str] = [
        "\n=== 라인업 정보 ===",
        "✅ 이 라인업은 공식 발표된 정보입니다.",
    ]
    for side in ("home", "away"):
        team_data = lineups.get(side, {})
        team = team_data.get("team", "")
        formation = team_data.get("formation", "")
        start_xi = team_data.get("start_xi", [])
        if not start_xi:
            continue

        header = f"\n=== {team} 선발 라인업"
        if formation:
            header += f" ({formation})"
        header += " ==="
        parts.append(header)

        # 포지션별 그룹핑
        grouped: dict[str, list[str]] = {"GK": [], "DF": [], "MF": [], "FW": []}
        for p in start_xi:
            pos = p.get("pos", "")
            name = p.get("name", "?")
            number = p.get("number")
            label = f"{name} (#{number})" if number else name
            if pos in grouped:
                grouped[pos].append(label)
            else:
                grouped.setdefault("기타", []).append(label)

        for pos, players in grouped.items():
            if players:
                parts.append(f"{pos}: {', '.join(players)}")

    return "\n".join(parts)


def _format_live_state(live_data: dict) -> str:
    """라이브 경기 상태(스코어, 이벤트, 통계, 주심)를 자연어로 포맷한다."""
    parts: list[str] = []

    # 주심
    referee = live_data.get("referee")
    if referee:
        parts.append(f"\n=== 주심 ===\n{referee}")

    # 스코어
    score = live_data.get("score", {})
    if score and score.get("status") in ("live", "halftime", "finished"):
        home_score = score.get("home_score", 0)
        away_score = score.get("away_score", 0)
        minute = score.get("minute")
        status_kr = {"live": "진행중", "halftime": "하프타임", "finished": "종료"}.get(score["status"], "")
        minute_str = f" ({minute}분)" if minute else ""
        parts.append(f"\n=== 현재 스코어 ({status_kr}{minute_str}) ===")
        home_name = score.get("home_team", "홈팀")
        away_name = score.get("away_team", "어웨이팀")
        parts.append(f"{home_name} {home_score} - {away_score} {away_name}")

    # 주요 이벤트
    events = live_data.get("events", [])
    if events:
        parts.append("\n=== 경기 주요 이벤트 ===")
        for evt in events[:15]:
            t = evt.get("time", "")
            team = evt.get("team", "")
            player = evt.get("player", "")
            detail = evt.get("detail", "")
            etype = evt.get("type", "")
            if etype == "Goal":
                parts.append(f"{t}분 ⚽ 골! {player} ({team}) {detail}")
            elif etype == "Card":
                parts.append(f"{t}분 🟨 {detail} - {player} ({team})")
            elif etype == "subst":
                assist = evt.get("assist", "")
                parts.append(f"{t}분 🔄 교체: {assist} → {player} ({team})")

    # 주요 통계
    stats = live_data.get("statistics", {})
    if stats:
        parts.append("\n=== 경기 통계 ===")
        for side in ("home", "away"):
            team_stats = stats.get(side, {})
            team = team_stats.get("team", side)
            s = team_stats.get("stats", {})
            possession = s.get("Ball Possession", "")
            shots = s.get("Total Shots", "")
            shots_on = s.get("Shots on Goal", "")
            parts.append(f"{team}: 점유율 {possession}, 슈팅 {shots} (유효 {shots_on})")

    return "\n".join(parts)


def _convert_to_context(data: dict) -> str:
    """API 응답 JSON을 자연어 컨텍스트로 변환한다.

    Args:
        data: /api/match/preview API 응답 데이터.

    Returns:
        자연어 한국어 컨텍스트 문자열.
    """
    sections: list[str] = []

    # 리그 순위
    standings = data.get("standings", [])
    if standings:
        sections.append(_format_standings(standings))

    # 경기 정보 (MatchPreview 구조: home, away, match_date)
    home = data.get("home", {})
    away = data.get("away", {})
    match_date = data.get("match_date", "")
    if home and away:
        home_name = home.get("team_name", "홈팀")
        away_name = away.get("team_name", "어웨이팀")
        sections.append(f"\n=== 다음 경기 정보 ===")
        sections.append(f"{home_name} vs {away_name}")
        if match_date:
            sections.append(f"일시: {match_date}")

    # 홈팀 감독 + 선수
    if home:
        home_name = home.get("team_name", "홈팀")
        coach = home.get("coach")
        if coach and coach.get("name"):
            sections.append(f"\n=== {home_name} 감독: {coach['name']} ({coach.get('nationality', '')}) ===")
        squad = home.get("squad", [])
        if squad:
            sections.append(_format_squad(home_name, squad))

    # 어웨이팀 감독 + 선수
    if away:
        away_name = away.get("team_name", "어웨이팀")
        coach = away.get("coach")
        if coach and coach.get("name"):
            sections.append(f"\n=== {away_name} 감독: {coach['name']} ({coach.get('nationality', '')}) ===")
        squad = away.get("squad", [])
        if squad:
            sections.append(_format_squad(away_name, squad))

    return "\n".join(sections)


# 개별 소스 타임아웃 (초)
_SOURCE_TIMEOUT = 5.0


async def _fetch_preview(
    client: httpx.AsyncClient,
    match_context: str,
    plog: PipelineLogger | None,
) -> str:
    """match/preview API를 호출하여 자연어 컨텍스트를 반환한다.

    개별 타임아웃(_SOURCE_TIMEOUT)이 적용된다.
    성공 시 자연어 문자열, 실패 시 빈 문자열을 반환한다.

    Args:
        client: httpx 비동기 클라이언트.
        match_context: 경기 컨텍스트 쿼리 파라미터.
        plog: 구조화 로거 (선택).

    Returns:
        자연어 한국어 프리뷰 컨텍스트 문자열. 실패 시 빈 문자열.

    Raises:
        Exception: API 호출 또는 파싱 실패 시 (호출부에서 처리).
    """
    source_start = time.monotonic()
    resp = await asyncio.wait_for(
        client.get(
            f"{_API_BASE_URL}/api/match/preview",
            params={"context": match_context} if match_context else None,
        ),
        timeout=_SOURCE_TIMEOUT,
    )
    latency = int((time.monotonic() - source_start) * 1000)
    resp.raise_for_status()
    data = resp.json()
    if plog:
        plog.info(
            f"match/preview API 성공 ({resp.status_code})",
            pipeline_stage="structured_context", event="api_call_success",
            source="football-data", latency_ms=latency,
            status_code=resp.status_code,
        )
    return _convert_to_context(data)


async def _fetch_live_state(
    client: httpx.AsyncClient,
    plog: PipelineLogger | None,
) -> str:
    """match/live-state API를 호출하여 라이브 데이터 컨텍스트를 반환한다.

    개별 타임아웃(_SOURCE_TIMEOUT)이 적용된다.
    스코어, 이벤트, 통계, 라인업을 자연어로 변환한다.

    Args:
        client: httpx 비동기 클라이언트.
        plog: 구조화 로거 (선택).

    Returns:
        자연어 한국어 라이브 컨텍스트 문자열. 데이터 없으면 빈 문자열.

    Raises:
        Exception: API 호출 또는 파싱 실패 시 (호출부에서 처리).
    """
    source_start = time.monotonic()
    resp = await asyncio.wait_for(
        client.get(f"{_API_BASE_URL}/api/match/live-state"),
        timeout=_SOURCE_TIMEOUT,
    )
    latency = int((time.monotonic() - source_start) * 1000)
    resp.raise_for_status()
    live_data = resp.json()
    if plog:
        plog.info(
            f"match/live-state API 성공 ({resp.status_code})",
            pipeline_stage="structured_context", event="api_call_success",
            source="API-Football", latency_ms=latency,
            status_code=resp.status_code,
        )

    parts: list[str] = []
    live_text = _format_live_state(live_data)
    if live_text:
        parts.append(live_text)
    # 라인업은 항상 포함 (미발표 시 경고 문구가 삽입됨)
    lineup_text = _format_lineups(live_data.get("lineups", {}))
    parts.append(lineup_text)
    return "\n".join(parts)


async def _safe_log_error(
    error_log_fn: ErrorLogFn,
    *,
    request_id: str,
    question: str,
    error_type: str,
    pipeline_stage: str,
    error_message: str,
    latency_ms: int | None = None,
) -> None:
    """error_log_fn 콜백을 안전하게 호출한다.

    콜백이 None이거나 호출 자체가 실패해도 예외를 발생시키지 않는다.
    부분 실패 시 DB 기록이 원래 흐름을 절대 막지 않기 위함.
    """
    if error_log_fn is None:
        return
    try:
        await error_log_fn(
            request_id=request_id,
            question=question,
            error_type=error_type,
            pipeline_stage=pipeline_stage,
            error_message=error_message,
            latency_ms=latency_ms,
        )
    except Exception as e:
        logger.warning("error_log_fn 콜백 실패 (무시): %s", e)


async def build_structured_context(
    match_context: str = "",
    *,
    plog: PipelineLogger | None = None,
    error_log_fn: ErrorLogFn = None,
    request_id: str = "",
    question: str = "",
) -> str:
    """구조화 데이터를 가져와 자연어 컨텍스트로 변환한다.

    백엔드 API /api/match/preview와 /api/match/live-state를 병렬 호출하여
    실시간 순위, 선수 명단, 스코어, 이벤트 등을 자연어 한국어 텍스트로 변환한다.

    각 소스에 개별 타임아웃(_SOURCE_TIMEOUT)이 적용되며, 단일 소스 실패 시
    나머지 소스만으로 부분 컨텍스트를 조합하여 반환한다.
    두 소스 모두 실패하면 DataSourceError를 raise한다.

    Args:
        match_context: 현재 경기 컨텍스트 (API 호출 시 쿼리 파라미터로 전달).
        plog: 구조화 로거 (선택).

    Returns:
        자연어 한국어 구조화 컨텍스트 문자열.

    Raises:
        DataSourceError: 두 소스 모두 실패한 경우.
    """
    global _cache, _cache_ts

    start = time.monotonic()

    # 캐시 확인 (2분 TTL)
    now = time.monotonic()
    if _cache and (now - _cache_ts) < _CACHE_TTL:
        if plog:
            plog.info("구조화 데이터 캐시 히트", pipeline_stage="structured_context",
                      event="cache_hit", source="internal_api", cached=True)
        else:
            logger.debug("구조화 데이터 캐시 히트")
        return _cache.get("context", "")

    # 개별 타임아웃이 적용된 소스별 fetch 함수를 병렬 호출
    preview_context = ""
    live_context = ""
    preview_error: Exception | None = None
    live_error: Exception | None = None

    async with httpx.AsyncClient(timeout=_SOURCE_TIMEOUT + 2.0) as client:
        preview_result, live_result = await asyncio.gather(
            _fetch_preview(client, match_context, plog),
            _fetch_live_state(client, plog),
            return_exceptions=True,
        )

    # preview 결과 처리
    if isinstance(preview_result, Exception):
        preview_error = preview_result
        preview_latency = int((time.monotonic() - start) * 1000)
        if plog:
            plog.warning(
                f"match/preview API 실패: {preview_result}",
                pipeline_stage="structured_context", event="api_call_error",
                source="football-data",
                error_type=type(preview_result).__name__,
                latency_ms=preview_latency,
                status="failed",
            )
        else:
            logger.warning("match/preview API 실패: %s", preview_result)
        # 부분 실패 DB 기록 (전체 실패가 아닌 경우에만 의미 — 전체 실패는 pipeline.py가 처리)
        await _safe_log_error(
            error_log_fn,
            request_id=request_id,
            question=question,
            error_type="data_source_partial",
            pipeline_stage="structured_context",
            error_message=f"match/preview 실패: {preview_result}",
            latency_ms=preview_latency,
        )
    else:
        preview_context = preview_result

    # live-state 결과 처리
    if isinstance(live_result, Exception):
        live_error = live_result
        live_latency = int((time.monotonic() - start) * 1000)
        if plog:
            plog.warning(
                f"match/live-state API 실패: {live_result}",
                pipeline_stage="structured_context", event="api_call_error",
                source="API-Football",
                error_type=type(live_result).__name__,
                latency_ms=live_latency,
                status="failed",
            )
        else:
            logger.warning("match/live-state API 실패: %s", live_result)
        # 부분 실패 DB 기록
        await _safe_log_error(
            error_log_fn,
            request_id=request_id,
            question=question,
            error_type="data_source_partial",
            pipeline_stage="structured_context",
            error_message=f"match/live-state 실패: {live_result}",
            latency_ms=live_latency,
        )

    # 두 소스 모두 실패 → DataSourceError raise (pipeline.py의 degradation이 처리)
    if preview_error and live_error:
        total_latency = int((time.monotonic() - start) * 1000)
        if plog:
            plog.warning(
                "두 데이터 소스 모두 실패",
                pipeline_stage="structured_context", event="all_sources_failed",
                error_type="DataSourceError",
                latency_ms=total_latency,
                preview_error=type(preview_error).__name__,
                live_error=type(live_error).__name__,
            )
        raise DataSourceError(
            f"모든 데이터 소스 실패: preview={preview_error}, live={live_error}"
        ) from preview_error

    # 부분 컨텍스트 조합
    sections = [s for s in (preview_context, live_context) if s]
    context = "\n".join(sections)

    is_partial = bool(preview_error or live_error)
    if is_partial and plog:
        failed_source = "football-data" if preview_error else "API-Football"
        succeeded_source = "API-Football" if preview_error else "football-data"
        plog.info(
            f"부분 컨텍스트 조합: {failed_source} 실패, {succeeded_source}만 사용",
            pipeline_stage="structured_context", event="partial_context",
            partial_context=True,
            failed_source=failed_source,
            succeeded_source=succeeded_source,
        )

    # 캐시 저장
    _cache = {"context": context}
    _cache_ts = now

    total_latency = int((time.monotonic() - start) * 1000)
    if plog:
        plog.info(
            f"구조화 데이터 로드 완료 ({len(context)}자)",
            pipeline_stage="structured_context", event="done",
            latency_ms=total_latency,
            partial_context=is_partial,
        )
    else:
        logger.info("구조화 데이터 로드 완료 (%d자, partial=%s)", len(context), is_partial)
    return context
