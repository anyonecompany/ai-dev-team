"""RAG 파이프라인: classify -> retrieve -> generate 통합."""

import asyncio
import hashlib
import logging
import time
from collections import OrderedDict
from typing import AsyncIterator, Callable, Optional

# error_log_fn 콜백 타입: async (request_id, question, error_type, pipeline_stage, error_message, latency_ms) -> None
ErrorLogFn = Optional[Callable[..., "asyncio.coroutines"]]

from .classifier import classify
from .generator import generate, generate_stream, _strip_markdown, _trim_to_last_sentence
from .logging_utils import PipelineLogger, generate_request_id
from .retriever import embed_query, retrieve
from .structured_context import build_structured_context


def _assess_context_quality(documents: list[dict]) -> str:
    """검색 결과의 품질을 평가한다.

    문서 수와 유사도 점수를 기반으로 컨텍스트 충분성을 판단한다.
    pgvector similarity는 0~1 범위 (코사인 유사도).

    Args:
        documents: 검색된 문서 리스트.

    Returns:
        "none" | "low" | "sufficient"
    """
    if not documents:
        return "none"

    # similarity 필드는 벡터 검색 결과에만 존재 (키워드 전용은 없음)
    similarities = [
        d.get("similarity", 0) or 0
        for d in documents
    ]
    top_sim = max(similarities)

    # 임계값 근거:
    # - pgvector 코사인 유사도 0~1 범위
    # - 0.3 미만: 질문과 문서 간 의미적 연관성이 매우 낮음
    # - 문서 2개 이하: RRF 병합 후에도 관련 자료가 부족
    # - 키워드 전용 결과 (top_sim=0): similarity 없으므로 문서 수로만 판단
    if top_sim > 0 and top_sim < 0.3:
        return "low"
    if len(documents) <= 2 and top_sim == 0:
        # 키워드 전용 결과이면서 문서도 적음
        return "low"
    if len(documents) <= 1:
        return "low"

    return "sufficient"

logger = logging.getLogger(__name__)

# perf: total pipeline timeout — return fallback if exceeded
_PIPELINE_TIMEOUT = 45.0
_TIMEOUT_FALLBACK_ANSWER = (
    "답변 생성에 시간이 걸리고 있습니다. 잠시 후 다시 시도해주세요."
)

# -- 응답 캐시 (LRU, 최대 100개) --

_RESPONSE_CACHE_MAX = 100
_RESPONSE_CACHE_TTL = 60  # 1분 후 만료 (라이브 경기 대응)
_response_cache: OrderedDict[str, dict] = OrderedDict()

OUT_OF_SCOPE_ANSWER = (
    "축구 관련 질문이 아닌 것 같아요! "
    "맨유, 아스톤 빌라 경기나 프리미어리그에 대해 물어봐 주세요 ⚽"
)

OUT_OF_SCOPE_CHECK_ANSWER = (
    "혹시 축구 관련 질문이셨나요? "
    "축구 질문이 맞다면 다시 한번 시도해 주세요."
)

_DATA_UNAVAILABLE_ANSWER = (
    "현재 데이터를 불러올 수 없습니다. 잠시 후 다시 질문해주세요."
)

# 분류 실패 시 기본값
_DEFAULT_CLASSIFICATION: dict = {
    "category": "general_football",
    "keywords": [],
    "confidence": 0.0,
    "complexity": "simple",
}


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
    degradation 흐름을 절대 막지 않기 위함.
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


def _extract_last_question(history: list[dict] | None) -> str:
    """history에서 마지막 사용자 질문을 추출한다. 없으면 빈 문자열."""
    if not history:
        return ""
    for msg in reversed(history):
        if msg.get("role") == "user":
            return msg.get("content", "").strip().lower()
    return ""


def _cache_key(question: str, match_context: str, history: list[dict] | None = None) -> str:
    """질문+컨텍스트+대화맥락의 캐시 키 생성."""
    last_q = _extract_last_question(history)
    raw = f"{question.strip().lower()}|{match_context.strip()}|{last_q}"
    return hashlib.md5(raw.encode()).hexdigest()


