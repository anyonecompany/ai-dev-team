"""RAG 파이프라인 래퍼 서비스."""

import json
import logging
from typing import AsyncIterator

import config  # noqa: F401 — sys.path 설정 트리거

from rag.pipeline import ask, ask_stream
from services.error_log_service import log_error as _error_log_fn

logger = logging.getLogger(__name__)


async def generate_answer(
    question: str,
    match_context: dict | None = None,
    *,
    request_id: str = "",
    force_football: bool = False,
    history: list[dict] | None = None,
) -> dict:
    """RAG 파이프라인을 호출하여 답변을 생성한다."""
    # match_context를 문자열로 변환 (pipeline.ask가 str을 받음)
    ctx_str = ""
    if match_context:
        ctx_str = json.dumps(match_context, ensure_ascii=False)

    result = await ask(question, match_context=ctx_str, request_id=request_id, error_log_fn=_error_log_fn, force_football=force_football, history=history or [])

    return {
        "question": result["question"],
        "answer": result["answer"],
        "category": result["category"],
        "confidence": result["confidence"],
        "source_count": len(result.get("source_docs", [])),
        "generation_time_ms": result.get("generation_time_ms", 0),
        "total_time_ms": result.get("total_time_ms", result.get("generation_time_ms", 0)),
    }


async def generate_answer_stream(
    question: str,
    match_context: str = "",
    *,
    request_id: str = "",
    force_football: bool = False,
    history: list[dict] | None = None,
) -> AsyncIterator[str]:
    """스트리밍 RAG 파이프라인. JSON 청크를 yield한다."""
    async for chunk_json in ask_stream(question, match_context=match_context, request_id=request_id, error_log_fn=_error_log_fn, force_football=force_football, history=history or []):
        yield chunk_json
