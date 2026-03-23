"""하이브리드 검색기: pgvector 유사도 + 키워드 ILIKE + RRF 병합."""

from __future__ import annotations

import asyncio
import hashlib
import logging
import os
import time
from collections import OrderedDict
from concurrent.futures import ThreadPoolExecutor
from typing import TYPE_CHECKING

import voyageai
from dotenv import load_dotenv
from supabase import create_client

if TYPE_CHECKING:
    from .logging_utils import PipelineLogger

load_dotenv(os.path.join(os.path.dirname(__file__), "..", "..", ".env"))

logger = logging.getLogger(__name__)

# perf: reduced collections per category (max 2-3) to cut search fan-out
CATEGORY_COLLECTIONS: dict[str, list[str]] = {
    "player_info": ["player_profiles", "match_context"],
    "tactical_intent": ["tactical_preview", "manager_analysis"],
    "match_flow": ["match_context", "match_preview"],
    "player_form": ["player_profiles", "match_context"],
    "fan_simulation": ["player_profiles", "fan_tactical_guide"],
    "season_narrative": ["match_context", "season_context"],
    "rules_judgment": ["match_context", "rules_explainer"],
}

RRF_K = 60
# perf: reduced docs per collection 7->5 to cut DB load
DEFAULT_MATCH_COUNT = 5

# -- 프리뷰/예상 문서 태깅 키워드 --
_PREVIEW_KEYWORDS = (
    "예상", "프리뷰", "전망", "preview", "predicted", "expected", "예측", "가능성",
)


# perf: total timeout for the retrieve step (return whatever is available)
_RETRIEVE_TIMEOUT = 8.0

# -- 최신 시즌 우선순위 (과거 데이터 오염 방지) --
# 2025-26 시즌 관련 카테고리는 boost, 과거 시즌은 penalty
FRESH_CATEGORIES = {"season_mun", "season_avl", "season", "manager_mun", "manager_avl"}
STALE_SEASON_PATTERNS = [
    "2015-16", "2016-17", "2017-18", "2018-19", "2019-20",
    "2020-21", "2021-22", "2022-23", "2023-24", "2024-25",
]

# -- 싱글톤 클라이언트 --

_supabase_client = None
_voyage_client = None

# -- 임베딩 캐시 (LRU, 최대 200개) --

_EMBED_CACHE_MAX = 200
_embed_cache: OrderedDict[str, list[float]] = OrderedDict()

# Voyage AI 임베딩 및 키워드 검색용 스레드 풀 (동기 API 래핑 성능 개선)
_executor = ThreadPoolExecutor(max_workers=10)


def _cache_key(text: str) -> str:
    """텍스트의 캐시 키 생성."""
    return hashlib.md5(text.strip().lower().encode()).hexdigest()


def _get_cached_embedding(question: str) -> list[float] | None:
    """캐시에서 임베딩 조회."""
    key = _cache_key(question)
    if key in _embed_cache:
        _embed_cache.move_to_end(key)
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
    # perf: wrap in asyncio timeout to prevent slow RPC from blocking pipeline
    try:
        result = await asyncio.wait_for(
            asyncio.get_event_loop().run_in_executor(
                _executor,
                lambda: supabase.rpc(
                    "match_documents",
                    {
                        "query_embedding": query_embedding,
                        "match_count": match_count,
                        "filter_collection": collection,
                    },
                ).execute(),
            ),
            timeout=5.0,  # perf: per-collection vector search timeout
        )
        return result.data or []
    except asyncio.TimeoutError:
        logger.warning("벡터 검색 타임아웃: collection=%s", collection)
        return []


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

    # 최신 -> 직전 -> 과거 순으로 채움
    combined = current + recent + older
    return combined[:limit]


def _recency_score(doc: dict) -> float:
    """문서의 최신성 점수. 최신 시즌 boost, 과거 시즌은 후순위(참고자료로 보존)."""
    metadata = doc.get("metadata") or {}
    page_title = metadata.get("page_title", "")
    category = metadata.get("category", "")
    content = doc.get("content", "")

    # 2025-26 시즌 문서 -> 강한 boost
    if "2025-26" in page_title or "2025-26" in content[:200]:
        return 0.3
    if category in FRESH_CATEGORIES:
        return 0.15

    # 2024-25 직전 시즌 -> 약한 penalty (참고 가치 있음)
    if "2024-25" in page_title:
        return -0.1

    # 그 이전 과거 시즌 -> 후순위 (삭제 아닌 뒤로 밀기)
    for pattern in STALE_SEASON_PATTERNS:
        if pattern in page_title:
            return -0.25

    # 전술/감독 분석 전문 컬렉션 -> boost
    collection = doc.get("collection", "")
    if collection in ("tactical_preview", "manager_analysis", "match_preview",
                       "h2h_analysis", "season_context"):
        return 0.2

    return 0.0