def _get_cached_response(question: str, match_context: str, history: list[dict] | None = None) -> dict | None:
    """응답 캐시 조회. TTL 만료된 항목은 삭제한다."""
    key = _cache_key(question, match_context, history)
    if key in _response_cache:
        entry = _response_cache[key]
        # TTL 체크
        if time.monotonic() - entry.get("_cached_at", 0) > _RESPONSE_CACHE_TTL:
            del _response_cache[key]
            return None
        _response_cache.move_to_end(key)
        return entry
    return None


def _put_cached_response(question: str, match_context: str, result: dict, history: list[dict] | None = None) -> None:
    """응답을 캐시에 저장 (TTL 타임스탬프 포함)."""
    key = _cache_key(question, match_context, history)
    result["_cached_at"] = time.monotonic()
    _response_cache[key] = result
    _response_cache.move_to_end(key)
    if len(_response_cache) > _RESPONSE_CACHE_MAX:
        _response_cache.popitem(last=False)


async def _ask_inner(question: str, match_context: str, start: float, plog: PipelineLogger, error_log_fn: ErrorLogFn = None, *, force_football: bool = False, history: list[dict] | None = None) -> dict:
    """파이프라인 코어 로직 (타임아웃 래핑 전).

    각 단계를 독립 격리하여 실패 시 graceful degradation으로
    부분 응답을 제공한다.

    Args:
        question: 사용자 질문 텍스트.
        match_context: 현재 경기 컨텍스트.
        start: 파이프라인 시작 시각 (monotonic).
        plog: 구조화 로거.
        force_football: True이면 분류를 건너뛰고 general_football로 실행.

    Returns:
        RAG 파이프라인 결과 딕셔너리.
    """
    degradation_path: list[str] = []
    is_degraded = False

    # 0.5. force_football: 분류 건너뛰고 general_football로 강제 실행
    if force_football:
        plog.info("force_football 활성화, 분류 건너뜀", pipeline_stage="classify",
                  event="force_football")
        classify_start = plog.stage_start("classify")
        classification = {
            "category": "general_football",
            "keywords": [],
            "confidence": 0.0,
        }
        # 임베딩만 실행
        query_embedding = None
        try:
            query_embedding = await embed_query(question, plog=plog)
        except Exception as e:
            is_degraded = True
            degradation_path.append("embedding_failed→keyword_only")
            plog.warning(
                f"임베딩 실패 (force_football), 키워드 검색만 사용: {e}",
                pipeline_stage="embed", event="degradation",
                error_type=type(e).__name__,
            )
        plog.stage_done("classify", classify_start,
                        category=classification["category"],
                        confidence=classification["confidence"])
    else:
        # 1. 질문 분류 + 임베딩 생성을 병렬 실행 (각각 독립 격리)
        classify_start = plog.stage_start("classify")

        classification = _DEFAULT_CLASSIFICATION
        query_embedding = None

        try:
            classify_result, embed_result = await asyncio.gather(
                classify(question, plog=plog),
                embed_query(question, plog=plog),
                return_exceptions=True,
            )

            # 분류 결과 처리
            if isinstance(classify_result, Exception):
                classification = {**_DEFAULT_CLASSIFICATION}
                is_degraded = True
                degradation_path.append("classification_failed→default_category")
                classify_latency = int((time.monotonic() - classify_start) * 1000)
                plog.warning(
                    f"분류 실패, 기본 카테고리로 진행: {classify_result}",
                    pipeline_stage="classify", event="degradation",
                    error_type=type(classify_result).__name__,
                    degradation_path="→".join(degradation_path),
                )
                await _safe_log_error(
                    error_log_fn,
                    request_id=plog.request_id,
                    question=question,
                    error_type="classification",
                    pipeline_stage="classify",
                    error_message=str(classify_result),
                    latency_ms=classify_latency,
                )
            else:
                classification = classify_result

            # 임베딩 결과 처리
            if isinstance(embed_result, Exception):
                query_embedding = None
                is_degraded = True
                degradation_path.append("embedding_failed→keyword_only")
                embed_latency = int((time.monotonic() - classify_start) * 1000)
                plog.warning(
                    f"임베딩 실패, 키워드 검색만 사용: {embed_result}",
                    pipeline_stage="embed", event="degradation",
                    error_type=type(embed_result).__name__,
                    degradation_path="→".join(degradation_path),
                )
                await _safe_log_error(
                    error_log_fn,
                    request_id=plog.request_id,
                    question=question,
                    error_type="embedding",
                    pipeline_stage="embed",
                    error_message=str(embed_result),
                    latency_ms=embed_latency,
                )
            else:
                query_embedding = embed_result
        except Exception as e:
            # asyncio.gather 자체가 실패하는 극단적 케이스
            classification = {**_DEFAULT_CLASSIFICATION}
            query_embedding = None
            is_degraded = True
            degradation_path.append("classify_embed_failed→defaults")
            gather_latency = int((time.monotonic() - classify_start) * 1000)
            plog.warning(
                f"분류+임베딩 단계 전체 실패: {e}",
                pipeline_stage="classify", event="degradation",
                error_type=type(e).__name__,
                degradation_path="→".join(degradation_path),
            )
            await _safe_log_error(
                error_log_fn,
                request_id=plog.request_id,
                question=question,
                error_type="classification",
                pipeline_stage="classify",
                error_message=str(e),
                latency_ms=gather_latency,
            )

        plog.stage_done("classify", classify_start,
                        category=classification["category"],
                        confidence=classification["confidence"])

    # 분류 결과에서 complexity 추출 (없으면 기본값 simple)
    complexity = classification.get("complexity", "simple")

    # 1.5. Out-of-scope → 확인 응답 반환 (분류가 성공한 경우에만)
    if classification["category"] == "out_of_scope":
        total_ms = int((time.monotonic() - start) * 1000)
        plog.info("out_of_scope → out_of_scope_check 확인 응답", pipeline_stage="pipeline",
                  event="out_of_scope_check", latency_ms=total_ms)
        # 오탐 분석용 DB 기록
        await _safe_log_error(
            error_log_fn,
            request_id=plog.request_id,
            question=question,
            error_type="false_negative_candidate",
            pipeline_stage="classification",
            error_message=f"out_of_scope (confidence={classification['confidence']:.2f})",
            latency_ms=total_ms,
        )
        return {
            "question": question,
            "category": "out_of_scope_check",
            "keywords": classification.get("keywords", []),
            "confidence": classification["confidence"],
            "complexity": complexity,
            "answer": OUT_OF_SCOPE_CHECK_ANSWER,
            "source_docs": [],
            "generation_time_ms": 0,
            "total_time_ms": total_ms,
        }

    # 2. 하이브리드 검색 + 구조화 데이터 병렬 로드 (각각 독립 격리)
    retrieve_start = plog.stage_start("retrieve")

    documents: list[dict] = []
    structured_data: str = ""

    try:
        retrieve_result, structured_result = await asyncio.gather(
            retrieve(
                question=question,
                category=classification["category"],
                keywords=classification.get("keywords", [question]),
                top_k=3,
                query_embedding=query_embedding,
                plog=plog,
            ),
            build_structured_context(
                match_context, plog=plog,
                error_log_fn=error_log_fn,
                request_id=plog.request_id,
                question=question,
            ),
            return_exceptions=True,
        )

        # 검색 결과 처리
        if isinstance(retrieve_result, Exception):
            documents = []
            is_degraded = True
            degradation_path.append("retrieve_failed→empty_docs")
            retrieve_latency = int((time.monotonic() - retrieve_start) * 1000)
            plog.warning(
                f"검색 실패, 구조화 데이터만으로 진행: {retrieve_result}",
                pipeline_stage="retrieve", event="degradation",
                error_type=type(retrieve_result).__name__,
                degradation_path="→".join(degradation_path),
            )
            await _safe_log_error(
                error_log_fn,
                request_id=plog.request_id,
                question=question,
                error_type="retrieval",
                pipeline_stage="retrieve",
                error_message=str(retrieve_result),
                latency_ms=retrieve_latency,
            )
        else:
            documents = retrieve_result

        # 구조화 데이터 처리
        if isinstance(structured_result, Exception):
            structured_data = ""
            is_degraded = True
            degradation_path.append("structured_data_failed→empty_context")
            struct_latency = int((time.monotonic() - retrieve_start) * 1000)
            plog.warning(
                f"구조화 데이터 실패, 검색 결과만으로 진행: {structured_result}",
                pipeline_stage="structured_context", event="degradation",
                error_type=type(structured_result).__name__,
                degradation_path="→".join(degradation_path),
            )
            await _safe_log_error(
                error_log_fn,
                request_id=plog.request_id,
                question=question,
                error_type="structured_context",
                pipeline_stage="structured_context",
                error_message=str(structured_result),
                latency_ms=struct_latency,
            )
        else:
            structured_data = structured_result
    except Exception as e:
        # asyncio.gather 자체가 실패하는 극단적 케이스
        documents = []
        structured_data = ""
        is_degraded = True
        degradation_path.append("retrieve_structured_failed→all_empty")
        gather2_latency = int((time.monotonic() - retrieve_start) * 1000)
        plog.warning(
            f"검색+구조화 단계 전체 실패: {e}",
            pipeline_stage="retrieve", event="degradation",
            error_type=type(e).__name__,
            degradation_path="→".join(degradation_path),
        )
        await _safe_log_error(
            error_log_fn,
            request_id=plog.request_id,
            question=question,
            error_type="retrieval",
            pipeline_stage="retrieve",
            error_message=str(e),
            latency_ms=gather2_latency,
        )

    plog.stage_done("retrieve", retrieve_start, doc_count=len(documents))

    # 2.5. 검색 결과와 구조화 데이터 모두 없으면 안내 메시지 반환
    if not documents and not structured_data:
        total_ms = int((time.monotonic() - start) * 1000)
        degradation_path.append("no_data→fallback_answer")
        plog.warning(
            "검색 결과 및 구조화 데이터 모두 없음, 안내 메시지 반환",
            pipeline_stage="pipeline", event="degradation",
            degradation_path="→".join(degradation_path),
            is_degraded=True, latency_ms=total_ms,
        )
        return {
            "question": question,
            "category": classification["category"],
            "keywords": classification.get("keywords", []),
            "confidence": classification["confidence"],
            "complexity": complexity,
            "answer": _DATA_UNAVAILABLE_ANSWER,
            "source_docs": [],
            "generation_time_ms": 0,
            "total_time_ms": total_ms,
            "is_degraded": True,
            "degradation_path": "→".join(degradation_path),
        }

    # 2.7. 검색 결과 품질 평가
    context_quality = _assess_context_quality(documents)
    if context_quality != "sufficient":
        top_sim = max((d.get("similarity", 0) or 0 for d in documents), default=0)
        plog.info(
            f"컨텍스트 품질 평가: {context_quality}",
            pipeline_stage="retrieve", event="context_quality",
            context_quality=context_quality,
            doc_count=len(documents),
            top_similarity=round(top_sim, 4) if top_sim else None,
        )

    # 3. 답변 생성 (실패 시 그대로 raise — A1-1에서 보조 모델 전환 구현 예정)
    gen_start = plog.stage_start("generate")
    generation = await generate(
        question=question,
        documents=documents,
        match_context=match_context,
        structured_data=structured_data,
        complexity=complexity,
        plog=plog,
        history=history,
        context_quality=context_quality,
    )
    plog.stage_done("generate", gen_start)

    total_ms = int((time.monotonic() - start) * 1000)

    # degradation 상태 로깅
    if is_degraded:
        plog.info(
            f"degraded 응답 생성 완료",
            pipeline_stage="pipeline", event="degraded_response",
            is_degraded=True,
            degradation_path="→".join(degradation_path),
            latency_ms=total_ms,
        )

    result = {
        "question": question,
        "category": classification["category"],
        "keywords": classification.get("keywords", []),
        "confidence": classification["confidence"],
        "complexity": complexity,
        "answer": generation["answer"],
        "source_docs": generation["source_docs"],
        "generation_time_ms": generation["generation_time_ms"],
        "total_time_ms": total_ms,
    }

    # 내부 로그용 메타데이터 (외부 응답에는 포함하지 않지만 로그에 기록됨)
    if is_degraded:
        result["is_degraded"] = True
        result["degradation_path"] = "→".join(degradation_path)

    return result


