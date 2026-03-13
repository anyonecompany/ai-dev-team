#!/usr/bin/env python3
"""La Paz — Pilot Match Prep: Man Utd vs Aston Villa (2026-03-15)

PART 1: football-data.org에서 양 팀 최신 데이터 수집
PART 2: Google Gemini Flash로 팬 친화적 AI 문서 생성
PART 3: SentenceTransformer 임베딩 + Supabase 저장

총 예상 문서: 55-65건 (match_preview, tactical, h2h, player profiles, Q&A 등)
"""

from __future__ import annotations

import json
import sys
import time
import traceback
import uuid
from pathlib import Path

# ── 경로 설정 ────────────────────────────────────
sys.path.insert(0, str(Path(__file__).parent))
from shared_config import (
    get_agent_logger,
    get_supabase,
    sb_select,
    sb_upsert,
    sb_insert,
    FOOTBALL_DATA_TOKEN,
    GOOGLE_API_KEY,
)
from collectors._common import _fd_get

log = get_agent_logger("pilot_match_prep")

# ── 상수 ──────────────────────────────────────────
MATCH_DATE = "2026-03-15"
MAN_UTD_FD_CODE = 66
ASTON_VILLA_FD_CODE = 58
MAN_UTD_TEAM_ID = "480ce206-bf2a-48f8-949c-7af889d8bf0f"
ASTON_VILLA_TEAM_ID = "5fa1129a-6569-4977-a735-c19814c42d60"
EMBED_MODEL = "intfloat/multilingual-e5-large"  # 1024-dim (DB 스키마 맞춤)
BATCH_SIZE = 50

# Gemini 온도 설정
TEMP_FACTUAL = 0.3
TEMP_FAN = 0.5


# ══════════════════════════════════════════════════
# PART 1: 데이터 수집 (football-data.org)
# ══════════════════════════════════════════════════

def collect_squad(team_code: int, team_name: str) -> dict | None:
    """팀 스쿼드 데이터 수집."""
    log.info(f"[수집] {team_name} 스쿼드 (team code={team_code})")
    data = _fd_get(f"/teams/{team_code}")
    if data:
        squad = data.get("squad", [])
        coach = data.get("coach", {})
        log.info(f"  → 선수 {len(squad)}명, 감독: {coach.get('name', 'N/A')}")
    else:
        log.warning(f"  → {team_name} 스쿼드 수집 실패")
    return data


def collect_team_matches(team_code: int, team_name: str, limit: int = 15) -> list[dict]:
    """팀의 최근 경기 결과 수집."""
    log.info(f"[수집] {team_name} 최근 경기 (team code={team_code})")
    data = _fd_get(f"/teams/{team_code}/matches?status=FINISHED&limit={limit}")
    if data and "matches" in data:
        matches = data["matches"]
        log.info(f"  → {len(matches)}경기 수집")
        return matches
    log.warning(f"  → {team_name} 경기 수집 실패")
    return []


def collect_standings() -> list[dict]:
    """프리미어리그 순위표 수집."""
    log.info("[수집] EPL 순위표")
    data = _fd_get("/competitions/PL/standings")
    if data and "standings" in data:
        total = [s for s in data["standings"] if s.get("type") == "TOTAL"]
        if total:
            table = total[0].get("table", [])
            log.info(f"  → {len(table)}팀 순위 수집")
            return table
    log.warning("  → 순위표 수집 실패")
    return []


def collect_h2h_from_db() -> list[dict]:
    """DB에서 맨유 vs 빌라 맞대결 조회."""
    log.info("[수집] DB에서 맨유 vs 빌라 맞대결 조회")
    all_team_ids = [
        MAN_UTD_TEAM_ID,
        "8616c7db-8d3d-4fa1-a0d0-d63601684404",  # StatsBomb Man Utd
    ]
    matches = []
    for tid in all_team_ids:
        home = sb_select("matches", filters={"home_team_id": tid, "away_team_id": ASTON_VILLA_TEAM_ID}, limit=100)
        away = sb_select("matches", filters={"home_team_id": ASTON_VILLA_TEAM_ID, "away_team_id": tid}, limit=100)
        matches.extend(home)
        matches.extend(away)
    # 반대 방향도 확인
    for tid in all_team_ids:
        home2 = sb_select("matches", filters={"home_team_id": ASTON_VILLA_TEAM_ID, "away_team_id": tid}, limit=100)
        # 이미 위에서 포함됨 — 중복 제거
        pass

    # 중복 제거
    seen = set()
    unique = []
    for m in matches:
        if m["id"] not in seen:
            seen.add(m["id"])
            unique.append(m)

    log.info(f"  → 맞대결 {len(unique)}경기 발견")
    return unique


def collect_recent_form_from_db(team_id: str, team_name: str, limit: int = 10) -> list[dict]:
    """DB에서 팀의 최근 경기 조회."""
    log.info(f"[수집] DB에서 {team_name} 최근 폼 조회")
    home = sb_select("matches", filters={"home_team_id": team_id}, limit=200)
    away = sb_select("matches", filters={"away_team_id": team_id}, limit=200)
    all_matches = home + away
    # 날짜 정렬 (최신순)
    all_matches.sort(key=lambda x: x.get("match_date", "") or "", reverse=True)
    recent = all_matches[:limit]
    log.info(f"  → {len(recent)}경기 조회")
    return recent


