"""구조화 데이터 컨텍스트: 백엔드 API에서 실시간 데이터를 가져와 자연어로 변환."""

import logging
import time
from typing import Any

import httpx

logger = logging.getLogger(__name__)

# ── 간단 캐시 (10분 TTL) ──

_cache: dict[str, Any] = {}
_cache_ts: float = 0.0
_CACHE_TTL = 600  # 10분


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

    # 포지션 매핑 (football-data.org 세부 포지션 → 약어)
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


async def build_structured_context(match_context: str = "") -> str:
    """구조화 데이터를 가져와 자연어 컨텍스트로 변환한다.

    백엔드 API /api/match/preview를 호출하여 실시간 순위, 선수 명단 등을
    자연어 한국어 텍스트로 변환한다. API 실패 시 빈 문자열을 반환하여
    파이프라인을 차단하지 않는다.

    Args:
        match_context: 현재 경기 컨텍스트 (API 호출 시 쿼리 파라미터로 전달).

    Returns:
        자연어 한국어 구조화 컨텍스트 문자열. 실패 시 빈 문자열.
    """
    global _cache, _cache_ts

    # 캐시 확인 (10분 TTL)
    now = time.monotonic()
    if _cache and (now - _cache_ts) < _CACHE_TTL:
        logger.debug("구조화 데이터 캐시 히트")
        return _cache.get("context", "")

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                "http://localhost:8000/api/match/preview",
                params={"context": match_context} if match_context else None,
            )
            response.raise_for_status()
            data = response.json()

        context = _convert_to_context(data)

        # 캐시 저장
        _cache = {"context": context}
        _cache_ts = now

        logger.info("구조화 데이터 로드 완료 (%d자)", len(context))
        return context

    except httpx.TimeoutException:
        logger.warning("구조화 데이터 API 타임아웃 (5초 초과)")
        return ""
    except httpx.HTTPStatusError as e:
        logger.warning("구조화 데이터 API HTTP 에러: %s", e.response.status_code)
        return ""
    except Exception as e:
        logger.warning("구조화 데이터 로드 실패: %s", e)
        return ""
