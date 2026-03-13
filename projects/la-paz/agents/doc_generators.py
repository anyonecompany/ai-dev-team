#!/usr/bin/env python3
"""La Paz Agent 4: 문서 생성 모듈

agent_4_document.py에서 분리된 문서 생성 함수들.
각 함수는 DB 원본 테이블에서 자연어 문서를 생성하여 반환합니다.

개선 사항 (v2):
- player_profile: player_season_stats의 meta.player_name으로 매칭 보강
- team_profile: competition_id → 리그 풀네임 해소
- league_standing: competition_id 기반 리그별 분리
- scorer_ranking: 리그 약칭 → 풀네임 매핑
- match_report: 누락 경기 없이 전건 처리
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from shared_config import (
    get_agent_logger,
    sb_select,
    get_supabase,
)

log = get_agent_logger("agent_4")

# ── 리그 약칭 → 풀네임 매핑 ────────────────────────
COMP_ABBR_MAP: dict[str, str] = {
    "PL": "Premier League",
    "PD": "La Liga",
    "SA": "Serie A",
    "BL1": "Bundesliga",
    "FL1": "Ligue 1",
    "CL": "Champions League",
    "ELC": "EFL Championship",
    "PPL": "Primeira Liga",
    "DED": "Eredivisie",
    "BSA": "Brasileirão Série A",
}


def _resolve_team(name: str, lookup: dict) -> str:
    """팀명 → canonical 이름 변환."""
    if not name:
        return "Unknown"
    return lookup.get(name.strip(), name.strip())


def _resolve_comp_name(
    meta: dict,
    comp_id: str | None,
    comps: dict,
) -> str:
    """리그 이름 해소: meta.competition 약칭 → 풀네임 → competition_id 조회."""
    # 1) meta에서 약칭 확인
    abbr = meta.get("competition", "")
    if abbr and abbr in COMP_ABBR_MAP:
        return COMP_ABBR_MAP[abbr]
    # 2) meta.league 확인
    league = meta.get("league", "")
    if league and league != "?":
        return league
    # 3) competition_id로 조회
    if comp_id and comp_id in comps:
        return comps[comp_id].get("name", abbr or "Unknown")
    return abbr or "Unknown"


# ── Key Events Loader ────────────────────────────
_KEY_EVENT_TYPES = [
    "Goal", "Own Goal", "Shot",
    "Yellow Card", "Red Card", "Second Yellow",
    "Bad Behaviour",
]
_KEY_EVENT_COLS = "id,match_id,minute,type,player_name,team_name,outcome,created_at"


def _fetch_key_events() -> list[dict]:
    """골/카드 이벤트만 DB에서 페이징 조회."""
    sb = get_supabase()
    PAGE = 1000
    all_rows: list[dict] = []
    offset = 0

    while True:
        resp = (
            sb.table("match_events")
            .select(_KEY_EVENT_COLS)
            .in_("type", _KEY_EVENT_TYPES)
            .range(offset, offset + PAGE - 1)
            .execute()
        )
        rows = resp.data or []
        all_rows.extend(rows)
        if len(rows) < PAGE:
            break
        offset += PAGE

    log.info(f"  주요 이벤트 로드: {len(all_rows)}건")
    return all_rows


# ── 공유 데이터 로더 ─────────────────────────────
def _load_shared_data() -> dict:
    """여러 생성 함수에서 공통으로 쓰는 데이터 로드 (1회 호출)."""
    teams_raw = sb_select("teams", limit=0)
    comps_raw = sb_select("competitions", limit=0)
    return {
        "teams": {t["id"]: t for t in teams_raw},
        "teams_list": teams_raw,
        "comps": {c["id"]: c for c in comps_raw},
    }


# ══════════════════════════════════════════════════
# 1. match_report
# ══════════════════════════════════════════════════
def generate_match_reports(
    team_lookup: dict,
    shared: dict | None = None,
) -> list[dict]:
    """경기 결과 + match_events → match_report 문서."""
    log.info("match_report 문서 생성 중...")
    matches = sb_select("matches", limit=0)
    teams = shared["teams"] if shared else {t["id"]: t for t in sb_select("teams", limit=0)}
    comps = shared["comps"] if shared else {c["id"]: c for c in sb_select("competitions", limit=0)}

    all_events = _fetch_key_events()
    events_by_match: dict[str, list] = {}
    for e in all_events:
        mid = e.get("match_id")
        if mid:
            events_by_match.setdefault(mid, []).append(e)

    docs = []
    for m in matches:
        home = teams.get(m.get("home_team_id"), {})
        away = teams.get(m.get("away_team_id"), {})
        home_name = _resolve_team(home.get("canonical", "홈팀"), team_lookup)
        away_name = _resolve_team(away.get("canonical", "원정팀"), team_lookup)

        h_score = m.get("home_score")
        a_score = m.get("away_score")
        date_str = m.get("match_date", "날짜 미상")
        comp = comps.get(m.get("competition_id"), {})
        comp_name = comp.get("name", "")

        if h_score is not None and a_score is not None:
            result = f"{h_score}-{a_score}"
            if h_score > a_score:
                winner = f"{home_name} 승리"
            elif h_score < a_score:
                winner = f"{away_name} 승리"
            else:
                winner = "무승부"
        else:
            result = "미확정"
            winner = "결과 미확정"

        lines = [f"{date_str} {home_name} vs {away_name}"]
        if comp_name:
            lines.append(f"대회: {comp_name}")
        if m.get("matchday"):
            lines.append(f"라운드: {m['matchday']}")
        lines.append(f"결과: {result} ({winner})")
        if m.get("stadium"):
            lines.append(f"경기장: {m['stadium']}")
        if m.get("referee"):
            lines.append(f"심판: {m['referee']}")
        if m.get("attendance"):
            lines.append(f"관중: {m['attendance']:,}명")

        # 주요 이벤트
        m_events = events_by_match.get(m["id"], [])
        goals = sorted(
            [e for e in m_events
             if ((e.get("type") or "").lower() == "shot"
                 and (e.get("outcome") or "").lower() == "goal")
             or (e.get("type") or "").lower() in ("goal", "own goal")],
            key=lambda e: e.get("minute", 0),
        )
        cards = [e for e in m_events
                 if "card" in (e.get("type") or "").lower()
                 or (e.get("type") or "").lower() == "bad behaviour"]

        if goals:
            lines.append("골:")
            for g in goals:
                pname = g.get("player_name", "?")
                tname = g.get("team_name", "")
                minute = g.get("minute", "?")
                lines.append(f"  {minute}분 {pname} ({tname})")
        if cards:
            lines.append("카드:")
            for c in sorted(cards, key=lambda e: e.get("minute", 0))[:10]:
                lines.append(
                    f"  {c.get('minute', '?')}분 "
                    f"{c.get('player_name', '?')} ({c.get('team_name', '')})"
                )

        content = "\n".join(lines)
        docs.append({
            "doc_type": "match_report",
            "ref_id": m["id"],
            "title": f"{home_name} vs {away_name} ({date_str})",
            "content": content,
            "metadata": {
                "match_date": date_str,
                "home_team": home_name,
                "away_team": away_name,
                "score": result,
                "competition": comp_name,
            },
        })

    log.info(f"  match_report: {len(docs)}건 (원본 {len(matches)}건)")
    return docs


# ══════════════════════════════════════════════════
# 2. team_profile
# ══════════════════════════════════════════════════
def generate_team_profiles(
    team_lookup: dict,
    shared: dict | None = None,
) -> list[dict]:
    """팀 정보 + 시즌 통계 → team_profile 문서.

    개선: competition_id로 리그 풀네임 해소.
    """
    log.info("team_profile 문서 생성 중...")
    teams = shared["teams_list"] if shared else sb_select("teams", limit=0)
    team_stats = sb_select("team_season_stats", limit=0)
    comps = shared["comps"] if shared else {c["id"]: c for c in sb_select("competitions", limit=0)}

    stats_by_team: dict[str, list] = {}
    for s in team_stats:
        tid = s.get("team_id")
        if tid:
            stats_by_team.setdefault(tid, []).append(s)

    docs = []
    for t in teams:
        canonical = t["canonical"]
        stats_list = stats_by_team.get(t["id"], [])

        lines = [f"팀: {canonical}"]
        if t.get("country"):
            lines.append(f"국가: {t['country']}")
        if t.get("stadium"):
            lines.append(f"홈구장: {t['stadium']}")
        if t.get("founded_year"):
            lines.append(f"설립: {t['founded_year']}년")
        aliases = t.get("aliases") or []
        if aliases and aliases != [canonical]:
            lines.append(f"별칭: {', '.join(aliases)}")

        if stats_list:
            lines.append("")
            lines.append("== 시즌 성적 ==")
            for s in stats_list:
                meta = s.get("meta", {})
                season = meta.get("season", "?")
                # 개선: competition_id로 리그 풀네임 해소
                league = _resolve_comp_name(meta, s.get("competition_id"), comps)
                pos = s.get("position", "?")
                played = s.get("played", 0)
                w = s.get("won", 0)
                d = s.get("draw", 0)
                lo = s.get("lost", 0)
                pts = s.get("points", 0)
                gf = s.get("goals_for", 0)
                ga = s.get("goals_against", 0)
                gd = s.get("goal_diff", 0)

                stat_line = (
                    f"{season} {league}: {pos}위, {played}경기 "
                    f"(승{w} 무{d} 패{lo}), "
                    f"승점 {pts}, 득점 {gf}, 실점 {ga}, 골득실 {gd:+d}"
                )
                xg_f = s.get("xg_for")
                xg_a = s.get("xg_against")
                if xg_f is not None:
                    stat_line += f", xG {xg_f:.1f}"
                if xg_a is not None:
                    stat_line += f", xGA {xg_a:.1f}"
                lines.append(stat_line)

        content = "\n".join(lines)
        docs.append({
            "doc_type": "team_profile",
            "ref_id": t["id"],
            "title": f"{canonical} 프로필",
            "content": content,
            "metadata": {
                "team": canonical,
                "country": t.get("country"),
                "stadium": t.get("stadium"),
            },
        })

    log.info(f"  team_profile: {len(docs)}건")
    return docs


# ══════════════════════════════════════════════════
# 3. player_profile
# ══════════════════════════════════════════════════
def generate_player_profiles(
    team_lookup: dict,
    shared: dict | None = None,
) -> list[dict]:
    """선수 정보 + 시즌 통계 + 이벤트 → player_profile 문서.

    개선:
    - player_season_stats.meta.player_name으로 역매칭 (player_id 없는 경우 보강)
    - 리그 약칭 → 풀네임 변환
    - 통계 풍부한 선수에 시즌별 상세 기록 포함
    """
    log.info("player_profile 문서 생성 중...")
    players_raw = sb_select("players", limit=0)
    player_stats = sb_select("player_season_stats", limit=0)
    teams = shared["teams"] if shared else {t["id"]: t for t in sb_select("teams", limit=0)}
    comps = shared["comps"] if shared else {c["id"]: c for c in sb_select("competitions", limit=0)}

    # ── 선수 병합 (StatsBomb + football-data 중복 제거) ──
    merged_players: dict[str, dict] = {}
    for p in players_raw:
        name = p.get("name", "").strip()
        if not name:
            continue
        if name not in merged_players:
            merged_players[name] = {
                "ids": [],
                "name": name,
                "full_name": p.get("full_name") or "",
                "nationality": (p.get("nationality") or "").strip(),
                "position": p.get("position"),
                "birth_date": p.get("birth_date"),
                "height_cm": p.get("height_cm"),
                "preferred_foot": p.get("preferred_foot"),
                "meta": p.get("meta") or {},
            }
        mp = merged_players[name]
        mp["ids"].append(p["id"])
        if not mp["full_name"] and p.get("full_name"):
            mp["full_name"] = p["full_name"]
        nat = (p.get("nationality") or "").strip()
        if not mp["nationality"] and nat and nat != name and nat != mp["full_name"]:
            mp["nationality"] = nat
        if not mp["position"] and p.get("position"):
            mp["position"] = p["position"]
        if not mp["birth_date"] and p.get("birth_date"):
            mp["birth_date"] = p["birth_date"]
        if not mp["height_cm"] and p.get("height_cm"):
            mp["height_cm"] = p["height_cm"]
        if not mp["preferred_foot"] and p.get("preferred_foot"):
            mp["preferred_foot"] = p["preferred_foot"]
        p_meta = p.get("meta") or {}
        if not mp["meta"].get("team") and p_meta.get("team"):
            mp["meta"]["team"] = p_meta["team"]
        if not mp["meta"].get("nationality") and p_meta.get("nationality"):
            mp["meta"]["nationality"] = p_meta["nationality"]

    log.info(f"  선수 병합: {len(players_raw)} → {len(merged_players)}명")

    # ── 시즌 통계 매칭 ──
    # 방법 1: player_id → name 매핑
    pid_to_name: dict[str, str] = {}
    for name, mp in merged_players.items():
        for pid in mp["ids"]:
            pid_to_name[pid] = name

    stats_by_name: dict[str, list] = {}
    unmatched_stats: list[dict] = []

    for s in player_stats:
        pid = s.get("player_id")
        name = pid_to_name.get(pid)
        if name:
            stats_by_name.setdefault(name, []).append(s)
        else:
            unmatched_stats.append(s)

    # 방법 2: meta.player_name으로 역매칭 (player_id 매칭 실패 건)
    matched_by_meta = 0
    for s in unmatched_stats:
        meta_name = (s.get("meta") or {}).get("player_name", "")
        if meta_name and meta_name in merged_players:
            stats_by_name.setdefault(meta_name, []).append(s)
            matched_by_meta += 1

    if matched_by_meta:
        log.info(f"  meta.player_name 역매칭: {matched_by_meta}건 추가")

    stats_count = sum(len(v) for v in stats_by_name.values())
    log.info(f"  시즌 통계 매칭: {stats_count}건 → {len(stats_by_name)}명")

    # ── 골/카드 이벤트 ──
    key_events = _fetch_key_events()
    events_by_name: dict[str, list] = {}
    for e in key_events:
        etype = (e.get("type") or "").lower()
        outcome = (e.get("outcome") or "").lower()
        is_goal = (
            (etype == "shot" and outcome == "goal")
            or etype == "goal"
            or etype == "own goal"
        )
        is_card = "card" in etype or etype == "bad behaviour"
        if is_goal or is_card:
            pname = e.get("player_name")
            if pname:
                events_by_name.setdefault(pname, []).append(e)

    log.info(f"  주요 이벤트 선수 수: {len(events_by_name)}")

    # ── 1인 1문서 생성 ──
    docs = []
    for name, mp in merged_players.items():
        full_name = mp["full_name"]
        meta = mp["meta"]
        lines = [f"선수: {name}"]

        if full_name and full_name != name:
            lines.append(f"풀네임: {full_name}")

        nationality = mp["nationality"]
        if nationality and nationality not in (name, full_name):
            lines.append(f"국적: {nationality}")
        elif meta.get("nationality"):
            lines.append(f"국적: {meta['nationality']}")

        if mp["position"]:
            lines.append(f"포지션: {mp['position']}")

        # 소속팀 (최신 통계 기준)
        current_team = meta.get("team", "")
        p_stats = stats_by_name.get(name, [])
        if not current_team and p_stats:
            latest = p_stats[-1]
            s_meta = latest.get("meta", {})
            current_team = s_meta.get("team_name", "")
            if not current_team:
                tid = latest.get("team_id")
                if tid and tid in teams:
                    current_team = teams[tid].get("canonical", "")
        if current_team:
            lines.append(f"소속팀: {current_team}")

        if mp["birth_date"]:
            lines.append(f"생년월일: {mp['birth_date']}")
        if mp["height_cm"]:
            lines.append(f"신장: {int(mp['height_cm'])}cm")
        if mp["preferred_foot"]:
            lines.append(f"주발: {mp['preferred_foot']}")

        # 시즌별 기록 (개선: 리그 풀네임 + 중복 제거)
        if p_stats:
            lines.append("")
            lines.append("== 시즌별 기록 ==")
            seen_seasons: set[str] = set()
            for s in p_stats:
                s_meta = s.get("meta", {})
                season = s_meta.get("season", "?")
                comp_name = _resolve_comp_name(
                    s_meta, s.get("competition_id"), comps
                )
                team_name = s_meta.get("team_name", "")
                if not team_name:
                    tid = s.get("team_id")
                    if tid and tid in teams:
                        team_name = teams[tid].get("canonical", "")

                dedup_key = f"{season}_{comp_name}_{team_name}"
                if dedup_key in seen_seasons:
                    continue
                seen_seasons.add(dedup_key)

                apps = s.get("appearances") or 0
                minutes = s.get("minutes") or 0
                goals = s.get("goals") or 0
                assists = s.get("assists") or 0

                stat_line = (
                    f"{season} {comp_name} ({team_name}): "
                    f"{apps}경기"
                )
                if minutes:
                    stat_line += f" {minutes}분"
                stat_line += f", {goals}골 {assists}도움"
                xg = s.get("xg")
                xa = s.get("xa")
                if xg is not None:
                    stat_line += f", xG {xg:.1f}"
                if xa is not None:
                    stat_line += f", xA {xa:.1f}"
                penalties = s_meta.get("penalties")
                if penalties:
                    stat_line += f", PK {penalties}골"
                lines.append(stat_line)

        # 주요 이벤트 요약
        p_events = events_by_name.get(name, [])
        if p_events:
            goal_events = [
                e for e in p_events
                if ((e.get("type") or "").lower() == "shot"
                    and (e.get("outcome") or "").lower() == "goal")
                or (e.get("type") or "").lower() in ("goal", "own goal")
            ]
            card_events = [
                e for e in p_events
                if "card" in (e.get("type") or "").lower()
                or (e.get("type") or "").lower() == "bad behaviour"
            ]
            if goal_events:
                lines.append(f"이벤트 골 합계: {len(goal_events)}골")
            if card_events:
                lines.append(f"이벤트 카드 합계: {len(card_events)}장")

        content = "\n".join(lines)
        docs.append({
            "doc_type": "player_profile",
            "ref_id": mp["ids"][0],
            "title": f"{name} 프로필",
            "content": content,
            "metadata": {
                "player": name,
                "full_name": full_name if full_name != name else "",
                "position": mp["position"],
                "nationality": (
                    nationality
                    if nationality not in (name, full_name)
                    else meta.get("nationality", "")
                ),
                "team": current_team,
            },
        })

    log.info(f"  player_profile: {len(docs)}건")
    return docs


# ══════════════════════════════════════════════════
# 4. transfer_news
# ══════════════════════════════════════════════════
def generate_transfer_news(team_lookup: dict) -> list[dict]:
    """이적 정보 → transfer_news 문서."""
    log.info("transfer_news 문서 생성 중...")
    transfers = sb_select("transfers", limit=0)

    docs = []
    for tr in transfers:
        meta = tr.get("meta", {})
        player = meta.get("player_name", "선수 미상")
        from_team = _resolve_team(meta.get("from_team", ""), team_lookup)
        to_team = _resolve_team(meta.get("to_team", ""), team_lookup)
        fee_raw = meta.get("fee_raw", "비공개")
        t_type = tr.get("transfer_type", "permanent")

        content = (
            f"{player} 이적: {from_team} → {to_team}. "
            f"유형: {t_type}. 이적료: {fee_raw}. "
            f"시즌: {tr.get('season', '')}."
        )

        docs.append({
            "doc_type": "transfer_news",
            "ref_id": tr["id"],
            "title": f"{player} 이적 ({from_team} → {to_team})",
            "content": content,
            "metadata": {
                "player": player,
                "from_team": from_team,
                "to_team": to_team,
                "transfer_type": t_type,
            },
        })

    log.info(f"  transfer_news: {len(docs)}건")
    return docs


# ══════════════════════════════════════════════════
# 5. league_standing
# ══════════════════════════════════════════════════
def generate_league_standings(
    team_lookup: dict,
    shared: dict | None = None,
) -> list[dict]:
    """팀 시즌 통계 → league_standing 문서.

    개선: competition_id 기반으로 리그별 분리 + 리그 풀네임 해소.
    """
    log.info("league_standing 문서 생성 중...")
    team_stats = sb_select("team_season_stats", limit=0)
    teams = shared["teams"] if shared else {t["id"]: t for t in sb_select("teams", limit=0)}
    comps = shared["comps"] if shared else {c["id"]: c for c in sb_select("competitions", limit=0)}

    # 개선: competition_id + season 기준 그룹화 (meta.league 의존 제거)
    grouped: dict[str, list] = {}
    group_info: dict[str, dict] = {}

    for s in team_stats:
        meta = s.get("meta", {})
        comp_id = s.get("competition_id", "")
        season = meta.get("season", "?")

        # 리그명 해소
        comp_name = _resolve_comp_name(meta, comp_id, comps)
        key = f"{comp_name}_{season}"
        grouped.setdefault(key, []).append(s)
        group_info[key] = {"comp_name": comp_name, "season": season}

    docs = []
    for key, stats in grouped.items():
        info = group_info[key]
        comp_name = info["comp_name"]
        season = info["season"]

        sorted_stats = sorted(stats, key=lambda x: x.get("position") or 999)

        lines = [f"{comp_name} {season} 시즌 순위표"]
        lines.append(f"총 {len(sorted_stats)}팀")
        lines.append("")

        for s in sorted_stats:
            team = teams.get(s.get("team_id"), {})
            name = _resolve_team(team.get("canonical", "?"), team_lookup)
            pos = s.get("position", "?")
            pts = s.get("points", 0)
            played = s.get("played", 0)
            w = s.get("won", 0)
            d = s.get("draw", 0)
            lo = s.get("lost", 0)
            gf = s.get("goals_for", 0)
            ga = s.get("goals_against", 0)
            gd = s.get("goal_diff", 0)
            lines.append(
                f"{pos}. {name} - 승점 {pts}, "
                f"{played}경기 (승{w} 무{d} 패{lo}), "
                f"득{gf} 실{ga} 골득실{gd:+d}"
            )

        content = "\n".join(lines)
        docs.append({
            "doc_type": "league_standing",
            "ref_id": key,
            "title": f"{comp_name} {season} 순위표",
            "content": content,
            "metadata": {
                "competition": comp_name,
                "season": season,
                "team_count": len(sorted_stats),
            },
        })

    log.info(f"  league_standing: {len(docs)}건 (이전: 1건 → {len(docs)}건)")
    return docs


# ══════════════════════════════════════════════════
# 6. scorer_ranking
# ══════════════════════════════════════════════════
def generate_scorer_rankings(
    team_lookup: dict,
    shared: dict | None = None,
) -> list[dict]:
    """리그별 득점 순위 문서 (개선: 리그 풀네임 + 어시스트 순위 추가)."""
    log.info("scorer_ranking 문서 생성 중...")
    stats = sb_select("player_season_stats", limit=0)
    teams = shared["teams"] if shared else {t["id"]: t for t in sb_select("teams", limit=0)}
    comps = shared["comps"] if shared else {c["id"]: c for c in sb_select("competitions", limit=0)}
    players = {p["id"]: p for p in sb_select("players", limit=0)}

    # meta.competition 약칭 기준 그룹화
    by_comp: dict[str, list] = {}
    for s in stats:
        s_meta = s.get("meta", {})
        comp_name = _resolve_comp_name(s_meta, s.get("competition_id"), comps)
        by_comp.setdefault(comp_name, []).append(s)

    docs = []
    for comp_name, comp_stats in by_comp.items():
        if not comp_name or comp_name == "Unknown":
            continue

        # 시즌 정보
        meta0 = comp_stats[0].get("meta", {}) if comp_stats else {}
        season = meta0.get("season", "?")

        # ── 득점 순위 ──
        sorted_goals = sorted(
            comp_stats,
            key=lambda x: (x.get("goals") or 0, x.get("assists") or 0),
            reverse=True,
        )

        lines = [f"{comp_name} {season} 시즌 득점 순위"]
        lines.append("")
        for i, s in enumerate(sorted_goals[:30], 1):
            player = players.get(s.get("player_id"), {})
            player_name = (
                player.get("name")
                or (s.get("meta") or {}).get("player_name", "?")
            )
            team = teams.get(s.get("team_id"), {})
            team_name = _resolve_team(
                team.get("canonical")
                or (s.get("meta") or {}).get("team_name", ""),
                team_lookup,
            )
            goals = s.get("goals") or 0
            assists = s.get("assists") or 0
            apps = s.get("appearances") or 0
            penalties = (s.get("meta") or {}).get("penalties")
            pen_str = f" (PK {penalties})" if penalties else ""
            lines.append(
                f"{i}. {player_name} ({team_name}) - "
                f"{goals}골{pen_str} {assists}도움 {apps}경기"
            )

        content = "\n".join(lines)
        docs.append({
            "doc_type": "scorer_ranking",
            "ref_id": f"scorer_{comp_name}_{season}",
            "title": f"{comp_name} {season} 득점 순위",
            "content": content,
            "metadata": {
                "competition": comp_name,
                "season": season,
                "type": "goals",
            },
        })

        # ── 어시스트 순위 (추가) ──
        sorted_assists = sorted(
            comp_stats,
            key=lambda x: (x.get("assists") or 0, x.get("goals") or 0),
            reverse=True,
        )

        a_lines = [f"{comp_name} {season} 시즌 어시스트 순위"]
        a_lines.append("")
        for i, s in enumerate(sorted_assists[:20], 1):
            player = players.get(s.get("player_id"), {})
            player_name = (
                player.get("name")
                or (s.get("meta") or {}).get("player_name", "?")
            )
            team = teams.get(s.get("team_id"), {})
            team_name = _resolve_team(
                team.get("canonical")
                or (s.get("meta") or {}).get("team_name", ""),
                team_lookup,
            )
            goals = s.get("goals") or 0
            assists = s.get("assists") or 0
            apps = s.get("appearances") or 0
            a_lines.append(
                f"{i}. {player_name} ({team_name}) - "
                f"{assists}도움 {goals}골 {apps}경기"
            )

        a_content = "\n".join(a_lines)
        docs.append({
            "doc_type": "scorer_ranking",
            "ref_id": f"assist_{comp_name}_{season}",
            "title": f"{comp_name} {season} 어시스트 순위",
            "content": a_content,
            "metadata": {
                "competition": comp_name,
                "season": season,
                "type": "assists",
            },
        })

    log.info(f"  scorer_ranking: {len(docs)}건 (득점+어시스트)")
    return docs


# ══════════════════════════════════════════════════
# 7. article
# ══════════════════════════════════════════════════
def generate_article_docs() -> list[dict]:
    """RSS 기사 → article 문서 (임베딩용)."""
    log.info("article 문서 생성 중...")
    articles = sb_select("articles", limit=0)

    docs = []
    for a in articles:
        content = a.get("summary") or a.get("title", "")
        if not content:
            continue

        docs.append({
            "doc_type": "article",
            "ref_id": a["id"],
            "title": a["title"][:500],
            "content": content[:3000],
            "metadata": {
                "source": a.get("source_name"),
                "url": a.get("url"),
                "published_at": a.get("published_at"),
            },
        })

    log.info(f"  article: {len(docs)}건")
    return docs