def _classify_document_type(doc: dict) -> str:
    """문서가 프리뷰/예상인지 확정 정보인지 분류한다.

    content, metadata의 title/page_title, collection 이름을 검사하여
    프리뷰 키워드가 포함되면 "preview", 아니면 "factual"을 반환한다.

    Args:
        doc: 검색된 문서 딕셔너리.

    Returns:
        "preview" 또는 "factual".
    """
    content = doc.get("content", "").lower()
    metadata = doc.get("metadata") or {}
    title = metadata.get("title", "").lower()
    page_title = metadata.get("page_title", "").lower()
    collection = doc.get("collection", "").lower()

    search_text = f"{content[:500]} {title} {page_title} {collection}"
    for kw in _PREVIEW_KEYWORDS:
        if kw in search_text:
            return "preview"
    return "factual"


def _tag_document_types(docs: list[dict]) -> list[dict]:
    """문서 리스트에 document_type 필드를 추가한다.

    원본 문서를 변경하지 않고 새 딕셔너리를 반환한다 (불변성 원칙).

    Args:
        docs: 검색된 문서 리스트.

    Returns:
        document_type 필드가 추가된 문서 리스트.
    """
    return [{**doc, "document_type": _classify_document_type(doc)} for doc in docs]


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
            _executor, _keyword_search, supabase, keywords, col, match_count
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


async def embed_query(question: str, *, plog: PipelineLogger | None = None) -> list[float] | None:
    """Voyage 임베딩을 비동기로 생성한다 (pipeline에서 병렬 호출용).

    Args:
        question: 임베딩할 질문 텍스트.
        plog: 구조화 로거 (선택).

    Returns:
        임베딩 벡터 또는 None (API 키 미설정 시).
    """
    start = time.monotonic()
    loop = asyncio.get_event_loop()
    try:
        result = await loop.run_in_executor(_executor, _embed_query_sync, question)
        latency = int((time.monotonic() - start) * 1000)
        if plog:
            cached = _get_cached_embedding(question) is not None
            plog.info(
                "임베딩 생성 완료",
                pipeline_stage="embed", event="done",
                provider="voyage", latency_ms=latency,
                cached=cached,
            )
        return result
    except Exception as e:
        latency = int((time.monotonic() - start) * 1000)
        if plog:
            plog.warning(
                f"임베딩 생성 실패: {e}",
                pipeline_stage="embed", event="error",
                provider="voyage", latency_ms=latency,
                error_type=type(e).__name__,
            )
        else:
            logger.warning("임베딩 생성 실패: %s", e)
        return None


async def _retrieve_inner(
    question: str,
    category: str,
    keywords: list[str],
    top_k: int,
    query_embedding: list[float] | None,
    plog: PipelineLogger | None = None,
) -> list[dict]:
    """하이브리드 검색 내부 구현 (타임아웃 래핑 전)."""
    collections = CATEGORY_COLLECTIONS.get(category, ["match_context"])
    supabase = _get_supabase()

    # 임베딩이 없으면 내부에서 생성 + 키워드 검색 병렬 실행
    if query_embedding is None:
        embed_task = embed_query(question, plog=plog)
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
            if plog:
                plog.warning(
                    f"벡터 검색 실패, 키워드 폴백: {e}",
                    pipeline_stage="retrieve", event="vector_search_error",
                    error_type=type(e).__name__,
                )
            else:
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

    final = _tag_document_types(merged[:top_k])

    # 검색 결과 로깅
    if plog:
        search_method = "hybrid" if all_vector else "keyword_only"
        top_sim = None
        if all_vector and all_vector[0].get("similarity") is not None:
            top_sim = round(all_vector[0]["similarity"], 4)
        plog.info(
            f"검색 완료: {len(final)}건 ({search_method})",
            pipeline_stage="retrieve", event="search_done",
            search_method=search_method,
            doc_count=len(final),
            top_similarity=top_sim,
        )

    return final


async def retrieve(
    question: str,
    category: str,
    keywords: list[str],
    top_k: int = 5,
    query_embedding: list[float] | None = None,
    *,
    plog: PipelineLogger | None = None,
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
        plog: 구조화 로거 (선택).

    Returns:
        관련 문서 리스트 [{"id", "collection", "content", "metadata", ...}]
    """
    # perf: total retrieve timeout — return whatever results are available
    try:
        return await asyncio.wait_for(
            _retrieve_inner(question, category, keywords, top_k, query_embedding, plog),
            timeout=_RETRIEVE_TIMEOUT,
        )
    except asyncio.TimeoutError:
        if plog:
            plog.warning(
                f"검색 전체 타임아웃 ({_RETRIEVE_TIMEOUT}s)",
                pipeline_stage="retrieve", event="timeout",
                error_type="timeout",
            )
        else:
            logger.warning("검색 전체 타임아웃 (%.0fs): question=%s", _RETRIEVE_TIMEOUT, question[:50])
        return []