async def ask(question: str, match_context: str = "", *, request_id: str = "", error_log_fn: ErrorLogFn = None, force_football: bool = False, history: list[dict] | None = None) -> dict:
    """전체 RAG 파이프라인을 실행한다.

    Args:
        question: 사용자 질문 텍스트.
        match_context: 현재 경기 컨텍스트 (선택).
        request_id: 요청 추적 ID (선택, 없으면 자동 생성).
        force_football: True이면 분류를 건너뛰고 general_football로 실행.

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
    if not request_id:
        request_id = generate_request_id()
    plog = PipelineLogger(request_id, "rag.pipeline")

    start = time.monotonic()
    plog.info("파이프라인 시작", pipeline_stage="pipeline", event="start",
              question=question[:80], force_football=force_football)

    # 0. 응답 캐시 확인 (force_football 시 캐시 건너뜀 — 재분류이므로)
    if not force_football:
        cached = _get_cached_response(question, match_context, history)
        if cached is not None:
            result = {k: v for k, v in cached.items() if not k.startswith("_")}
            result["total_time_ms"] = int((time.monotonic() - start) * 1000)
            plog.info("응답 캐시 히트", pipeline_stage="pipeline", event="cache_hit",
                      latency_ms=result["total_time_ms"], cached=True)
            return result

    # perf: total pipeline timeout — return fallback answer if exceeded
    try:
        result = await asyncio.wait_for(
            _ask_inner(question, match_context, start, plog, error_log_fn=error_log_fn, force_football=force_football, history=history or []),
            timeout=_PIPELINE_TIMEOUT,
        )
    except asyncio.TimeoutError:
        total_ms = int((time.monotonic() - start) * 1000)
        plog.warning(
            f"파이프라인 타임아웃 ({_PIPELINE_TIMEOUT}s)",
            pipeline_stage="pipeline", event="timeout",
            latency_ms=total_ms, error_type="timeout",
        )
        await _safe_log_error(
            error_log_fn,
            request_id=plog.request_id,
            question=question,
            error_type="timeout",
            pipeline_stage="pipeline",
            error_message=f"파이프라인 타임아웃 ({_PIPELINE_TIMEOUT}s 초과)",
            latency_ms=total_ms,
        )
        result = {
            "question": question,
            "category": "timeout",
            "keywords": [],
            "confidence": 0.0,
            "answer": _TIMEOUT_FALLBACK_ANSWER,
            "source_docs": [],
            "generation_time_ms": 0,
            "total_time_ms": total_ms,
        }
        return result

    # 캐시 저장
    _put_cached_response(question, match_context, result, history)

    total_ms = int((time.monotonic() - start) * 1000)
    plog.info("파이프라인 완료", pipeline_stage="pipeline", event="done",
              latency_ms=total_ms, category=result.get("category", ""))
    return result


async def ask_stream(question: str, match_context: str = "", *, request_id: str = "", error_log_fn: ErrorLogFn = None, force_football: bool = False, history: list[dict] | None = None) -> AsyncIterator[str]:
    """스트리밍 RAG 파이프라인. SSE 청크를 yield한다.

    캐시 히트 시 전체 답변을 한 번에 yield.
    """
    import json

    if not request_id:
        request_id = generate_request_id()
    plog = PipelineLogger(request_id, "rag.pipeline")

    start = time.monotonic()
    plog.info("스트리밍 파이프라인 시작", pipeline_stage="pipeline", event="stream_start",
              question=question[:80], force_football=force_football)

    # 0. 응답 캐시 확인 (force_football 시 캐시 건너뜀 — 재분류이므로)
    if not force_football:
        cached = _get_cached_response(question, match_context, history)
        if cached is not None:
            plog.info("응답 캐시 히트 (스트리밍)", pipeline_stage="pipeline", event="cache_hit",
                      cached=True)
            yield json.dumps({
                "type": "metadata",
                "category": cached["category"],
                "confidence": cached["confidence"],
                "complexity": cached.get("complexity", "simple"),
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

    # 1. 분류 + 임베딩 병렬 (각각 독립 격리)
    degradation_path: list[str] = []
    is_degraded = False

    classify_start = plog.stage_start("classify")

    classification = {**_DEFAULT_CLASSIFICATION}
    query_embedding = None

    # force_football: 분류 건너뛰고 general_football로 강제 실행
    if force_football:
        plog.info("force_football 활성화, 분류 건너뜀 (스트리밍)", pipeline_stage="classify",
                  event="force_football")
        classification = {
            "category": "general_football",
            "keywords": [],
            "confidence": 0.0,
        }
        try:
            query_embedding = await embed_query(question, plog=plog)
        except Exception as e:
            is_degraded = True
            degradation_path.append("embedding_failed→keyword_only")
            plog.warning(
                f"임베딩 실패 (force_football, 스트리밍), 키워드 검색만 사용: {e}",
                pipeline_stage="embed", event="degradation",
                error_type=type(e).__name__,
            )
    else:
        try:
            classify_result, embed_result = await asyncio.gather(
                classify(question, plog=plog),
                embed_query(question, plog=plog),
                return_exceptions=True,
            )

            if isinstance(classify_result, Exception):
                classification = {**_DEFAULT_CLASSIFICATION}
                is_degraded = True
                degradation_path.append("classification_failed→default_category")
                s_classify_latency = int((time.monotonic() - classify_start) * 1000)
                plog.warning(
                    f"분류 실패, 기본 카테고리로 진행: {classify_result}",
                    pipeline_stage="classify", event="degradation",
                    error_type=type(classify_result).__name__,
                    degradation_path="→".join(degradation_path),
                )
                await _safe_log_error(
                    error_log_fn,
                    request_id=plog.request_id,
                    question=question,
                    error_type="classification",
                    pipeline_stage="classify",
                    error_message=str(classify_result),
                    latency_ms=s_classify_latency,
                )
            else:
                classification = classify_result

            if isinstance(embed_result, Exception):
                query_embedding = None
                is_degraded = True
                degradation_path.append("embedding_failed→keyword_only")
                s_embed_latency = int((time.monotonic() - classify_start) * 1000)
                plog.warning(
                    f"임베딩 실패, 키워드 검색만 사용: {embed_result}",
                    pipeline_stage="embed", event="degradation",
                    error_type=type(embed_result).__name__,
                    degradation_path="→".join(degradation_path),
                )
                await _safe_log_error(
                    error_log_fn,
                    request_id=plog.request_id,
                    question=question,
                    error_type="embedding",
                    pipeline_stage="embed",
                    error_message=str(embed_result),
                    latency_ms=s_embed_latency,
                )
            else:
                query_embedding = embed_result
        except Exception as e:
            classification = {**_DEFAULT_CLASSIFICATION}
            query_embedding = None
            is_degraded = True
            degradation_path.append("classify_embed_failed→defaults")
            s_gather_latency = int((time.monotonic() - classify_start) * 1000)
            plog.warning(
                f"분류+임베딩 단계 전체 실패: {e}",
                pipeline_stage="classify", event="degradation",
                error_type=type(e).__name__,
                degradation_path="→".join(degradation_path),
            )
            await _safe_log_error(
                error_log_fn,
                request_id=plog.request_id,
                question=question,
                error_type="classification",
                pipeline_stage="classify",
                error_message=str(e),
                latency_ms=s_gather_latency,
            )

    plog.stage_done("classify", classify_start,
                    category=classification["category"],
                    confidence=classification["confidence"])

    # 분류 결과에서 complexity 추출 (없으면 기본값 simple)
    complexity = classification.get("complexity", "simple")

    # 메타데이터 먼저 전송
    yield json.dumps({
        "type": "metadata",
        "category": classification["category"],
        "confidence": classification["confidence"],
        "complexity": complexity,
        "cached": False,
    }, ensure_ascii=False)

    # 1.5. Out-of-scope → 확인 응답 반환 (분류가 성공한 경우에만)
    if classification["category"] == "out_of_scope":
        oos_total_ms = int((time.monotonic() - start) * 1000)
        plog.info("out_of_scope → out_of_scope_check 확인 응답 (스트리밍)", pipeline_stage="pipeline",
                  event="out_of_scope_check", latency_ms=oos_total_ms)
        # 오탐 분석용 DB 기록
        await _safe_log_error(
            error_log_fn,
            request_id=plog.request_id,
            question=question,
            error_type="false_negative_candidate",
            pipeline_stage="classification",
            error_message=f"out_of_scope (confidence={classification['confidence']:.2f})",
            latency_ms=oos_total_ms,
        )
        # metadata를 out_of_scope_check로 재전송 (위에서 out_of_scope로 보냈으므로)
        yield json.dumps({
            "type": "metadata",
            "category": "out_of_scope_check",
            "confidence": classification["confidence"],
            "complexity": complexity,
            "cached": False,
        }, ensure_ascii=False)
        yield json.dumps({
            "type": "answer",
            "text": OUT_OF_SCOPE_CHECK_ANSWER,
        }, ensure_ascii=False)
        yield json.dumps({
            "type": "done",
            "source_count": 0,
            "total_time_ms": oos_total_ms,
        }, ensure_ascii=False)
        return

    # 2. 검색 + 구조화 데이터 병렬 로드 (각각 독립 격리)
    retrieve_start = plog.stage_start("retrieve")

    documents: list[dict] = []
    structured_data: str = ""

    try:
        retrieve_result, structured_result = await asyncio.gather(
            retrieve(
                question=question,
                category=classification["category"],
                keywords=classification.get("keywords", [question]),
                top_k=3,
                query_embedding=query_embedding,
                plog=plog,
            ),
            build_structured_context(
                match_context, plog=plog,
                error_log_fn=error_log_fn,
                request_id=plog.request_id,
                question=question,
            ),
            return_exceptions=True,
        )

        if isinstance(retrieve_result, Exception):
            documents = []
            is_degraded = True
            degradation_path.append("retrieve_failed→empty_docs")
            s_retrieve_latency = int((time.monotonic() - retrieve_start) * 1000)
            plog.warning(
                f"검색 실패, 구조화 데이터만으로 진행: {retrieve_result}",
                pipeline_stage="retrieve", event="degradation",
                error_type=type(retrieve_result).__name__,
                degradation_path="→".join(degradation_path),
            )
            await _safe_log_error(
                error_log_fn,
                request_id=plog.request_id,
                question=question,
                error_type="retrieval",
                pipeline_stage="retrieve",
                error_message=str(retrieve_result),
                latency_ms=s_retrieve_latency,
            )
        else:
            documents = retrieve_result

        if isinstance(structured_result, Exception):
            structured_data = ""
            is_degraded = True
            degradation_path.append("structured_data_failed→empty_context")
            s_struct_latency = int((time.monotonic() - retrieve_start) * 1000)
            plog.warning(
                f"구조화 데이터 실패, 검색 결과만으로 진행: {structured_result}",
                pipeline_stage="structured_context", event="degradation",
                error_type=type(structured_result).__name__,
                degradation_path="→".join(degradation_path),
            )
            await _safe_log_error(
                error_log_fn,
                request_id=plog.request_id,
                question=question,
                error_type="structured_context",
                pipeline_stage="structured_context",
                error_message=str(structured_result),
                latency_ms=s_struct_latency,
            )
        else:
            structured_data = structured_result
    except Exception as e:
        documents = []
        structured_data = ""
        is_degraded = True
        degradation_path.append("retrieve_structured_failed→all_empty")
        s_gather2_latency = int((time.monotonic() - retrieve_start) * 1000)
        plog.warning(
            f"검색+구조화 단계 전체 실패: {e}",
            pipeline_stage="retrieve", event="degradation",
            error_type=type(e).__name__,
            degradation_path="→".join(degradation_path),
        )
        await _safe_log_error(
            error_log_fn,
            request_id=plog.request_id,
            question=question,
            error_type="retrieval",
            pipeline_stage="retrieve",
            error_message=str(e),
            latency_ms=s_gather2_latency,
        )

    plog.stage_done("retrieve", retrieve_start, doc_count=len(documents))

    # 2.5. 검색 결과와 구조화 데이터 모두 없으면 안내 메시지 반환
    if not documents and not structured_data:
        degradation_path.append("no_data→fallback_answer")
        total_ms = int((time.monotonic() - start) * 1000)
        plog.warning(
            "검색 결과 및 구조화 데이터 모두 없음, 안내 메시지 반환 (스트리밍)",
            pipeline_stage="pipeline", event="degradation",
            degradation_path="→".join(degradation_path),
            is_degraded=True, latency_ms=total_ms,
        )
        yield json.dumps({
            "type": "answer",
            "text": _DATA_UNAVAILABLE_ANSWER,
        }, ensure_ascii=False)
        yield json.dumps({
            "type": "done",
            "source_count": 0,
            "total_time_ms": total_ms,
        }, ensure_ascii=False)
        return

    # 2.7. 검색 결과 품질 평가 (스트리밍)
    context_quality = _assess_context_quality(documents)
    if context_quality != "sufficient":
        top_sim = max((d.get("similarity", 0) or 0 for d in documents), default=0)
        plog.info(
            f"컨텍스트 품질 평가 (스트리밍): {context_quality}",
            pipeline_stage="retrieve", event="context_quality",
            context_quality=context_quality,
            doc_count=len(documents),
            top_similarity=round(top_sim, 4) if top_sim else None,
        )

    # 3. 스트리밍 생성 (실패 시 그대로 raise — A1-1에서 보조 모델 전환 구현 예정)
    full_answer = ""
    gen_start_time = time.monotonic()
    plog.stage_start("generate_stream")
    async for chunk in generate_stream(
        question=question,
        documents=documents,
        match_context=match_context,
        structured_data=structured_data,
        complexity=complexity,
        plog=plog,
        history=history or [],
        context_quality=context_quality,
    ):
        full_answer += chunk
        yield json.dumps({
            "type": "chunk",
            "text": chunk,
        }, ensure_ascii=False)

    gen_ms = int((time.monotonic() - gen_start_time) * 1000)
    total_ms = int((time.monotonic() - start) * 1000)
    plog.stage_done("generate_stream", gen_start_time)

    source_ids = [doc.get("id") for doc in documents if doc.get("id")]

    # 스트리밍 완료 후 마크다운 제거된 최종 답변
    cleaned_answer = _trim_to_last_sentence(_strip_markdown(full_answer))

    # degradation 상태 로깅
    if is_degraded:
        plog.info(
            "degraded 스트리밍 응답 생성 완료",
            pipeline_stage="pipeline", event="degraded_response",
            is_degraded=True,
            degradation_path="→".join(degradation_path),
            latency_ms=total_ms,
        )

    yield json.dumps({
        "type": "done",
        "source_count": len(source_ids),
        "generation_time_ms": gen_ms,
        "total_time_ms": total_ms,
        "cleaned_answer": cleaned_answer,
    }, ensure_ascii=False)

    plog.info("스트리밍 파이프라인 완료", pipeline_stage="pipeline", event="stream_done",
              latency_ms=total_ms, source_count=len(source_ids))

    # 캐시 저장 (마크다운 제거된 버전)
    _put_cached_response(question, match_context, {
        "question": question,
        "category": classification["category"],
        "keywords": classification.get("keywords", []),
        "confidence": classification["confidence"],
        "complexity": complexity,
        "answer": cleaned_answer,
        "source_docs": source_ids,
        "generation_time_ms": gen_ms,
        "total_time_ms": total_ms,
    }, history)
