"""하이브리드 검색기: pgvector 유사도 + 키워드 ILIKE + RRF 병합."""

import asyncio
import hashlib
import logging
import os
from collections import OrderedDict

import voyageai
from dotenv import load_dotenv
from supabase import create_client

load_dotenv(os.path.join(os.path.dirname(__file__), "..", "..", ".env"))

logger = logging.getLogger(__name__)

CATEGORY_COLLECTIONS: dict[str, list[str]] = {
    "player_info": ["player_profiles", "match_context"],
    "tactical_intent": ["match_context", "tactical_preview", "manager_analysis"],
    "match_flow": ["match_context", "match_preview", "h2h_analysis"],
    "player_form": ["player_profiles", "match_context", "form_analysis"],
    "fan_simulation": ["player_profiles", "match_context", "fan_tactical_guide"],
    "season_narrative": ["match_context", "season_context"],
    "rules_judgment": ["match_context", "rules_explainer"],
}

RRF_K = 60
DEFAULT_MATCH_COUNT = 7

# ── 최신 시즌 우선순위 (과거 데이터 오염 방지) ──
# 2025-26 시즌 관련 카테고리는 boost, 과거 시즌은 penalty
FRESH_CATEGORIES = {"season_mun", "season_avl", "season", "manager_mun", "manager_avl"}
STALE_SEASON_PATTERNS = [
    "2015-16", "2016-17", "2017-18", "2018-19", "2019-20",
    "2020-21", "2021-22", "2022-23", "2023-24", "2024-25",
]

# ── 싱글톤 클라이언트 ──

_supabase_client = None
_voyage_client = None

# ── 임베딩 캐시 (LRU, 최대 200개) ──

_EMBED_CACHE_MAX = 200
_embed_cache: OrderedDict[str, list[float]] = OrderedDict()


def _cache_key(text: str) -> str:
    """텍스트의 캐시 키 생성."""
    return hashlib.md5(text.strip().lower().encode()).hexdigest()


def _get_cached_embedding(question: str) -> list[float] | None:
    """캐시에서 임베딩 조회."""
    key = _cache_key(question)
    if key in _embed_cache:
        _embed_cache.move_to_end(key)
        logger.debug("임베딩 캐시 히트: %s", question[:30])
        return _embed_cache[key]
    return None


def _put_cached_embedding(question: str, embedding: list[float]) -> None:
    """임베딩을 캐시에 저장."""
    key = _cache_key(question)
    _embed_cache[key] = embedding
    _embed_cache.move_to_end(key)
    if len(_embed_cache) > _EMBED_CACHE_MAX:
        _embed_cache.popitem(last=False)


def _get_supabase():
    """Supabase 클라이언트 싱글톤."""
    global _supabase_client
    if _supabase_client is None:
        _supabase_client = create_client(
            os.environ["SUPABASE_URL"], os.environ["SUPABASE_SERVICE_KEY"]
        )
    return _supabase_client


def _get_voyage():
    """Voyage 클라이언트 싱글톤."""
    global _voyage_client
    if _voyage_client is None:
        _voyage_client = voyageai.Client(api_key=os.environ["VOYAGE_API_KEY"])
    return _voyage_client


async def _vector_search(
    supabase, query_embedding: list[float], collection: str, match_count: int
) -> list[dict]:
    """pgvector 유사도 검색 (match_documents RPC)."""
    result = supabase.rpc(
        "match_documents",
        {
            "query_embedding": query_embedding,
            "match_count": match_count,
            "filter_collection": collection,
        },
    ).execute()
    return result.data or []


def _keyword_search(
    supabase, keywords: list[str], collection: str, limit: int
) -> list[dict]:
    """키워드 ILIKE 검색. 과거 시즌 문서 필터링."""
    if not keywords:
        return []

    query = supabase.table("documents").select("id, collection, content, metadata")
    query = query.eq("collection", collection)

    # OR 조건으로 키워드 검색
    or_conditions = [f"content.ilike.%{kw}%" for kw in keywords[:5]]
    query = query.or_(",".join(or_conditions))
    # 더 많이 가져온 후 과거 시즌 필터링
    query = query.limit(limit * 3)

    result = query.execute()
    docs = result.data or []

    # 최신 시즌 우선, 과거 시즌 후순위 (참고자료로 보존)
    current = []  # 2025-26 시즌 + 비시즌 문서
    recent = []   # 2024-25 직전 시즌
    older = []    # 그 이전 과거 시즌
    for doc in docs:
        meta = doc.get("metadata") or {}
        title = meta.get("page_title", "")
        if any(p in title for p in STALE_SEASON_PATTERNS):
            older.append(doc)
        elif "2024-25" in title:
            recent.append(doc)
        else:
            current.append(doc)

    # 최신 → 직전 → 과거 순으로 채움
    combined = current + recent + older
    return combined[:limit]


def _recency_score(doc: dict) -> float:
    """문서의 최신성 점수. 최신 시즌 boost, 과거 시즌은 후순위(참고자료로 보존)."""
    metadata = doc.get("metadata") or {}
    page_title = metadata.get("page_title", "")
    category = metadata.get("category", "")
    content = doc.get("content", "")

    # 2025-26 시즌 문서 → 강한 boost
    if "2025-26" in page_title or "2025-26" in content[:200]:
        return 0.3
    if category in FRESH_CATEGORIES:
        return 0.15

    # 2024-25 직전 시즌 → 약한 penalty (참고 가치 있음)
    if "2024-25" in page_title:
        return -0.1

    # 그 이전 과거 시즌 → 후순위 (삭제 아닌 뒤로 밀기)
    for pattern in STALE_SEASON_PATTERNS:
        if pattern in page_title:
            return -0.25

    # 전술/감독 분석 전문 컬렉션 → boost
    collection = doc.get("collection", "")
    if collection in ("tactical_preview", "manager_analysis", "match_preview",
                       "h2h_analysis", "season_context"):
        return 0.2

    return 0.0