def run_data_collection() -> dict:
    """PART 1 전체 데이터 수집 실행."""
    log.info("=" * 60)
    log.info("PART 1: 데이터 수집 시작")
    log.info("=" * 60)

    collected = {}

    # 1) Man Utd 스쿼드
    collected["manu_squad"] = collect_squad(MAN_UTD_FD_CODE, "Man United")
    time.sleep(7)

    # 2) Aston Villa 스쿼드
    collected["villa_squad"] = collect_squad(ASTON_VILLA_FD_CODE, "Aston Villa")
    time.sleep(7)

    # 3) Man Utd 최근 경기
    collected["manu_matches"] = collect_team_matches(MAN_UTD_FD_CODE, "Man United")
    time.sleep(7)

    # 4) Aston Villa 최근 경기
    collected["villa_matches"] = collect_team_matches(ASTON_VILLA_FD_CODE, "Aston Villa")
    time.sleep(7)

    # 5) EPL 순위표
    collected["standings"] = collect_standings()

    # 6) DB에서 맞대결 기록
    collected["h2h"] = collect_h2h_from_db()

    # 7) DB에서 최근 폼
    collected["manu_form"] = collect_recent_form_from_db(MAN_UTD_TEAM_ID, "Man United")
    collected["villa_form"] = collect_recent_form_from_db(ASTON_VILLA_TEAM_ID, "Aston Villa")

    # 8) DB에서 팀 시즌 통계
    collected["manu_stats"] = sb_select("team_season_stats", filters={"team_id": MAN_UTD_TEAM_ID}, limit=10)
    collected["villa_stats"] = sb_select("team_season_stats", filters={"team_id": ASTON_VILLA_TEAM_ID}, limit=10)

    log.info("PART 1 완료: 데이터 수집 끝")
    return collected


# ══════════════════════════════════════════════════
# PART 2: AI 문서 생성 (Google Gemini Flash)
# ══════════════════════════════════════════════════

def _init_gemini():
    """Gemini 모델 초기화."""
    import google.generativeai as genai
    genai.configure(api_key=GOOGLE_API_KEY)
    return genai.GenerativeModel("gemini-2.0-flash")


def _generate(model, prompt: str, temperature: float = TEMP_FAN, max_retries: int = 3) -> str:
    """Gemini 문서 생성 (에러 안전, 429 자동 재시도)."""
    for attempt in range(max_retries):
        try:
            response = model.generate_content(
                prompt,
                generation_config={"temperature": temperature, "max_output_tokens": 4096},
            )
            return response.text.strip()
        except Exception as e:
            err_str = str(e)
            if "429" in err_str or "Resource exhausted" in err_str:
                wait = 30 * (attempt + 1)
                log.warning(f"  Gemini 429 — {wait}초 대기 후 재시도 ({attempt+1}/{max_retries})")
                time.sleep(wait)
            else:
                log.warning(f"  Gemini 생성 실패: {e}")
                return ""
    log.warning("  Gemini 최대 재시도 초과")
    return ""


def _format_matches_for_prompt(matches: list[dict], limit: int = 10) -> str:
    """경기 데이터를 프롬프트용 텍스트로 변환."""
    lines = []
    for m in matches[:limit]:
        date = m.get("match_date", "N/A")
        home_score = m.get("home_score", "?")
        away_score = m.get("away_score", "?")
        meta = m.get("meta", {}) or {}
        home = meta.get("home_team_name", "Home")
        away = meta.get("away_team_name", "Away")
        lines.append(f"  {date}: {home} {home_score}-{away_score} {away}")
    return "\n".join(lines) if lines else "  데이터 없음"


def _format_squad_for_prompt(squad_data: dict | None) -> str:
    """스쿼드 데이터를 프롬프트용 텍스트로 변환."""
    if not squad_data:
        return "스쿼드 데이터 없음"
    squad = squad_data.get("squad", [])
    coach = squad_data.get("coach", {})
    lines = [f"감독: {coach.get('name', 'N/A')} (국적: {coach.get('nationality', 'N/A')})"]
    for p in squad:
        pos = p.get("position", "N/A")
        name = p.get("name", "N/A")
        nat = p.get("nationality", "")
        lines.append(f"  [{pos}] {name} ({nat})")
    return "\n".join(lines)


def _format_standings_for_prompt(standings: list[dict], highlight_teams: list[str] | None = None) -> str:
    """순위표를 프롬프트용 텍스트로 변환."""
    lines = []
    for entry in standings:
        team_info = entry.get("team", {})
        team_name = team_info.get("shortName") or team_info.get("name", "?")
        pos = entry.get("position", "?")
        pts = entry.get("points", 0)
        played = entry.get("playedGames", 0)
        won = entry.get("won", 0)
        draw = entry.get("draw", 0)
        lost = entry.get("lost", 0)
        gf = entry.get("goalsFor", 0)
        ga = entry.get("goalsAgainst", 0)
        marker = " ★" if highlight_teams and team_name in highlight_teams else ""
        lines.append(f"  {pos}. {team_name}{marker} - {pts}pts ({played}경기, {won}승 {draw}무 {lost}패, 득실 {gf}-{ga})")
    return "\n".join(lines) if lines else "  순위 데이터 없음"


