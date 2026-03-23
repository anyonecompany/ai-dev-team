"""답변 생성기: Gemini Flash로 한국어 3~4문장 답변 생성."""

import logging
import os
import time
from pathlib import Path

from google import genai
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), "..", "..", ".env"))

logger = logging.getLogger(__name__)

PROMPTS_DIR = Path(__file__).parent / "prompts"
SYSTEM_PROMPT = (PROMPTS_DIR / "system_prompt.txt").read_text(encoding="utf-8")

MODEL = "gemini-2.5-flash"


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
) -> dict:
    """검색된 문서를 기반으로 답변을 생성한다.

    Args:
        question: 사용자 질문.
        documents: 검색된 문서 리스트.
        match_context: 현재 경기 컨텍스트 (선택).

    Returns:
        {"answer": str, "source_docs": list[int], "generation_time_ms": int}
    """
    start = time.monotonic()
    client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

    formatted_docs = _format_documents(documents)
    system = SYSTEM_PROMPT.replace(
        "{match_context}", match_context or "(경기 컨텍스트 없음)"
    ).replace("{retrieved_documents}", formatted_docs)

    prompt = f"{system}\n\n사용자 질문: {question}"

    response = await client.aio.models.generate_content(
        model=MODEL,
        contents=prompt,
    )

    answer = response.text.strip()
    elapsed_ms = int((time.monotonic() - start) * 1000)

    source_ids = [doc.get("id") for doc in documents if doc.get("id")]

    return {
        "answer": answer,
        "source_docs": source_ids,
        "generation_time_ms": elapsed_ms,
    }
