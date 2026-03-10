"""RAG 파이프라인: classify → retrieve → generate 통합."""

import asyncio
import hashlib
import logging
import time
from collections import OrderedDict
from typing import AsyncIterator

from .classifier import classify
from .generator import generate, generate_stream, _strip_markdown
from .retriever import embed_query, retrieve
from .structured_context import build_structured_context

logger = logging.getLogger(__name__)

# ── 응답 캐시 (LRU, 최대 100개) ──

_RESPONSE_CACHE_MAX = 100
_RESPONSE_CACHE_TTL = 300  # 5분 후 만료
_response_cache: OrderedDict[str, dict] = OrderedDict()

OUT_OF_SCOPE_ANSWER = (
    "축구 관련 질문이 아닌 것 같아요! "
    "맨유, 아스톤 빌라 경기나 프리미어리그에 대해 물어봐 주세요 ⚽"
)


def _cache_key(question: str, match_context: str) -> str:
    """질문+컨텍스트의 캐시 키 생성."""
    raw = f"{question.strip().lower()}|{match_context.strip()}"
    return hashlib.md5(raw.encode()).hexdigest()


def _get_cached_response(question: str, match_context: str) -> dict | None:
    """응답 캐시 조회. TTL 만료된 항목은 삭제한다."""
    key = _cache_key(question, match_context)
    if key in _response_cache:
        entry = _response_cache[key]
        # TTL 체크
        if time.monotonic() - entry.get("_cached_at", 0) > _RESPONSE_CACHE_TTL:
            del _response_cache[key]
            logger.info("응답 캐시 만료: %s", question[:30])
            return None
        _response_cache.move_to_end(key)
        logger.info("응답 캐시 히트: %s", question[:30])
        return entry
    return None


def _put_cached_response(question: str, match_context: str, result: dict) -> None:
    """응답을 캐시에 저장 (TTL 타임스탬프 포함)."""
    key = _cache_key(question, match_context)
    result["_cached_at"] = time.monotonic()
    _response_cache[key] = result
    _response_cache.move_to_end(key)
    if len(_response_cache) > _RESPONSE_CACHE_MAX:
        _response_cache.popitem(last=False)


async def ask(question: str, match_context: str = "") -> dict:
    """전체 RAG 파이프라인을 실행한다.

    Args:
        question: 사용자 질문 텍스트.
        match_context: 현재 경기 컨텍스트 (선택).

    Returns:
        {
            "question": str,
            "category": str,
            "keywords": list[str],
            "confidence": float,
            "answer": str,
            "source_docs": list[int],
            "generation_time_ms": int,
            "total_time_ms": int,
        }
    """
    start = time.monotonic()

    # 0. 응답 캐시 확인
    cached = _get_cached_response(question, match_context)
    if cached is not None:
        result = {k: v for k, v in cached.items() if not k.startswith("_")}
        result["total_time_ms"] = int((time.monotonic() - start) * 1000)
        return result

    # 1. 질문 분류 + 임베딩 생성을 병렬 실행
    classification, query_embedding = await asyncio.gather(
        classify(question),
        embed_query(question),
    )
    logger.info(
        "분류 결과: %s (confidence=%.2f)",
        classification["category"],
        classification["confidence"],
    )

    # 1.5. Out-of-scope 조기 차단
    if classification["category"] == "out_of_scope":
        total_ms = int((time.monotonic() - start) * 1000)
        result = {
            "question": question,
            "category": "out_of_scope",
            "keywords": classification.get("keywords", []),
            "confidence": classification["confidence"],
            "answer": OUT_OF_SCOPE_ANSWER,
            "source_docs": [],
            "generation_time_ms": 0,
            "total_time_ms": total_ms,
        }
        return result

    # 2. 하이브리드 검색 + 구조화 데이터 병렬 로드
    retrieve_task = retrieve(
        question=question,
        category=classification["category"],
        keywords=classification["keywords"],
        query_embedding=query_embedding,
    )
    structured_task = build_structured_context(match_context)
    documents, structured_data = await asyncio.gather(
        retrieve_task, structured_task
    )
    logger.info("검색 결과: %d건, 구조화 데이터: %d자", len(documents), len(structured_data))

    # 3. 답변 생성
    generation = await generate(
        question=question,
        documents=documents,
        match_context=match_context,
        structured_data=structured_data,
    )

    total_ms = int((time.monotonic() - start) * 1000)

    result = {
        "question": question,
        "category": classification["category"],
        "keywords": classification["keywords"],
        "confidence": classification["confidence"],
        "answer": generation["answer"],
        "source_docs": generation["source_docs"],
        "generation_time_ms": generation["generation_time_ms"],
        "total_time_ms": total_ms,
    }

    # 캐시 저장
    _put_cached_response(question, match_context, result)

    return result