def _format_stats_for_prompt(stats: list[dict]) -> str:
    """시즌 통계를 프롬프트용 텍스트로 변환."""
    if not stats:
        return "  시즌 통계 없음"
    lines = []
    for s in stats:
        lines.append(
            f"  순위 {s.get('position', '?')} | {s.get('played', 0)}경기 "
            f"{s.get('won', 0)}승 {s.get('draw', 0)}무 {s.get('lost', 0)}패 | "
            f"득점 {s.get('goals_for', 0)} 실점 {s.get('goals_against', 0)} | "
            f"{s.get('points', 0)}pts"
        )
        if s.get("xg_for"):
            lines.append(f"    xG: {s.get('xg_for', 0)} / xGA: {s.get('xg_against', 0)}")
    return "\n".join(lines)


def generate_manager_analysis(model, collected: dict) -> list[dict]:
    """감독 분석 문서 2건 생성."""
    log.info("[생성] 감독 분석 문서")
    docs = []

    managers = [
        {
            "name": "마이클 캐릭 (Michael Carrick)",
            "team": "맨체스터 유나이티드",
            "team_id": MAN_UTD_TEAM_ID,
            "squad": collected.get("manu_squad"),
            "matches": collected.get("manu_matches", []),
            "stats": collected.get("manu_stats", []),
        },
        {
            "name": "우나이 에메리 (Unai Emery)",
            "team": "아스톤 빌라",
            "team_id": ASTON_VILLA_TEAM_ID,
            "squad": collected.get("villa_squad"),
            "matches": collected.get("villa_matches", []),
            "stats": collected.get("villa_stats", []),
        },
    ]

    for mgr in managers:
        prompt = f"""당신은 축구 전술 전문가입니다. 다음 데이터를 바탕으로 {mgr['name']}의 전술 분석 문서를 작성해주세요.
팬이 이해하기 쉽게, 전술 철학, 선호 포메이션, 핵심 전술 원칙, 강점과 약점을 분석해주세요.

팀: {mgr['team']}

스쿼드 정보:
{_format_squad_for_prompt(mgr['squad'])}

최근 경기 결과:
{_format_matches_for_prompt(mgr['matches'])}

시즌 통계:
{_format_stats_for_prompt(mgr['stats'])}

다음 형식으로 작성해주세요:
1. 감독 소개 및 경력 배경
2. 전술 철학 (핵심 키워드 3-4개)
3. 선호 포메이션 및 시스템
4. 핵심 전술 원칙 (공격/수비)
5. 현재 시즌 강점
6. 현재 시즌 약점/과제
7. 맨유 vs 빌라 전에서의 전술 포인트

한국어로 작성하세요. 팬 친화적이지만 전술적 깊이도 있게 작성해주세요."""

        content = _generate(model, prompt, TEMP_FAN)
        if content:
            docs.append({
                "doc_type": "manager_analysis",
                "ref_id": mgr["team_id"],
                "title": f"{mgr['name']} 전술 분석 — {mgr['team']}",
                "content": content,
                "metadata": {
                    "match_date": MATCH_DATE,
                    "manager": mgr["name"],
                    "team": mgr["team"],
                    "pilot": True,
                },
            })
            log.info(f"  ✓ {mgr['name']} 전술 분석 생성 ({len(content)}자)")
        time.sleep(2)

    return docs


def generate_tactical_preview(model, collected: dict) -> list[dict]:
    """전술 프리뷰 문서 1건 생성."""
    log.info("[생성] 전술 프리뷰")

    prompt = f"""당신은 축구 전술 분석가입니다. 맨체스터 유나이티드 vs 아스톤 빌라 (2026년 3월 15일) 경기의 전술 프리뷰를 작성해주세요.

맨유 스쿼드:
{_format_squad_for_prompt(collected.get('manu_squad'))}

빌라 스쿼드:
{_format_squad_for_prompt(collected.get('villa_squad'))}

맨유 최근 경기:
{_format_matches_for_prompt(collected.get('manu_matches', []))}

빌라 최근 경기:
{_format_matches_for_prompt(collected.get('villa_matches', []))}

맨유 시즌 통계:
{_format_stats_for_prompt(collected.get('manu_stats', []))}

빌라 시즌 통계:
{_format_stats_for_prompt(collected.get('villa_stats', []))}

다음을 포함해 한국어로 작성:
1. 예상 포메이션 대결 분석
2. 핵심 매치업 3가지 (구체적 선수 명시)
3. 공간 활용 포인트 (어디서 우위를 점할 수 있는지)
4. 세트피스 위협 분석
5. 교체 전략 시나리오
6. 승부 포인트 요약

팬이 경기 전에 읽으면 경기를 더 잘 이해할 수 있도록 작성해주세요."""

    content = _generate(model, prompt, TEMP_FAN)
    if content:
        return [{
            "doc_type": "tactical_preview",
            "ref_id": None,
            "title": "전술 프리뷰: 맨체스터 유나이티드 vs 아스톤 빌라 (2026.03.15)",
            "content": content,
            "metadata": {"match_date": MATCH_DATE, "teams": ["Man United", "Aston Villa"], "pilot": True},
        }]
    return []


