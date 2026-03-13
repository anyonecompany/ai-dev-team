#!/usr/bin/env python3
"""La Paz Agent 5: FastAPI REST + RAG + B2B API

LLM : Gemini 2.0 Flash (primary) via OpenAI SDK, DeepSeek V3.2 (fallback)
Auth: Supabase Auth (fan) / API-key (B2B)
RAG : 하이브리드 검색 (pgvector + 키워드 ILIKE) + Gemini 생성

Endpoints
---------
Fan (B2C)
  POST /chat              RAG 채팅
  GET  /matches           경기 목록
  GET  /teams             팀 목록
  GET  /teams/{id}        팀 상세
  GET  /players/{id}      선수 상세
  GET  /search            시맨틱 검색 (GET ?q=)
  POST /predictions       팬 경기 예측

B2B
  GET  /b2b/trends        트렌드 스냅샷
  GET  /b2b/fan-segments  팬 세그먼트
  GET  /b2b/entity-buzz   엔티티 버즈 랭킹
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from shared_config import (
    get_agent_logger,
    publish_status,
    wait_for_agent,
    get_supabase,
    track_fan_event,
    DEEPSEEK_API_KEY,
    GOOGLE_API_KEY,
)

log = get_agent_logger("agent_5")

from fastapi import FastAPI, Depends, Header, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# ── App ──────────────────────────────────────────
app = FastAPI(title="La Paz — Football AI", version="2.0.0")

import os as _os
_CORS_ORIGINS = _os.getenv(
    "CORS_ORIGINS",
    "http://localhost:3000,http://localhost:8000",
).split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=_CORS_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True,
)

# ── State ────────────────────────────────────────
_st: dict = {"model": None, "ready": False, "queries": 0, "t0": None}
EMBED_MODEL = "paraphrase-multilingual-MiniLM-L12-v2"

# ── LLM System Prompt (고정 prefix → 캐시히트율 극대화) ──
SYSTEM_PREFIX = (
    "너는 La Paz, 전문 축구 AI 어시스턴트야.\n"
    "DB 데이터와 웹검색 결과를 활용해서 모든 축구 관련 질문에 정확하게 답변해.\n"
    "한국어로 자연스럽게 답변하되, 선수 이름은 원어 표기도 병기해.\n"
    "통계를 인용할 때는 출처와 시즌을 명시해.\n"
    "[web_search] 태그가 붙은 정보는 실시간 웹검색 결과입니다.\n"
    "DB 데이터와 웹검색 결과를 종합해서 답변하세요.\n"
    "규칙:\n"
    "- 관련 데이터에 정보가 있으면 반드시 활용하여 상세하게 답변해.\n"
    "- 수치와 날짜는 정확히 인용해.\n"
    "- 축구 용어를 자연스럽게 사용해.\n"
    "- 웹검색 결과를 인용할 때는 출처 URL을 명시해.\n"
    "- 확실하지 않은 정보는 추측임을 밝혀.\n"
)


# ── Pydantic ─────────────────────────────────────
class ChatReq(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000)
    session_id: str | None = None
    user_id: str | None = None
    top_k: int = Field(5, ge=1, le=20)

class ChatResp(BaseModel):
    answer: str
    sources: list[dict]
    model: str
    latency_ms: float

class PredictionReq(BaseModel):
    user_id: str
    match_id: str
    predicted_home: int = Field(..., ge=0)
    predicted_away: int = Field(..., ge=0)
    confidence: float = Field(0.5, ge=0, le=1)


# ── 한국어→영어 축구 엔티티 사전 ─────────────────
KOREAN_ENTITY_MAP: dict[str, str] = {
    # 선수
    "손흥민": "Heung-Min Son",
    "호날두": "Ronaldo",
    "메시": "Messi",
    "음바페": "Mbappe",
    "홀란드": "Haaland",
    "살라": "Salah",
    "벨링엄": "Bellingham",
    "비니시우스": "Vinicius",
    "페드리": "Pedri",
    "사카": "Saka",
    "파머": "Palmer",
    "포든": "Foden",
    "드브라위너": "De Bruyne",
    "누네스": "Nunez",
    "하베르츠": "Havertz",
    # 팀
    "맨유": "Manchester United",
    "맨시티": "Manchester City",
    "리버풀": "Liverpool",
    "첼시": "Chelsea",
    "아스날": "Arsenal",
    "토트넘": "Tottenham",
    "바르셀로나": "Barcelona",
    "레알마드리드": "Real Madrid",
    "바이에른": "Bayern",
    "PSG": "Paris Saint-Germain",
    # 대회
    "프리미어리그": "Premier League",
    "라리가": "La Liga",
    "분데스리가": "Bundesliga",
    "세리에A": "Serie A",
}

# ── 한국어→영어 축구 용어 사전 (벡터 검색용) ────
KOREAN_TERM_MAP: dict[str, str] = {
    "득점": "goals scoring",
    "순위": "ranking standings",
    "이적": "transfer",
    "부상": "injury",
    "프리미어리그": "Premier League",
    "라리가": "La Liga",
    "분데스리가": "Bundesliga",
    "세리에A": "Serie A",
    "리그앙": "Ligue 1",
    "챔피언스리그": "Champions League",
    "월드컵": "World Cup",
    "골": "goal",
    "어시스트": "assist",
    "도움": "assist",
    "경기": "match",
    "승리": "win victory",
    "패배": "defeat loss",
    "무승부": "draw",
    "승점": "points",
    "선수": "player",
    "감독": "manager coach",
    "골키퍼": "goalkeeper",
    "수비수": "defender",
    "미드필더": "midfielder",
    "공격수": "forward striker",
    "레드카드": "red card",
    "옐로카드": "yellow card",
    "페널티": "penalty",
    "프리킥": "free kick",
    "오프사이드": "offside",
    "해트트릭": "hat-trick",
    # 시간/일정
    "오늘": "today",
    "내일": "tomorrow",
    "어제": "yesterday",
    "결과": "results",
    "일정": "schedule fixtures",
    "진행하는": "today's",
    "누가 이겼어": "who won",
    "축구경기": "football match",
    "축구": "football",
    # 웹검색 보강
    "최근": "latest recent",
    "뉴스": "news",
    "하이라이트": "highlights",
    "스코어": "score",
    "선발": "lineup starting",
    "라인업": "lineup",
    "선발명단": "starting lineup",
    "실시간": "live",
    "중계": "live broadcast",
    "다음": "next upcoming",
    "지난": "last previous",
    # 불용어 (빈 문자열로 제거)
    "알려줘": "",
    "해줘": "",
    "뭐야": "",
    "어때": "",
    "인가요": "",
    "인가": "",
    "에서": "",
    "들": "",
    "을": "",
    "를": "",
    "의": "",
    "이": "",
    "가": "",
}


# ── RAG helpers (하이브리드 검색) ────────────────
def _embed(text: str) -> str:
    """임베딩 → pgvector 문자열 형식 반환."""
    vec = _st["model"].encode([text])[0].tolist()
    return "[" + ",".join(str(x) for x in vec) + "]"


def _translate_query_to_english(query: str) -> str:
    """쿼리를 영어로 변환. 긴 키워드부터 매칭하여 부분 충돌 방지."""
    en_query = query
    # 긴 키워드부터 매칭 (예: "이적"이 "이"보다 먼저 처리)
    for ko, en in sorted(KOREAN_ENTITY_MAP.items(), key=lambda x: len(x[0]), reverse=True):
        if ko in en_query:
            en_query = en_query.replace(ko, en)
    for ko, en in sorted(KOREAN_TERM_MAP.items(), key=lambda x: len(x[0]), reverse=True):
        if ko in en_query:
            en_query = en_query.replace(ko, en)
    return en_query


def _vector_search(query: str, top_k: int = 5, doc_type: str | None = None) -> list[dict]:
    """pgvector 시맨틱 검색. 한국어 쿼리를 영어로 변환 후 임베딩."""
    en_query = _translate_query_to_english(query)
    if en_query != query:
        log.debug(f"[벡터검색] 쿼리 변환: '{query[:60]}' → '{en_query[:60]}'")

    emb_str = _embed(en_query)
    sb = get_supabase()
    params: dict = {"query_embedding": emb_str, "match_count": top_k}
    if doc_type:
        params["filter_type"] = doc_type
    resp = sb.rpc("match_documents", params).execute()
    results = resp.data or []
    log.debug(f"[벡터검색] query='{en_query[:50]}' → {len(results)}건")
    for r in results[:3]:
        log.debug(f"  벡터: sim={r.get('similarity',0):.3f} title={r.get('title','')[:60]}")
    return results


def _translate_korean(query: str) -> list[tuple[str, str]]:
    """쿼리에서 한국어 엔티티를 영어로 변환. [(원본, 영어)] 반환.

    사전 매핑은 단어 단위뿐 아니라 연속 부분 문자열도 매칭한다.
    예: "레알마드리드의 비니시우스" → [("레알마드리드","Real Madrid"), ("비니시우스","Vinicius")]
    """
    pairs: list[tuple[str, str]] = []
    for ko, en in KOREAN_ENTITY_MAP.items():
        if ko in query:
            pairs.append((ko, en))
    return pairs


def _extract_entity_names(query: str) -> list[str]:
    """유저 메시지에서 선수명/팀명을 DB 매칭으로 추출. 한국어→영어 변환 포함."""
    sb = get_supabase()

    # 1) 한국어 사전 매핑 → 영어 검색어 확보
    ko_pairs = _translate_korean(query)
    translated = [en for _, en in ko_pairs]
    matched_ko = {ko for ko, _ in ko_pairs}
    log.debug(f"[한영변환] {ko_pairs}")

    # 2) 나머지 키워드 (사전에 매칭되지 않은 것만)
    raw_keywords = [w.strip() for w in query.split() if len(w.strip()) >= 2]
    remaining = [kw for kw in raw_keywords if kw not in matched_ko]

    # 검색할 키워드 = 영어 변환 + 원문 나머지
    search_keywords = translated + remaining

    names: list[str] = []
    for kw in search_keywords:
        # 복수 단어 → 각 단어별 AND ILIKE (이름 순서 무관 매칭)
        words = kw.split()

        # players 검색
        try:
            q = sb.table("players").select("name")
            for w in words:
                q = q.ilike("name", f"%{w}%")
            rows = q.limit(5).execute()
            names.extend(p["name"] for p in (rows.data or []))
        except Exception:
            pass

        # teams 검색
        try:
            if len(words) == 1:
                rows = sb.table("teams").select("canonical,name").or_(
                    f"canonical.ilike.%{kw}%,name.ilike.%{kw}%"
                ).limit(5).execute()
            else:
                # 복수 단어: canonical에 AND ILIKE
                q = sb.table("teams").select("canonical,name")
                for w in words:
                    q = q.ilike("canonical", f"%{w}%")
                rows = q.limit(5).execute()
            names.extend(t["canonical"] for t in (rows.data or []))
        except Exception:
            pass

    # 중복 제거
    seen: set[str] = set()
    unique: list[str] = []
    for n in names:
        if n not in seen:
            seen.add(n)
            unique.append(n)

    # 쿼리 단어 매칭 점수로 정렬 (높은 점수 = 더 관련성 높은 엔티티)
    # "Harry Kane" → "Harry"+"Kane" 2단어 매칭 > "Harry Winks" → "Harry"만 1단어 매칭
    query_words_lower = set()
    for kw in search_keywords:
        query_words_lower.update(w.lower() for w in kw.split())

    def _match_score(name: str) -> int:
        name_words = [w.lower() for w in name.split()]
        return sum(
            1 for qw in query_words_lower
            if any(qw in nw or nw in qw for nw in name_words)
        )

    unique.sort(key=_match_score, reverse=True)
    log.debug(f"[엔티티추출] search_keywords={search_keywords} → entities={unique}")
    return unique


def _keyword_search(query: str, top_k: int = 5) -> list[dict]:
    """키워드 ILIKE 검색: 엔티티 이름 + 한영 변환어 + 원문 키워드로 documents 검색."""
    sb = get_supabase()
    entity_names = _extract_entity_names(query)
    ko_translated = [en for _, en in _translate_korean(query)]
    raw_keywords = [w.strip() for w in query.split() if len(w.strip()) >= 2]
    # 엔티티명 우선, 그 다음 변환어, 마지막 원문
    search_terms = entity_names + ko_translated + raw_keywords
    # 중복 제거
    seen_terms: set[str] = set()
    unique_terms: list[str] = []
    for t in search_terms:
        if t not in seen_terms:
            seen_terms.add(t)
            unique_terms.append(t)
    search_terms = unique_terms[:15]  # 상한 15개

    results: list[dict] = []
    seen_ids: set[str] = set()

    for term in search_terms:
        try:
            resp = sb.table("documents")\
                     .select("id,doc_type,title,content,metadata")\
                     .ilike("content", f"%{term}%").limit(top_k).execute()
            for doc in (resp.data or []):
                if doc["id"] not in seen_ids:
                    seen_ids.add(doc["id"])
                    doc["similarity"] = 0.0  # 키워드 매치에는 유사도 없음
                    results.append(doc)
        except Exception:
            pass
        if len(results) >= top_k * 3:
            break

    log.debug(f"[키워드검색] terms={search_terms} → {len(results)}건")
    return results[:top_k * 2]


def _web_search(query: str, max_results: int = 5) -> list[dict]:
    """DuckDuckGo 웹검색. 한→영 변환 후 검색."""
    log.debug(f"[웹검색] 실행: query={query}")
    try:
        from ddgs import DDGS

        en_query = _translate_query_to_english(query)
        # 빈 토큰·여백 정리 후 football soccer 추가
        cleaned = " ".join(w for w in en_query.split() if w.strip())
        search_query = f"{cleaned} football soccer".strip()
        log.debug(f"[웹검색] 영어 변환: '{query}' → '{search_query}'")

        with DDGS() as ddgs:
            results = list(ddgs.text(search_query, max_results=max_results))

        docs = []
        for r in results:
            docs.append({
                "id": f"web_{abs(hash(r.get('href', '')))}",
                "doc_type": "web_search",
                "title": r.get("title", ""),
                "content": r.get("body", ""),
                "metadata": {"url": r.get("href", ""), "source": "web_search"},
                "similarity": 0.0,
            })
        log.debug(f"[웹검색] 결과: {len(docs)}건")
        return docs
    except Exception as e:
        log.warning(f"[웹검색] 실패: {e}")
        return []


def _fetch_entity_data(query: str) -> list[dict]:
    """쿼리에서 선수/팀 엔티티를 감지하고, DB에서 직접 통계를 가져와 컨텍스트 문서로 변환."""
    sb = get_supabase()
    ko_pairs = _translate_korean(query)
    if not ko_pairs:
        return []

    docs: list[dict] = []
    for ko_name, en_name in ko_pairs:
        words = en_name.split()

        # 선수 검색
        try:
            q = sb.table("players").select("id,name,full_name,nationality,position,birth_date,meta")
            for w in words:
                q = q.ilike("name", f"%{w}%")
            players = q.limit(3).execute().data or []
        except Exception:
            players = []

        for p in players:
            pid = p["id"]
            content_parts = [
                f"선수: {p['name']}",
                f"국적: {p.get('nationality') or '알 수 없음'}",
                f"포지션: {p.get('position') or '알 수 없음'}",
            ]
            if p.get("birth_date"):
                content_parts.append(f"생년월일: {p['birth_date']}")
            # meta에 팀 정보가 있을 수 있음
            if p.get("meta") and isinstance(p["meta"], dict) and p["meta"].get("team"):
                content_parts.append(f"팀(메타): {p['meta']['team']}")

            # 시즌 통계
            try:
                stats = sb.table("player_season_stats").select(
                    "appearances,goals,assists,minutes,xg,xa,meta"
                ).eq("player_id", pid).limit(5).execute().data or []
                if stats:
                    content_parts.append("\n시즌별 통계:")
                    for s in stats:
                        meta = s.get("meta") or {}
                        season = meta.get("season", "?")
                        team_name = meta.get("team_name", "")
                        comp = meta.get("competition", "")
                        line = f"  {season}"
                        if comp:
                            line += f" ({comp})"
                        if team_name:
                            line += f" {team_name}"
                        if s.get("appearances"):
                            line += f" | 출장: {s['appearances']}"
                        if s.get("goals") is not None:
                            line += f" | 골: {s['goals']}"
                        if s.get("assists") is not None:
                            line += f" | 어시스트: {s['assists']}"
                        if s.get("minutes"):
                            line += f" | 출장시간: {s['minutes']}분"
                        if s.get("xg"):
                            line += f" | xG: {s['xg']}"
                        content_parts.append(line)
            except Exception:
                pass

            content = "\n".join(content_parts)
            docs.append({
                "id": f"entity_player_{pid[:8]}",
                "doc_type": "player_data",
                "title": f"{p['name']} DB 통계",
                "content": content,
                "metadata": {"source": "database", "entity_type": "player"},
                "similarity": 1.0,  # 직접 매칭이므로 최고 유사도
            })
            break  # 엔티티당 1명만

        # 팀 검색
        if not players:
            try:
                if len(words) == 1:
                    teams = sb.table("teams").select("id,canonical,name,country,stadium").or_(
                        f"canonical.ilike.%{en_name}%,name.ilike.%{en_name}%"
                    ).limit(1).execute().data or []
                else:
                    q = sb.table("teams").select("id,canonical,name,country,stadium")
                    for w in words:
                        q = q.ilike("canonical", f"%{w}%")
                    teams = q.limit(1).execute().data or []
            except Exception:
                teams = []

            for t in teams:
                tid = t["id"]
                content_parts = [
                    f"팀: {t['canonical']}",
                    f"국가: {t.get('country', '알 수 없음')}",
                ]
                if t.get("stadium"):
                    content_parts.append(f"홈 구장: {t['stadium']}")

                # 시즌 통계
                try:
                    stats = sb.table("team_season_stats").select(
                        "wins,draws,losses,goals_for,goals_against,points,meta"
                    ).eq("team_id", tid).limit(3).execute().data or []
                    if stats:
                        content_parts.append("\n시즌별 통계:")
                        for s in stats:
                            meta = s.get("meta") or {}
                            season = meta.get("season", "?")
                            comp = meta.get("competition", "")
                            line = f"  {season}"
                            if comp:
                                line += f" ({comp})"
                            if s.get("wins") is not None:
                                line += f" | 승: {s['wins']}"
                            if s.get("draws") is not None:
                                line += f" | 무: {s['draws']}"
                            if s.get("losses") is not None:
                                line += f" | 패: {s['losses']}"
                            if s.get("goals_for") is not None:
                                line += f" | 득점: {s['goals_for']}"
                            if s.get("goals_against") is not None:
                                line += f" | 실점: {s['goals_against']}"
                            if s.get("points") is not None:
                                line += f" | 승점: {s['points']}"
                            content_parts.append(line)
                except Exception:
                    pass

                content = "\n".join(content_parts)
                docs.append({
                    "id": f"entity_team_{tid[:8]}",
                    "doc_type": "team_data",
                    "title": f"{t['canonical']} DB 통계",
                    "content": content,
                    "metadata": {"source": "database", "entity_type": "team"},
                    "similarity": 1.0,
                })
                break

    log.debug(f"[엔티티직접] {len(docs)}건 직접 조회: {[d['title'] for d in docs]}")
    return docs


def _retrieve(query: str, top_k: int = 5, doc_type: str | None = None) -> list[dict]:
    """하이브리드 검색: 엔티티 직접 조회 + 벡터 + 키워드 + 웹검색."""
    # 1) 엔티티 직접 조회 (최우선)
    entity_results = _fetch_entity_data(query)

    # 2) 벡터 + 키워드 검색
    vector_results = _vector_search(query, top_k, doc_type)
    keyword_results = _keyword_search(query, top_k)

    # RAG 결과 병합 (중복 제거)
    seen_ids = {r.get("id") for r in entity_results}
    rag_merged: list[dict] = []
    for vr in vector_results:
        if vr.get("id") not in seen_ids:
            seen_ids.add(vr["id"])
            rag_merged.append(vr)
    for kr in keyword_results:
        if kr.get("id") not in seen_ids:
            seen_ids.add(kr["id"])
            rag_merged.append(kr)

    # 3) 항상 웹검색 실행
    try:
        web_results = _web_search(query)
    except Exception as e:
        log.warning(f"[하이브리드] 웹검색 예외: {e}")
        web_results = []

    # 4) 병합 순서: 엔티티(최우선) → RAG(유사도순) → 웹
    # 엔티티 직접 매칭은 항상 최상위
    merged = list(entity_results)

    # RAG 결과: 유사도 높은 순 정렬
    rag_merged.sort(key=lambda x: x.get("similarity", 0), reverse=True)
    merged.extend(rag_merged)

    # 웹 결과는 마지막
    for wr in web_results:
        if wr.get("id") not in seen_ids:
            seen_ids.add(wr["id"])
            merged.append(wr)

    log.debug(
        f"[하이브리드] 엔티티={len(entity_results)} + 벡터={len(vector_results)} "
        f"+ 키워드={len(keyword_results)} + 웹={len(web_results)} → 병합={len(merged)}"
    )
    return merged[:top_k + 5]


def _build_web_fallback_response(question: str, contexts: list[dict]) -> str:
    """LLM 실패 시 웹검색 + DB 결과를 한국어로 정리하여 반환."""
    web_parts: list[str] = []
    db_parts: list[str] = []

    for c in contexts[:8]:
        doc_type = c.get("doc_type", "")
        title = c.get("title", "")
        content = c.get("content", "")
        meta = c.get("metadata") or {}

        if doc_type == "web_search":
            url = meta.get("url", "")
            snippet = content[:300].strip()
            entry = f"**{title}**\n{snippet}"
            if url:
                entry += f"\n(출처: {url})"
            web_parts.append(entry)
        else:
            snippet = content[:200].strip()
            if title or snippet:
                db_parts.append(f"- {title}: {snippet}" if title else f"- {snippet}")

    lines: list[str] = [f"'{question}'에 대한 검색 결과입니다.\n"]

    if web_parts:
        lines.append("[웹 검색 결과]")
        for i, wp in enumerate(web_parts, 1):
            lines.append(f"\n{i}. {wp}")

    if db_parts:
        lines.append("\n[데이터베이스 결과]")
        lines.extend(db_parts)

    if not web_parts and not db_parts:
        lines.append("관련 정보를 찾지 못했습니다.")

    lines.append(
        "\n---\nAI 요약이 일시적으로 불가하여 검색 결과를 직접 보여드립니다. "
        "잠시 후 다시 시도해 주세요."
    )
    return "\n".join(lines)


def _llm_generate(question: str, contexts: list[dict]) -> tuple[str, str]:
    """Gemini 2.0 Flash 생성. 실패 시 DeepSeek fallback. (answer, model_used) 반환."""
    ctx_parts = []
    for i, c in enumerate(contexts[:8], 1):
        doc_type = c.get("doc_type", "")
        title = c.get("title", "")
        content = c.get("content", "")
        meta = c.get("metadata") or {}
        header = f"### 문서 {i} [{doc_type}] {title}"
        if doc_type == "web_search" and meta.get("url"):
            header += f"\n출처: {meta['url']}"
        ctx_parts.append(f"{header}\n{content}")
    ctx = "\n\n".join(ctx_parts)
    user_content = f"## 관련 데이터\n{ctx}\n\n## 질문\n{question}"
    log.debug(f"[LLM] 컨텍스트 문서={len(contexts[:8])}건, 길이={len(ctx)}자, 질문='{question[:50]}'")
    messages = [
        {"role": "system", "content": SYSTEM_PREFIX},
        {"role": "user", "content": user_content},
    ]

    # Gemini (primary)
    gemini_err = None
    if GOOGLE_API_KEY:
        try:
            from openai import OpenAI
            client = OpenAI(api_key=GOOGLE_API_KEY, base_url="https://generativelanguage.googleapis.com/v1beta/openai/")
            resp = client.chat.completions.create(
                model="gemini-2.0-flash", messages=messages, max_tokens=1024, temperature=0.3,
            )
            return resp.choices[0].message.content, "gemini-2.0-flash"
        except Exception as e:
            gemini_err = e
            err_str = str(e).lower()
            if "429" in str(e) or "rate limit" in err_str or "quota" in err_str or "resource_exhausted" in err_str:
                log.warning(f"Gemini 429 Rate Limit → DeepSeek fallback 시도: {e}")
            else:
                log.warning(f"Gemini 오류 → DeepSeek fallback 시도: {e}")

    # DeepSeek fallback
    if DEEPSEEK_API_KEY:
        try:
            from openai import OpenAI
            client = OpenAI(api_key=DEEPSEEK_API_KEY, base_url="https://api.deepseek.com")
            resp = client.chat.completions.create(
                model="deepseek-chat", messages=messages, max_tokens=1024, temperature=0.3,
            )
            return resp.choices[0].message.content, "deepseek-chat"
        except Exception as e:
            log.warning(f"DeepSeek 오류: {e}")
    elif gemini_err:
        log.warning("DEEPSEEK_API_KEY 미설정 → DeepSeek fallback 불가")

    # No LLM fallback — 웹검색 결과를 한국어로 정리해서 제공
    return _build_web_fallback_response(question, contexts), "fallback-web"


# ── B2B auth ─────────────────────────────────────
def _verify_b2b_key(x_api_key: str = Header(...)):
    sb = get_supabase()
    rows = sb.table("b2b_clients").select("id,company_name,plan,rate_limit,is_active")\
             .eq("api_key", x_api_key).execute().data or []
    if not rows or not rows[0].get("is_active"):
        raise HTTPException(401, "Invalid or inactive API key")
    return rows[0]


# ── Fan endpoints ────────────────────────────────
@app.get("/health")
async def health():
    sb = get_supabase()
    doc_count = len(sb.table("documents").select("id", count="exact").limit(0).execute().data or [])
    return {"status": "healthy" if _st["ready"] else "initializing",
            "documents": doc_count, "queries": _st["queries"]}


@app.post("/chat", response_model=ChatResp)
async def chat(req: ChatReq):
    if not _st["ready"]:
        raise HTTPException(503, "시스템 초기화 중")
    t0 = time.time()
    _st["queries"] += 1

    contexts = _retrieve(req.message, req.top_k)
    answer, model_used = _llm_generate(req.message, contexts)
    elapsed = (time.time() - t0) * 1000

    # 팬 행동 추적
    track_fan_event("chat", user_id=req.user_id, session_id=req.session_id,
                    payload={"query": req.message[:200], "model": model_used,
                             "source_count": len(contexts)})

    # 채팅 이력 저장
    if req.session_id:
        try:
            sb = get_supabase()
            sb.table("chat_messages").insert([
                {"session_id": req.session_id, "role": "user", "content": req.message, "model": model_used},
                {"session_id": req.session_id, "role": "assistant", "content": answer,
                 "model": model_used, "latency_ms": elapsed},
            ]).execute()
        except Exception:
            pass

    return ChatResp(
        answer=answer,
        sources=[{"title": c.get("title",""), "doc_type": c.get("doc_type",""),
                  "similarity": c.get("similarity",0)} for c in contexts[:5]],
        model=model_used,
        latency_ms=round(elapsed, 1),
    )


@app.post("/chat/stream")
async def chat_stream(req: ChatReq):
    """SSE 스트리밍 채팅. 토큰 단위로 실시간 전송."""
    from fastapi.responses import StreamingResponse
    import json as _json

    if not _st["ready"]:
        raise HTTPException(503, "시스템 초기화 중")

    t0 = time.time()
    _st["queries"] += 1
    contexts = _retrieve(req.message, req.top_k)

    # 소스 정보를 먼저 전송
    sources_data = [
        {"title": c.get("title", ""), "doc_type": c.get("doc_type", ""),
         "similarity": c.get("similarity", 0)} for c in contexts[:5]
    ]

    async def _generate():
        # 소스 이벤트
        yield f"data: {_json.dumps({'type': 'sources', 'sources': sources_data})}\n\n"

        # LLM 스트리밍 생성
        ctx_parts = []
        for i, c in enumerate(contexts[:8], 1):
            doc_type = c.get("doc_type", "")
            title = c.get("title", "")
            content = c.get("content", "")
            meta = c.get("metadata") or {}
            header = f"### 문서 {i} [{doc_type}] {title}"
            if doc_type == "web_search" and meta.get("url"):
                header += f"\n출처: {meta['url']}"
            ctx_parts.append(f"{header}\n{content}")
        ctx = "\n\n".join(ctx_parts)
        user_content = f"## 관련 데이터\n{ctx}\n\n## 질문\n{req.message}"
        messages = [
            {"role": "system", "content": SYSTEM_PREFIX},
            {"role": "user", "content": user_content},
        ]

        model_used = "fallback-web"
        full_answer = ""

        # Gemini 스트리밍
        if GOOGLE_API_KEY:
            try:
                from openai import OpenAI
                client = OpenAI(api_key=GOOGLE_API_KEY,
                                base_url="https://generativelanguage.googleapis.com/v1beta/openai/")
                stream = client.chat.completions.create(
                    model="gemini-2.0-flash", messages=messages,
                    max_tokens=1024, temperature=0.3, stream=True,
                )
                model_used = "gemini-2.0-flash"
                for chunk in stream:
                    delta = chunk.choices[0].delta.content if chunk.choices[0].delta else None
                    if delta:
                        full_answer += delta
                        yield f"data: {_json.dumps({'type': 'token', 'token': delta})}\n\n"
            except Exception as e:
                log.warning(f"Gemini 스트리밍 오류 → 일반 생성 fallback: {e}")
                # fallback: 비스트리밍
                answer, model_used = _llm_generate(req.message, contexts)
                full_answer = answer
                yield f"data: {_json.dumps({'type': 'token', 'token': answer})}\n\n"
        else:
            answer, model_used = _llm_generate(req.message, contexts)
            full_answer = answer
            yield f"data: {_json.dumps({'type': 'token', 'token': answer})}\n\n"

        elapsed = (time.time() - t0) * 1000
        yield f"data: {_json.dumps({'type': 'done', 'model': model_used, 'latency_ms': round(elapsed, 1)})}\n\n"

        # 팬 행동 추적 + 이력 저장
        track_fan_event("chat", user_id=req.user_id, session_id=req.session_id,
                        payload={"query": req.message[:200], "model": model_used,
                                 "source_count": len(contexts), "stream": True})
        if req.session_id:
            try:
                sb = get_supabase()
                sb.table("chat_messages").insert([
                    {"session_id": req.session_id, "role": "user",
                     "content": req.message, "model": model_used},
                    {"session_id": req.session_id, "role": "assistant",
                     "content": full_answer, "model": model_used, "latency_ms": elapsed},
                ]).execute()
            except Exception:
                pass

    return StreamingResponse(_generate(), media_type="text/event-stream",
                             headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})


@app.get("/matches")
async def list_matches(limit: int = Query(20, le=100), season: str | None = None):
    sb = get_supabase()
    q = sb.table("matches").select("id,source_id,match_date,home_score,away_score,stadium,source")\
          .order("match_date", desc=True).limit(limit)
    if season:
        q = q.eq("meta->>season", season)
    return q.execute().data or []


@app.get("/teams")
async def list_teams(limit: int = Query(50, le=200)):
    sb = get_supabase()
    return sb.table("teams").select("id,name,canonical,country,stadium").order("canonical").limit(limit).execute().data or []


@app.get("/teams/{team_id}")
async def get_team(team_id: str):
    sb = get_supabase()
    team = sb.table("teams").select("*").eq("id", team_id).single().execute().data
    if not team:
        raise HTTPException(404, "팀을 찾을 수 없습니다")
    stats = sb.table("team_season_stats").select("*").eq("team_id", team_id).execute().data or []
    track_fan_event("page_view", entity_type="team", entity_id=team_id,
                    payload={"entity_name": team.get("canonical", "")})
    return {"team": team, "stats": stats}


@app.get("/players/{player_id}")
async def get_player(player_id: str):
    sb = get_supabase()
    player = sb.table("players").select("*").eq("id", player_id).single().execute().data
    if not player:
        raise HTTPException(404, "선수를 찾을 수 없습니다")
    stats = sb.table("player_season_stats").select("*").eq("player_id", player_id).execute().data or []
    track_fan_event("page_view", entity_type="player", entity_id=player_id,
                    payload={"entity_name": player.get("name", "")})
    return {"player": player, "stats": stats}


@app.get("/search")
async def search(q: str = Query(..., min_length=1), doc_type: str | None = None, top_k: int = Query(5, ge=1, le=50)):
    if not _st["ready"]:
        raise HTTPException(503, "시스템 초기화 중")
    t0 = time.time()
    results = _retrieve(q, top_k, doc_type)
    elapsed = (time.time() - t0) * 1000
    track_fan_event("search", payload={"query": q[:200], "results": len(results)})
    return {"results": results, "query_time_ms": round(elapsed, 1)}


@app.post("/predictions")
async def create_prediction(req: PredictionReq):
    sb = get_supabase()
    try:
        resp = sb.table("fan_predictions").insert({
            "user_id": req.user_id, "match_id": req.match_id,
            "predicted_home": req.predicted_home, "predicted_away": req.predicted_away,
            "confidence": req.confidence,
        }).execute()
    except Exception as e:
        raise HTTPException(422, f"예측 저장 실패: {e}")
    track_fan_event("prediction", user_id=req.user_id,
                    entity_type="match", entity_id=req.match_id,
                    payload={"home": req.predicted_home, "away": req.predicted_away})
    return resp.data[0] if resp.data else {"status": "ok"}


# ── B2B endpoints ────────────────────────────────
@app.get("/b2b/trends")
async def b2b_trends(
    days: int = Query(7, le=90),
    metric: str = Query("entity_buzz"),
    client=Depends(_verify_b2b_key),
):
    sb = get_supabase()
    resp = sb.table("trend_snapshots").select("*").eq("metric_type", metric)\
             .order("snapshot_date", desc=True).limit(days * 20).execute()
    _log_b2b(client["id"], "/b2b/trends", 200)
    return resp.data or []


@app.get("/b2b/fan-segments")
async def b2b_fan_segments(client=Depends(_verify_b2b_key)):
    sb = get_supabase()
    resp = sb.table("fan_segments").select("*").order("user_count", desc=True).execute()
    _log_b2b(client["id"], "/b2b/fan-segments", 200)
    return resp.data or []


@app.get("/b2b/entity-buzz")
async def b2b_entity_buzz(
    entity_type: str = Query("team"),
    top: int = Query(10, le=50),
    client=Depends(_verify_b2b_key),
):
    sb = get_supabase()
    resp = sb.table("trend_snapshots").select("*")\
             .eq("metric_type", "entity_buzz").eq("entity_type", entity_type)\
             .order("value", desc=True).limit(top).execute()
    _log_b2b(client["id"], "/b2b/entity-buzz", 200)
    return resp.data or []


def _log_b2b(client_id: str, endpoint: str, status: int):
    try:
        sb = get_supabase()
        sb.table("b2b_api_logs").insert({
            "client_id": client_id, "endpoint": endpoint,
            "method": "GET", "status_code": status,
        }).execute()
    except Exception:
        pass


# ── Startup ──────────────────────────────────────
@app.on_event("startup")
async def startup():
    log.info("FastAPI 초기화 중...")
    _st["t0"] = time.time()
    try:
        from sentence_transformers import SentenceTransformer
        _st["model"] = SentenceTransformer(EMBED_MODEL)
        log.info(f"임베딩 모델 로드: {EMBED_MODEL}")
        _st["ready"] = True
        log.info("La Paz API 준비 완료!")
        publish_status("agent_5", "running", "API 서버 가동 :8000")
    except Exception as e:
        log.error(f"초기화 실패: {e}")
        publish_status("agent_5", "error", str(e))


# ── Main ─────────────────────────────────────────
def main():
    log.info("=" * 60)
    log.info("La Paz Agent 5 — API Server 시작")
    log.info("=" * 60)
    publish_status("agent_5", "waiting", "Agent 4 대기")
    if not wait_for_agent("agent_4", "completed", timeout=1800):
        log.warning("Agent 4 타임아웃 — 문서 없이 시작")

    import uvicorn
    uvicorn.run("agent_5_api:app", host="0.0.0.0", port=8000, log_level="info")


if __name__ == "__main__":
    main()
