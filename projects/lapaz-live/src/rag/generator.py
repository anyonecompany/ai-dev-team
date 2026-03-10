"""답변 생성기: Claude Sonnet으로 한국어 3~4문장 답변 생성 (스트리밍 지원)."""

import logging
import os
import re
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import AsyncIterator

import anthropic
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), "..", "..", ".env"))

logger = logging.getLogger(__name__)

PROMPTS_DIR = Path(__file__).parent / "prompts"
SYSTEM_PROMPT = (PROMPTS_DIR / "system_prompt.txt").read_text(encoding="utf-8")

MODEL = "claude-sonnet-4-5-20250929"

_anthropic_client = None


def _get_client() -> anthropic.AsyncAnthropic:
    """Anthropic 클라이언트 싱글톤."""
    global _anthropic_client
    if _anthropic_client is None:
        _anthropic_client = anthropic.AsyncAnthropic()
    return _anthropic_client


def _strip_markdown(text: str) -> str:
    """응답에서 마크다운 서식을 제거한다."""
    text = re.sub(r'```[\s\S]*?```', '', text)  # ```code blocks``` (먼저 처리)
    text = re.sub(r'\*\*(.+?)\*\*', r'\1', text)  # **bold**
    text = re.sub(r'\*(.+?)\*', r'\1', text)  # *italic*
    text = re.sub(r'#{1,6}\s*', '', text)  # ## headings
    text = re.sub(r'`([^`]+)`', r'\1', text)  # `code`
    text = re.sub(r'^- ', '', text, flags=re.MULTILINE)  # - list items
    text = text.replace('*', '')  # 잔여 별표 모두 제거
    return text.strip()


def _format_documents(docs: list[dict]) -> str:
    """검색된 문서들을 텍스트로 포맷."""
    if not docs:
        return "(관련 문서 없음)"

    parts = []
    for i, doc in enumerate(docs, 1):
        content = doc.get("content", "")
        collection = doc.get("collection", "unknown")
        parts.append(f"[문서 {i} | {collection}]\n{content}")
    return "\n\n".join(parts)


async def generate(
    question: str,
    documents: list[dict],
    match_context: str = "",
    structured_data: str = "",
) -> dict:
    """검색된 문서를 기반으로 답변을 생성한다.

    Args:
        question: 사용자 질문.
        documents: 검색된 문서 리스트.
        match_context: 현재 경기 컨텍스트 (선택).
        structured_data: FotMob 구조화 데이터 (선택).

    Returns:
        {"answer": str, "source_docs": list[int], "generation_time_ms": int}
    """
    start = time.monotonic()
    client = _get_client()

    formatted_docs = _format_documents(documents)
    kst = timezone(timedelta(hours=9))
    now_str = datetime.now(kst).strftime("%Y년 %m월 %d일 %H:%M KST")
    system = SYSTEM_PROMPT.replace(
        "{current_datetime}", now_str
    ).replace(
        "{match_context}", match_context or "(경기 컨텍스트 없음)"
    ).replace(
        "{structured_data}", structured_data or "(구조화 데이터 없음)"
    ).replace("{retrieved_documents}", formatted_docs)

    response = await client.messages.create(
        model=MODEL,
        max_tokens=512,
        system=system,
        messages=[{"role": "user", "content": question}],
    )

    answer = _strip_markdown(response.content[0].text)
    elapsed_ms = int((time.monotonic() - start) * 1000)

    source_ids = [doc.get("id") for doc in documents if doc.get("id")]

    return {
        "answer": answer,
        "source_docs": source_ids,
        "generation_time_ms": elapsed_ms,
    }


async def generate_stream(
    question: str,
    documents: list[dict],
    match_context: str = "",
    structured_data: str = "",
) -> AsyncIterator[str]:
    """스트리밍으로 답변을 생성한다. 텍스트 청크를 yield.

    Args:
        question: 사용자 질문.
        documents: 검색된 문서 리스트.
        match_context: 현재 경기 컨텍스트 (선택).
        structured_data: FotMob 구조화 데이터 (선택).

    Yields:
        텍스트 청크 문자열.
    """
    client = _get_client()

    formatted_docs = _format_documents(documents)
    kst = timezone(timedelta(hours=9))
    now_str = datetime.now(kst).strftime("%Y년 %m월 %d일 %H:%M KST")
    system = SYSTEM_PROMPT.replace(
        "{current_datetime}", now_str
    ).replace(
        "{match_context}", match_context or "(경기 컨텍스트 없음)"
    ).replace(
        "{structured_data}", structured_data or "(구조화 데이터 없음)"
    ).replace("{retrieved_documents}", formatted_docs)

    async with client.messages.stream(
        model=MODEL,
        max_tokens=512,
        system=system,
        messages=[{"role": "user", "content": question}],
    ) as stream:
        async for text in stream.text_stream:
            yield text