def generate_h2h_analysis(model, collected: dict) -> list[dict]:
    """맞대결 분석 문서 1건 생성."""
    log.info("[생성] 맞대결 분석")

    h2h = collected.get("h2h", [])
    h2h_text = _format_matches_for_prompt(h2h, limit=20) if h2h else "DB에서 맞대결 기록을 찾지 못했습니다."

    manu_matches_text = _format_matches_for_prompt(collected.get("manu_matches", []))
    villa_matches_text = _format_matches_for_prompt(collected.get("villa_matches", []))

    prompt = f"""당신은 축구 역사 전문가입니다. 맨체스터 유나이티드 vs 아스톤 빌라의 맞대결 역사를 분석해주세요.

맞대결 기록:
{h2h_text}

맨유 최근 경기:
{manu_matches_text}

빌라 최근 경기:
{villa_matches_text}

다음을 포함해 한국어로 작성:
1. 양 팀 역사적 라이벌리 배경
2. 최근 맞대결 트렌드 (누가 우세했는지)
3. 맞대결에서의 주요 기억에 남는 경기들
4. 올드 트래포드 / 빌라 파크에서의 각 팀 기록 차이
5. 2026년 3월 15일 경기에서 주목할 역사적 포인트
6. 양 팀 팬들이 기대하는 점

팬이 흥미를 느낄 수 있는 스토리텔링 방식으로 작성해주세요."""

    content = _generate(model, prompt, TEMP_FAN)
    if content:
        return [{
            "doc_type": "h2h_analysis",
            "ref_id": None,
            "title": "맞대결 분석: 맨체스터 유나이티드 vs 아스톤 빌라 역사",
            "content": content,
            "metadata": {"match_date": MATCH_DATE, "h2h_count": len(h2h), "pilot": True},
        }]
    return []


def generate_match_preview(model, collected: dict) -> list[dict]:
    """종합 매치 프리뷰 1건 생성."""
    log.info("[생성] 종합 매치 프리뷰")

    standings_text = _format_standings_for_prompt(
        collected.get("standings", []),
        highlight_teams=["Man United", "Man Utd", "Aston Villa"],
    )

    prompt = f"""당신은 축구 전문 저널리스트입니다. 맨체스터 유나이티드 vs 아스톤 빌라 (2026년 3월 15일, 프리미어리그) 경기 종합 프리뷰를 작성해주세요.

EPL 순위표:
{standings_text}

맨유 스쿼드:
{_format_squad_for_prompt(collected.get('manu_squad'))}

빌라 스쿼드:
{_format_squad_for_prompt(collected.get('villa_squad'))}

맨유 최근 경기:
{_format_matches_for_prompt(collected.get('manu_matches', []))}

빌라 최근 경기:
{_format_matches_for_prompt(collected.get('villa_matches', []))}

맨유 시즌 통계:
{_format_stats_for_prompt(collected.get('manu_stats', []))}

빌라 시즌 통계:
{_format_stats_for_prompt(collected.get('villa_stats', []))}

다음을 포함해 한국어로 작성:
1. 경기 기본 정보 (날짜, 장소, 킥오프)
2. 양 팀 현재 시즌 요약
3. 최근 폼 비교
4. 주요 선수 분석 (각 팀 3-4명)
5. 부상/결장 정보 (알려진 범위)
6. 핵심 매치업
7. 승부 예측 및 예상 스코어
8. 이 경기가 중요한 이유

종합적이고 깊이 있는 프리뷰를 작성해주세요."""

    content = _generate(model, prompt, TEMP_FAN)
    if content:
        return [{
            "doc_type": "match_preview",
            "ref_id": None,
            "title": "매치 프리뷰: 맨체스터 유나이티드 vs 아스톤 빌라 (2026.03.15)",
            "content": content,
            "metadata": {"match_date": MATCH_DATE, "competition": "Premier League", "pilot": True},
        }]
    return []