async def ask_stream(question: str, match_context: str = "") -> AsyncIterator[str]:
    """스트리밍 RAG 파이프라인. SSE 청크를 yield한다.

    캐시 히트 시 전체 답변을 한 번에 yield.
    """
    import json

    start = time.monotonic()

    # 0. 응답 캐시 확인
    cached = _get_cached_response(question, match_context)
    if cached is not None:
        yield json.dumps({
            "type": "metadata",
            "category": cached["category"],
            "confidence": cached["confidence"],
            "cached": True,
        }, ensure_ascii=False)
        yield json.dumps({
            "type": "answer",
            "text": cached["answer"],
        }, ensure_ascii=False)
        yield json.dumps({
            "type": "done",
            "source_count": len(cached.get("source_docs", [])),
            "total_time_ms": int((time.monotonic() - start) * 1000),
        }, ensure_ascii=False)
        return

    # 1. 분류 + 임베딩 병렬
    classification, query_embedding = await asyncio.gather(
        classify(question),
        embed_query(question),
    )

    # 메타데이터 먼저 전송
    yield json.dumps({
        "type": "metadata",
        "category": classification["category"],
        "confidence": classification["confidence"],
        "cached": False,
    }, ensure_ascii=False)

    # 1.5. Out-of-scope 조기 차단
    if classification["category"] == "out_of_scope":
        yield json.dumps({
            "type": "answer",
            "text": OUT_OF_SCOPE_ANSWER,
        }, ensure_ascii=False)
        yield json.dumps({
            "type": "done",
            "source_count": 0,
            "total_time_ms": int((time.monotonic() - start) * 1000),
        }, ensure_ascii=False)
        return

    # 2. 검색 + 구조화 데이터 병렬 로드
    retrieve_task = retrieve(
        question=question,
        category=classification["category"],
        keywords=classification["keywords"],
        query_embedding=query_embedding,
    )
    structured_task = build_structured_context(match_context)
    documents, structured_data = await asyncio.gather(
        retrieve_task, structured_task
    )

    # 3. 스트리밍 생성
    full_answer = ""
    gen_start = time.monotonic()
    async for chunk in generate_stream(
        question=question,
        documents=documents,
        match_context=match_context,
        structured_data=structured_data,
    ):
        full_answer += chunk
        yield json.dumps({
            "type": "chunk",
            "text": chunk,
        }, ensure_ascii=False)

    gen_ms = int((time.monotonic() - gen_start) * 1000)
    total_ms = int((time.monotonic() - start) * 1000)

    source_ids = [doc.get("id") for doc in documents if doc.get("id")]

    # 스트리밍 완료 후 마크다운 제거된 최종 답변
    cleaned_answer = _strip_markdown(full_answer)

    yield json.dumps({
        "type": "done",
        "source_count": len(source_ids),
        "generation_time_ms": gen_ms,
        "total_time_ms": total_ms,
        "cleaned_answer": cleaned_answer,
    }, ensure_ascii=False)

    # 캐시 저장 (마크다운 제거된 버전)
    _put_cached_response(question, match_context, {
        "question": question,
        "category": classification["category"],
        "keywords": classification.get("keywords", []),
        "confidence": classification["confidence"],
        "answer": cleaned_answer,
        "source_docs": source_ids,
        "generation_time_ms": gen_ms,
        "total_time_ms": total_ms,
    })
