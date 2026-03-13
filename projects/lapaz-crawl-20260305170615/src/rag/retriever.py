"""하이브리드 검색기: pgvector 유사도 + 키워드 ILIKE + RRF 병합."""

import logging
import os

import voyageai
from dotenv import load_dotenv
from supabase import create_client

load_dotenv(os.path.join(os.path.dirname(__file__), "..", "..", ".env"))

logger = logging.getLogger(__name__)

CATEGORY_COLLECTIONS: dict[str, list[str]] = {
    "player_info": ["player_profiles"],
    "tactical_intent": ["match_context"],
    "match_flow": ["match_context"],
    "player_form": ["player_profiles", "match_context"],
    "fan_simulation": ["player_profiles", "match_context"],
    "season_narrative": ["match_context"],
    "rules_judgment": ["match_context"],
}

RRF_K = 60
DEFAULT_MATCH_COUNT = 10


def _get_supabase():
    return create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_SERVICE_KEY"])


def _get_voyage():
    return voyageai.Client(api_key=os.environ["VOYAGE_API_KEY"])


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
    """키워드 ILIKE 검색."""
    if not keywords:
        return []

    query = supabase.table("documents").select("id, collection, content, metadata")
    query = query.eq("collection", collection)

    # OR 조건으로 키워드 검색
    or_conditions = [f"content.ilike.%{kw}%" for kw in keywords[:5]]
    query = query.or_(",".join(or_conditions))
    query = query.limit(limit)

    result = query.execute()
    return result.data or []


def _rrf_merge(
    vector_results: list[dict], keyword_results: list[dict], k: int = RRF_K
) -> list[dict]:
    """Reciprocal Rank Fusion으로 두 결과 리스트 병합."""
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

    sorted_ids = sorted(scores, key=lambda x: scores[x], reverse=True)
    return [doc_map[doc_id] for doc_id in sorted_ids]


async def retrieve(
    question: str,
    category: str,
    keywords: list[str],
    top_k: int = 5,
) -> list[dict]:
    """하이브리드 검색으로 관련 문서를 가져온다.

    벡터 검색 실패 시 (API 키 누락, 할당량 초과, 임베딩 NULL 등)
    키워드 검색만으로 폴백한다.

    Args:
        question: 원본 질문.
        category: 분류된 카테고리.
        keywords: 추출된 키워드 리스트.
        top_k: 최종 반환 문서 수.

    Returns:
        관련 문서 리스트 [{"id", "collection", "content", "metadata", ...}]
    """
    collections = CATEGORY_COLLECTIONS.get(category, ["match_context"])
    supabase = _get_supabase()

    # 벡터 검색 시도 (실패 시 키워드만 사용)
    all_vector: list[dict] = []
    try:
        voyage_key = os.environ.get("VOYAGE_API_KEY")
        if voyage_key:
            vo = _get_voyage()
            result = vo.embed([question[:8000]], model="voyage-3", input_type="query")
            query_embedding = result.embeddings[0]

            for collection in collections:
                vector_docs = await _vector_search(
                    supabase, query_embedding, collection, DEFAULT_MATCH_COUNT
                )
                all_vector.extend(vector_docs)
        else:
            logger.warning("VOYAGE_API_KEY 미설정 — 키워드 검색만 사용")
    except Exception as e:
        logger.warning("벡터 검색 실패, 키워드 폴백: %s", e)

    all_keyword: list[dict] = []
    for collection in collections:
        keyword_docs = _keyword_search(
            supabase, keywords, collection, DEFAULT_MATCH_COUNT
        )
        all_keyword.extend(keyword_docs)

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