def generate_season_context(model, collected: dict) -> list[dict]:
    """시즌 맥락 문서 1건 생성."""
    log.info("[생성] 시즌 맥락 분석")

    standings_text = _format_standings_for_prompt(
        collected.get("standings", []),
        highlight_teams=["Man United", "Man Utd", "Aston Villa"],
    )

    prompt = f"""당신은 EPL 분석 전문가입니다. 맨체스터 유나이티드 vs 아스톤 빌라 (2026년 3월 15일) 경기가 시즌 전체 맥락에서 어떤 의미를 갖는지 분석해주세요.

현재 EPL 순위표:
{standings_text}

맨유 시즌 통계:
{_format_stats_for_prompt(collected.get('manu_stats', []))}

빌라 시즌 통계:
{_format_stats_for_prompt(collected.get('villa_stats', []))}

다음을 포함해 한국어로 작성:
1. 현재 EPL 타이틀 레이스 상황
2. UCL/UEL 진출권 경쟁 분석 (4위 경쟁)
3. 맨유의 시즌 목표와 현재 위치
4. 빌라의 시즌 목표와 현재 위치
5. 이 경기 승/무/패 시나리오별 영향
6. 남은 시즌 일정 고려 시 이 경기의 중요도
7. 강등/잔류 관점 (해당 시)

팬이 "이 경기가 왜 중요한지"를 명확히 이해할 수 있도록 작성해주세요."""

    content = _generate(model, prompt, TEMP_FACTUAL)
    if content:
        return [{
            "doc_type": "season_context",
            "ref_id": None,
            "title": "시즌 맥락: 맨유 vs 빌라, 이 경기가 중요한 이유 (2026.03.15)",
            "content": content,
            "metadata": {"match_date": MATCH_DATE, "pilot": True},
        }]
    return []


def generate_player_profiles(model, collected: dict) -> list[dict]:
    """주요 선수 프로필 22-30건 생성."""
    log.info("[생성] 선수 프로필")
    docs = []

    teams_data = [
        {
            "team": "맨체스터 유나이티드",
            "team_id": MAN_UTD_TEAM_ID,
            "squad": collected.get("manu_squad"),
            "matches": collected.get("manu_matches", []),
        },
        {
            "team": "아스톤 빌라",
            "team_id": ASTON_VILLA_TEAM_ID,
            "squad": collected.get("villa_squad"),
            "matches": collected.get("villa_matches", []),
        },
    ]

    for team_data in teams_data:
        squad = (team_data["squad"] or {}).get("squad", [])
        if not squad:
            log.warning(f"  {team_data['team']} 스쿼드 없음 — 건너뜀")
            continue

        # 핵심 선수 선별: GK 1-2, DF 4-5, MF 4-5, FW 2-4
        by_pos = {}
        for p in squad:
            pos = (p.get("position") or "Unknown").upper()
            if "GOAL" in pos:
                by_pos.setdefault("GK", []).append(p)
            elif "BACK" in pos or "DEFENCE" in pos:
                by_pos.setdefault("DF", []).append(p)
            elif "MID" in pos:
                by_pos.setdefault("MF", []).append(p)
            elif "FORWARD" in pos or "WING" in pos or "OFFENCE" in pos or "ATTACK" in pos:
                by_pos.setdefault("FW", []).append(p)
            else:
                by_pos.setdefault("OTHER", []).append(p)

        # 포지션별 선발 수
        limits = {"GK": 1, "DF": 4, "MF": 4, "FW": 3, "OTHER": 0}
        selected_players = []
        for pos, players in by_pos.items():
            lim = limits.get(pos, 2)
            selected_players.extend(players[:lim])

        log.info(f"  {team_data['team']}: {len(selected_players)}명 선수 프로필 생성")

        for player in selected_players:
            p_name = player.get("name", "Unknown")
            p_nat = player.get("nationality", "N/A")
            p_pos = player.get("position", "N/A")
            p_dob = player.get("dateOfBirth", "N/A")

            prompt = f"""당신은 축구 팬 커뮤니티의 인기 칼럼니스트입니다. 다음 선수에 대한 팬 친화적 프로필을 작성해주세요.

선수 정보:
- 이름: {p_name}
- 팀: {team_data['team']}
- 포지션: {p_pos}
- 국적: {p_nat}
- 생년월일: {p_dob}

이 선수의 프로필을 다음 형식으로 한국어로 작성해주세요:
1. 한 줄 소개 ("이 선수는 __한 선수다")
2. 플레이 스타일 (팬 언어로, 전문 용어 설명 포함)
3. 현재 시즌 평가 (기대 대비 실제)
4. 이번 경기에서 주목할 포인트
5. 별명/평판 (있다면)
6. 재미있는 팩트 1-2개

통계 나열이 아니라 "이 선수가 어떤 선수인지" 팬에게 설명하는 방식으로 작성해주세요.
300-500자 정도로 간결하게."""

            content = _generate(model, prompt, TEMP_FAN)
            if content:
                docs.append({
                    "doc_type": "fan_player_profile",
                    "ref_id": team_data["team_id"],
                    "title": f"선수 프로필: {p_name} ({team_data['team']})",
                    "content": content,
                    "metadata": {
                        "match_date": MATCH_DATE,
                        "player_name": p_name,
                        "team": team_data["team"],
                        "position": p_pos,
                        "nationality": p_nat,
                        "pilot": True,
                    },
                })
                log.info(f"    ✓ {p_name} ({len(content)}자)")
            time.sleep(1)  # Gemini rate limit 관리

    return docs