def _rrf_merge(
    vector_results: list[dict], keyword_results: list[dict], k: int = RRF_K
) -> list[dict]:
    """Reciprocal Rank Fusion + 최신성 가중치로 두 결과 리스트 병합."""
    scores: dict[int, float] = {}
    doc_map: dict[int, dict] = {}

    for rank, doc in enumerate(vector_results):
        doc_id = doc["id"]
        scores[doc_id] = scores.get(doc_id, 0) + 1.0 / (k + rank + 1)
        doc_map[doc_id] = doc

    for rank, doc in enumerate(keyword_results):
        doc_id = doc["id"]
        scores[doc_id] = scores.get(doc_id, 0) + 1.0 / (k + rank + 1)
        doc_map[doc_id] = doc

    # 최신성 가중치 적용
    for doc_id in scores:
        scores[doc_id] += _recency_score(doc_map[doc_id])

    sorted_ids = sorted(scores, key=lambda x: scores[x], reverse=True)
    return [doc_map[doc_id] for doc_id in sorted_ids]


async def _run_all_keyword_searches(
    supabase, keywords: list[str], collections: list[str], match_count: int
) -> list[dict]:
    """모든 컬렉션에 대해 키워드 검색을 이벤트 루프에서 병렬 실행."""
    loop = asyncio.get_event_loop()
    tasks = [
        loop.run_in_executor(
            None, _keyword_search, supabase, keywords, col, match_count
        )
        for col in collections
    ]
    results = await asyncio.gather(*tasks)
    all_docs: list[dict] = []
    for docs in results:
        all_docs.extend(docs)
    return all_docs


async def _run_all_vector_searches(
    supabase, query_embedding: list[float], collections: list[str], match_count: int
) -> list[dict]:
    """모든 컬렉션에 대해 벡터 검색을 병렬 실행."""
    tasks = [
        _vector_search(supabase, query_embedding, col, match_count)
        for col in collections
    ]
    results = await asyncio.gather(*tasks)
    all_docs: list[dict] = []
    for docs in results:
        all_docs.extend(docs)
    return all_docs


def _embed_query_sync(question: str) -> list[float] | None:
    """Voyage 임베딩 생성 (동기, run_in_executor용). 캐시 우선 조회."""
    cached = _get_cached_embedding(question)
    if cached is not None:
        return cached

    voyage_key = os.environ.get("VOYAGE_API_KEY")
    if not voyage_key:
        logger.warning("VOYAGE_API_KEY 미설정 — 키워드 검색만 사용")
        return None
    vo = _get_voyage()
    result = vo.embed([question[:8000]], model="voyage-3", input_type="query")
    embedding = result.embeddings[0]
    _put_cached_embedding(question, embedding)
    return embedding


async def embed_query(question: str) -> list[float] | None:
    """Voyage 임베딩을 비동기로 생성한다 (pipeline에서 병렬 호출용).

    Args:
        question: 임베딩할 질문 텍스트.

    Returns:
        임베딩 벡터 또는 None (API 키 미설정 시).
    """
    loop = asyncio.get_event_loop()
    try:
        return await loop.run_in_executor(None, _embed_query_sync, question)
    except Exception as e:
        logger.warning("임베딩 생성 실패: %s", e)
        return None


async def retrieve(
    question: str,
    category: str,
    keywords: list[str],
    top_k: int = 5,
    query_embedding: list[float] | None = None,
) -> list[dict]:
    """하이브리드 검색으로 관련 문서를 가져온다.

    벡터 검색 실패 시 (API 키 누락, 할당량 초과, 임베딩 NULL 등)
    키워드 검색만으로 폴백한다.

    Args:
        question: 원본 질문.
        category: 분류된 카테고리.
        keywords: 추출된 키워드 리스트.
        top_k: 최종 반환 문서 수.
        query_embedding: 사전 생성된 임베딩 (None이면 내부에서 생성).

    Returns:
        관련 문서 리스트 [{"id", "collection", "content", "metadata", ...}]
    """
    collections = CATEGORY_COLLECTIONS.get(category, ["match_context"])
    supabase = _get_supabase()

    # 임베딩이 없으면 내부에서 생성 + 키워드 검색 병렬 실행
    if query_embedding is None:
        embed_task = embed_query(question)
        keyword_task = _run_all_keyword_searches(
            supabase, keywords, collections, DEFAULT_MATCH_COUNT
        )
        query_embedding, all_keyword = await asyncio.gather(embed_task, keyword_task)
    else:
        # 임베딩이 이미 있으면 키워드 검색만 실행
        all_keyword = await _run_all_keyword_searches(
            supabase, keywords, collections, DEFAULT_MATCH_COUNT
        )

    # 벡터 검색 (임베딩 성공 시)
    all_vector: list[dict] = []
    if query_embedding is not None:
        try:
            all_vector = await _run_all_vector_searches(
                supabase, query_embedding, collections, DEFAULT_MATCH_COUNT
            )
        except Exception as e:
            logger.warning("벡터 검색 실패, 키워드 폴백: %s", e)

    if all_vector:
        merged = _rrf_merge(all_vector, all_keyword)
    else:
        # 벡터 검색 실패 시 키워드 결과만 중복 제거하여 반환
        seen: set[int] = set()
        merged = []
        for doc in all_keyword:
            if doc["id"] not in seen:
                seen.add(doc["id"])
                merged.append(doc)

    return merged[:top_k]
