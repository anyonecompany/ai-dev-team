"""RAG 파이프라인: classify → retrieve → generate 통합."""

import logging
import time

from .classifier import classify
from .generator import generate
from .retriever import retrieve

logger = logging.getLogger(__name__)


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

    # 1. 질문 분류
    classification = await classify(question)
    logger.info(
        "분류 결과: %s (confidence=%.2f)",
        classification["category"],
        classification["confidence"],
    )

    # 2. 하이브리드 검색
    documents = await retrieve(
        question=question,
        category=classification["category"],
        keywords=classification["keywords"],
    )
    logger.info("검색 결과: %d건", len(documents))

    # 3. 답변 생성
    generation = await generate(
        question=question,
        documents=documents,
        match_context=match_context,
    )

    total_ms = int((time.monotonic() - start) * 1000)

    return {
        "question": question,
        "category": classification["category"],
        "keywords": classification["keywords"],
        "confidence": classification["confidence"],
        "answer": generation["answer"],
        "source_docs": generation["source_docs"],
        "generation_time_ms": generation["generation_time_ms"],
        "total_time_ms": total_ms,
    }