def generate_fan_tactical_guide(model, collected: dict) -> list[dict]:
    """팬 전술 가이드 1건 생성."""
    log.info("[생성] 팬 전술 가이드")

    prompt = f"""당신은 축구를 쉽게 설명하는 전문가입니다. 맨체스터 유나이티드 vs 아스톤 빌라 경기를 위한 팬 전술 가이드를 작성해주세요.

맨유 스쿼드:
{_format_squad_for_prompt(collected.get('manu_squad'))}

빌라 스쿼드:
{_format_squad_for_prompt(collected.get('villa_squad'))}

다음을 포함해 한국어로 작성:

1. **"왜 저렇게 했어?" 가이드**
   - 높은 수비 라인 vs 낮은 수비 라인 — 언제, 왜?
   - 공을 뒤로 돌리는 이유
   - 왜 공격수가 수비를 하는지

2. **맨유의 전형적인 패턴**
   - 공격 빌드업 루트
   - 프레스 트리거
   - 위험한 공격 패턴

3. **빌라의 전형적인 패턴**
   - 에메리의 전환 축구
   - 수비 조직
   - 위험한 공격 패턴

4. **이 경기에서 볼 것들**
   - 양 팀이 서로를 어떻게 공략할지
   - 볼 점유 시나리오
   - 교체 시점과 전술 변화 포인트

축구를 잘 모르는 팬도 경기를 즐길 수 있도록 쉬운 언어로 작성해주세요."""

    content = _generate(model, prompt, TEMP_FAN)
    if content:
        return [{
            "doc_type": "fan_tactical_guide",
            "ref_id": None,
            "title": "팬 전술 가이드: 맨유 vs 빌라, 이렇게 보면 더 재밌다",
            "content": content,
            "metadata": {"match_date": MATCH_DATE, "pilot": True},
        }]
    return []


def generate_form_analysis(model, collected: dict) -> list[dict]:
    """양 팀 폼 분석 2건 생성."""
    log.info("[생성] 폼 분석")
    docs = []

    teams = [
        {
            "team": "맨체스터 유나이티드",
            "team_id": MAN_UTD_TEAM_ID,
            "matches": collected.get("manu_matches", []),
            "form": collected.get("manu_form", []),
            "stats": collected.get("manu_stats", []),
        },
        {
            "team": "아스톤 빌라",
            "team_id": ASTON_VILLA_TEAM_ID,
            "matches": collected.get("villa_matches", []),
            "form": collected.get("villa_form", []),
            "stats": collected.get("villa_stats", []),
        },
    ]

    for team in teams:
        prompt = f"""당신은 축구 분석가입니다. {team['team']}의 최근 폼을 분석해주세요.

최근 경기 결과 (football-data.org):
{_format_matches_for_prompt(team['matches'])}

DB 저장 최근 경기:
{_format_matches_for_prompt(team['form'])}

시즌 통계:
{_format_stats_for_prompt(team['stats'])}

다음을 포함해 한국어로 작성:
1. 최근 5-10경기 결과 요약
2. 모멘텀 평가 (상승/하락/안정)
3. 득점력 분석
4. 수비 안정성 분석
5. 홈/어웨이 폼 차이 (있다면)
6. 3월 15일 경기 전 폼 종합 판단

객관적 데이터 기반으로 작성하되, 팬이 이해하기 쉬운 언어로 작성해주세요."""

        content = _generate(model, prompt, TEMP_FACTUAL)
        if content:
            docs.append({
                "doc_type": "form_analysis",
                "ref_id": team["team_id"],
                "title": f"폼 분석: {team['team']} 최근 경기력 (2026.03.15 기준)",
                "content": content,
                "metadata": {"match_date": MATCH_DATE, "team": team["team"], "pilot": True},
            })
            log.info(f"  ✓ {team['team']} 폼 분석 ({len(content)}자)")
        time.sleep(2)

    return docs


def generate_rules_explainer(model) -> list[dict]:
    """규칙 설명 문서 1건 생성."""
    log.info("[생성] 규칙 설명 (VAR/SAOT/핸드볼)")

    prompt = """당신은 축구 규칙 해설 전문가입니다. 프리미어리그 경기를 시청하는 팬을 위한 규칙 가이드를 작성해주세요.

다음을 포함해 한국어로 작성:

1. **VAR (비디오 판독)**
   - VAR이 개입하는 4가지 상황
   - "심판이 왜 화면 보러 갔어?" 설명
   - VAR 판정이 뒤집어지는 기준
   - SAOT (반자동 오프사이드 기술) 작동 원리

2. **핸드볼 규칙 (2025-26 시즌)**
   - 핸드볼로 판정되는 경우 vs 아닌 경우
   - "팔이 몸에 붙어 있으면 괜찮은 거 아니야?" 설명
   - 공격 직전 핸드볼 규칙

3. **오프사이드 규칙**
   - 기본 원칙 + 예외 상황
   - "다시 보니까 오프사이드였네" 포인트
   - 간섭/이득 판단 기준

4. **자주 혼동되는 상황**
   - 선제 태클 vs 파울
   - 옐로카드 기준 (반복 파울, 지연, 항의)
   - 레드카드 — DOGSO vs SPA 차이

쉽고 재미있는 언어로, 축구 초보자도 이해할 수 있게 작성해주세요."""

    content = _generate(model, prompt, TEMP_FAN)
    if content:
        return [{
            "doc_type": "rules_explainer",
            "ref_id": None,
            "title": "팬 규칙 가이드: VAR, 핸드볼, 오프사이드 완벽 정리",
            "content": content,
            "metadata": {"match_date": MATCH_DATE, "pilot": True},
        }]
    return []


