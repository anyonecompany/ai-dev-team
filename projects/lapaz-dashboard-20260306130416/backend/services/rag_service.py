"""RAG 파이프라인 래퍼 서비스."""

import json
import logging

import config  # noqa: F401 — sys.path 설정 트리거

from rag.pipeline import ask

logger = logging.getLogger(__name__)


async def generate_answer(
    question: str,
    match_context: dict | None = None,
) -> dict:
    """RAG 파이프라인을 호출하여 답변을 생성한다."""
    # match_context를 문자열로 변환 (pipeline.ask가 str을 받음)
    ctx_str = ""
    if match_context:
        ctx_str = json.dumps(match_context, ensure_ascii=False)

    result = await ask(question, match_context=ctx_str)

    return {
        "question": result["question"],
        "answer": result["answer"],
        "category": result["category"],
        "confidence": result["confidence"],
        "source_count": len(result.get("source_docs", [])),
        "generation_time_ms": result.get("generation_time_ms", 0),
    }