def generate_pre_generated_qa(model, collected: dict) -> list[dict]:
    """사전 생성 Q&A 20+ 건 생성."""
    log.info("[생성] 사전 Q&A 문서")
    docs = []

    standings_text = _format_standings_for_prompt(
        collected.get("standings", []),
        highlight_teams=["Man United", "Man Utd", "Aston Villa"],
    )
    manu_matches_text = _format_matches_for_prompt(collected.get("manu_matches", []))
    villa_matches_text = _format_matches_for_prompt(collected.get("villa_matches", []))
    manu_stats_text = _format_stats_for_prompt(collected.get("manu_stats", []))
    villa_stats_text = _format_stats_for_prompt(collected.get("villa_stats", []))
    manu_squad_text = _format_squad_for_prompt(collected.get("manu_squad"))
    villa_squad_text = _format_squad_for_prompt(collected.get("villa_squad"))

    context_block = f"""=== 데이터 컨텍스트 ===
EPL 순위표:
{standings_text}

맨유 최근 경기:
{manu_matches_text}

빌라 최근 경기:
{villa_matches_text}

맨유 시즌 통계:
{manu_stats_text}

빌라 시즌 통계:
{villa_stats_text}

맨유 스쿼드:
{manu_squad_text}

빌라 스쿼드:
{villa_squad_text}
=== 데이터 끝 ==="""

    questions = [
        "맨유 이번 시즌 성적은?",
        "에메리 감독의 전술 스타일은?",
        "캐릭 감독은 어떤 축구를 하나?",
        "맨유 vs 아스톤빌라 전적은?",
        "빌라 주요 부상자는?",
        "이번 경기 핵심 매치업은?",
        "맨유 최근 폼은?",
        "아스톤빌라 최근 폼은?",
        "UCL 진출 가능성은?",
        "브루노 페르난데스 이번 시즌은?",
        "올리 왓킨스 어떤 선수야?",
        "디알로 어떤 선수야?",
        "메이누 어떤 선수야?",
        "맨유 약점은?",
        "빌라 강점은?",
        "올드 트래포드 경기 분위기는?",
        "VAR 판정 기준은?",
        "맨유 이적 루머 정리",
        "빌라 이적 루머 정리",
        "이번 경기 승부 예측",
    ]

    # 배치로 생성 (5개씩)
    for batch_start in range(0, len(questions), 5):
        batch_qs = questions[batch_start:batch_start + 5]
        q_list = "\n".join(f"{i+1}. {q}" for i, q in enumerate(batch_qs))

        prompt = f"""당신은 축구 전문가이자 팬 Q&A 답변자입니다. 2026년 3월 15일 맨체스터 유나이티드 vs 아스톤 빌라 경기와 관련하여 다음 질문에 답변해주세요.

{context_block}

질문 목록:
{q_list}

각 질문에 대해 다음 형식으로 한국어로 답변해주세요:

---ANSWER_START---
질문번호: (1-5)
답변: (200-400자, 팬 친화적이면서 정확한 정보 기반)
---ANSWER_END---

데이터에 없는 내용은 일반적인 축구 지식으로 보충하되, 추측은 "~로 예상됩니다" 형식으로 표현하세요."""

        response_text = _generate(model, prompt, TEMP_FAN)
        if not response_text:
            continue

        # 응답 파싱
        parts = response_text.split("---ANSWER_START---")
        for i, part in enumerate(parts[1:]):  # 첫 번째는 빈 문자열
            end_idx = part.find("---ANSWER_END---")
            answer_block = part[:end_idx].strip() if end_idx > 0 else part.strip()

            # 답변 내용 추출
            answer_lines = answer_block.split("\n")
            answer_content = ""
            for line in answer_lines:
                if line.strip().startswith("답변:"):
                    answer_content = line.strip()[3:].strip()
                elif answer_content:
                    answer_content += "\n" + line.strip()

            if not answer_content:
                # 파싱 실패 시 전체 블록 사용
                answer_content = answer_block

            q_idx = min(i, len(batch_qs) - 1)
            question = batch_qs[q_idx]

            docs.append({
                "doc_type": "pre_generated_qa",
                "ref_id": None,
                "title": question,
                "content": answer_content,
                "metadata": {
                    "match_date": MATCH_DATE,
                    "question": question,
                    "pilot": True,
                },
            })
            log.info(f"    ✓ Q&A: {question} ({len(answer_content)}자)")

        time.sleep(2)

    return docs


def run_document_generation(collected: dict) -> list[dict]:
    """PART 2 전체 문서 생성 실행."""
    log.info("=" * 60)
    log.info("PART 2: AI 문서 생성 시작 (Gemini Flash)")
    log.info("=" * 60)

    model = _init_gemini()
    all_docs: list[dict] = []

    generators = [
        ("manager_analysis", lambda: generate_manager_analysis(model, collected)),
        ("tactical_preview", lambda: generate_tactical_preview(model, collected)),
        ("h2h_analysis", lambda: generate_h2h_analysis(model, collected)),
        ("match_preview", lambda: generate_match_preview(model, collected)),
        ("season_context", lambda: generate_season_context(model, collected)),
        ("fan_player_profile", lambda: generate_player_profiles(model, collected)),
        ("fan_tactical_guide", lambda: generate_fan_tactical_guide(model, collected)),
        ("form_analysis", lambda: generate_form_analysis(model, collected)),
        ("rules_explainer", lambda: generate_rules_explainer(model)),
        ("pre_generated_qa", lambda: generate_pre_generated_qa(model, collected)),
    ]

    for name, gen_fn in generators:
        try:
            docs = gen_fn()
            all_docs.extend(docs)
            log.info(f"  [{name}] {len(docs)}건 생성 완료")
        except Exception as e:
            log.error(f"  [{name}] 생성 실패: {e}\n{traceback.format_exc()}")

    log.info(f"PART 2 완료: 총 {len(all_docs)}건 문서 생성")
    return all_docs


# ══════════════════════════════════════════════════
# PART 3: 임베딩 & Supabase 저장
# ══════════════════════════════════════════════════

def _load_embed_model():
    """SentenceTransformer 모델 로드."""
    from sentence_transformers import SentenceTransformer
    log.info(f"임베딩 모델 로드: {EMBED_MODEL}")
    return SentenceTransformer(EMBED_MODEL)


def embed_and_store(docs: list[dict]) -> int:
    """문서 임베딩 + Supabase documents 테이블에 INSERT (기존 문서 유지)."""
    if not docs:
        log.info("저장할 문서 없음")
        return 0

    log.info("=" * 60)
    log.info(f"PART 3: 임베딩 & 저장 ({len(docs)}건)")
    log.info("=" * 60)

    model = _load_embed_model()
    sb = get_supabase()
    stored = 0
    INSERT_CHUNK = 30

    for i in range(0, len(docs), BATCH_SIZE):
        batch = docs[i:i + BATCH_SIZE]
        texts = [d["content"] for d in batch]
        embeddings = model.encode(texts, show_progress_bar=False)

        rows = []
        for doc, emb in zip(batch, embeddings):
            vec_str = "[" + ",".join(str(x) for x in emb.tolist()) + "]"
            # 실제 documents 테이블 스키마: id, collection, content, metadata, created_at, embedding
            meta = dict(doc.get("metadata", {}))
            meta["title"] = doc["title"]
            meta["doc_type"] = doc["doc_type"]
            if doc.get("ref_id"):
                meta["ref_id"] = doc["ref_id"]
            rows.append({
                "collection": doc["doc_type"],
                "content": doc["content"],
                "embedding": vec_str,
                "metadata": meta,
            })

        # 배치 insert
        for j in range(0, len(rows), INSERT_CHUNK):
            chunk = rows[j:j + INSERT_CHUNK]
            try:
                sb.table("documents").insert(chunk).execute()
                stored += len(chunk)
            except Exception as e:
                log.warning(f"  배치 insert 실패, 건별 insert로 폴백: {e}")
                for row in chunk:
                    try:
                        sb.table("documents").insert(row).execute()
                        stored += 1
                    except Exception as row_err:
                        log.warning(f"    문서 저장 실패 [{row.get('title', '?')}]: {row_err}")

        log.info(
            f"  임베딩 저장 진행: {min(i + BATCH_SIZE, len(docs))}/{len(docs)} "
            f"(누적 {stored}건)"
        )

    log.info(f"PART 3 완료: {stored}/{len(docs)}건 저장")
    return stored


# ══════════════════════════════════════════════════
# 메인 실행
# ══════════════════════════════════════════════════

def main():
    """파일럿 매치 준비 전체 파이프라인 실행."""
    log.info("=" * 60)
    log.info("La Paz Pilot Match Prep")
    log.info("맨체스터 유나이티드 vs 아스톤 빌라 (2026-03-15)")
    log.info("=" * 60)

    start_time = time.time()

    # PART 1: 데이터 수집
    collected = run_data_collection()

    # PART 2: AI 문서 생성
    all_docs = run_document_generation(collected)

    # PART 3: 임베딩 & 저장
    stored = embed_and_store(all_docs)

    elapsed = time.time() - start_time
    log.info("=" * 60)
    log.info(f"파일럿 매치 준비 완료!")
    log.info(f"  생성 문서: {len(all_docs)}건")
    log.info(f"  저장 문서: {stored}건")
    log.info(f"  소요 시간: {elapsed:.1f}초 ({elapsed/60:.1f}분)")
    log.info("=" * 60)

    # 문서 유형별 집계
    type_counts: dict[str, int] = {}
    for d in all_docs:
        dt = d["doc_type"]
        type_counts[dt] = type_counts.get(dt, 0) + 1
    log.info("문서 유형별 집계:")
    for dt, count in sorted(type_counts.items()):
        log.info(f"  {dt}: {count}건")


if __name__ == "__main__":
    main()
