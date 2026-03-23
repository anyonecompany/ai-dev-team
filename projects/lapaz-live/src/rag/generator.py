"""답변 생성기: Gemini Flash로 한국어 3~4문장 답변 생성 (스트리밍 지원)."""

from __future__ import annotations

import asyncio
import logging
import os
import re
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import AsyncIterator, TYPE_CHECKING

from google import genai
from google.genai.errors import ClientError
from dotenv import load_dotenv

if TYPE_CHECKING:
    from .logging_utils import PipelineLogger

from .exceptions import RateLimitError, PipelineTimeoutError, GenerationError

load_dotenv(os.path.join(os.path.dirname(__file__), "..", "..", ".env"))

logger = logging.getLogger(__name__)

PROMPTS_DIR = Path(__file__).parent / "prompts"
SYSTEM_PROMPT = (PROMPTS_DIR / "system_prompt.txt").read_text(encoding="utf-8")

MODEL = "gemini-2.5-flash"
FALLBACK_MODEL = "gemini-2.0-flash-lite"

_gemini_client = None

_SENTENCE_PUNCTUATION = ".!?…"
_TERMINAL_CLOSERS = "\"')]}\u201D\u2019"
_KOREAN_SENTENCE_ENDINGS = (
    # 합쇼체 (formal)
    "했습니다",
    "있습니다",
    "없습니다",
    "됩니다",
    "입니다",
    "합니다",
    "답니다",
    "랍니다",
    "습니까",
    "니다",
    # 해요체 (polite conversational)
    "이에요",
    "거예요",
    "예요",
    "거든요",
    "잖아요",
    "는데요",
    "인데요",
    "건데요",
    "텐데요",
    "을걸요",
    "볼게요",
    "할게요",
    "같아요",
    "싶어요",
    "봐요",
    "줘요",
    "나요",
    "가요",
    "해요",
    "세요",
    "래요",
    "어요",
    "아요",
    "네요",
    "군요",
    "지요",
    "려고요",
    "할까요",
    "될까요",
    "죠",
    # 과거/접속
    "였어요",
    "었어요",
    "였고요",
    "었고요",
    "였죠",
    "었죠",
    # 해라체 (plain)
    "였다",
    "었다",
    "했다",
    "된다",
    "있다",
    "없다",
    "싶다",
    "같다",
    "보인다",
)
_KOREAN_ENDING_PATTERN = re.compile(
    "|".join(sorted((re.escape(ending) for ending in _KOREAN_SENTENCE_ENDINGS), key=len, reverse=True))
)


def _get_client() -> genai.Client:
    """Gemini 클라이언트 싱글톤."""
    global _gemini_client
    if _gemini_client is None:
        api_key = os.getenv("GEMINI_API_KEY")
        _gemini_client = genai.Client(api_key=api_key)
    return _gemini_client



def _trim_to_last_sentence(text: str) -> str:
    """토큰 한계로 잘린 텍스트를 마지막 완전한 문장에서 자른다."""
    if not text:
        return text
    stripped = text.strip()

    # 이미 문장부호나 닫는 따옴표로 마무리되면 그대로 반환
    trimmed_tail = stripped.rstrip(_TERMINAL_CLOSERS)
    if trimmed_tail and trimmed_tail[-1] in _SENTENCE_PUNCTUATION:
        return stripped

    # 1차: 일반 문장부호 기준으로 마지막 완전한 문장까지 자른다.
    last_pos = -1
    for ch in _SENTENCE_PUNCTUATION:
        pos = stripped.rfind(ch)
        if pos > last_pos:
            last_pos = pos
    if last_pos > 0:
        return stripped[: last_pos + 1].rstrip()

    # 2차: 한국어 종결형 뒤에 쉼표/공백이 나오면 그 지점까지를 완결 문장으로 본다.
    last_match = None
    for match in _KOREAN_ENDING_PATTERN.finditer(stripped):
        suffix = stripped[match.end():]
        if not suffix or suffix[0] in f",，;: \n\t{_TERMINAL_CLOSERS}":
            last_match = match

    if last_match and last_match.end() > 0:
        candidate = stripped[: last_match.end()].rstrip(" ,，;:")
        if candidate and candidate[-1] not in _SENTENCE_PUNCTUATION:
            candidate += "."
        return candidate

    # 문장 경계를 찾지 못하면 원본 반환
    return stripped


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


def _detect_match_status(match_context: str) -> str:
    """match_context에서 경기 상태를 추출한다.

    current_minute 키가 포함되어 있으면 'live', 없으면 'pre'.

    Args:
        match_context: 경기 컨텍스트 문자열.

    Returns:
        'live' 또는 'pre'.
    """
    if match_context and "current_minute" in match_context:
        return "live"
    return "pre"


def _build_dynamic_directive(match_status: str, complexity: str) -> str:
    """match_status와 complexity에 따른 동적 답변 가이드를 생성한다.

    Args:
        match_status: 경기 상태 ('live' 또는 'pre').
        complexity: 질문 복잡도 ('simple' 또는 'detailed').

    Returns:
        프롬프트에 삽입할 동적 지시 문자열.
    """
    return (
        f"[현재 상태: {match_status}, 질문 복잡도: {complexity}]\n"
        f"→ {match_status} + {complexity}에 해당하는 답변 길이 가이드를 따라."
    )


def _format_history(history: list[dict], max_turns: int = 3) -> str:
    """이전 대화 히스토리를 프롬프트용 텍스트로 포맷한다.

    Args:
        history: 대화 히스토리 리스트 (각 항목: {"role": "user"|"assistant", "content": str}).
        max_turns: 포함할 최대 턴 수 (1턴 = user + assistant). 초과 시 최근 턴만.

    Returns:
        포맷된 히스토리 문자열. 비어 있으면 빈 문자열.
    """
    if not history:
        return ""

    # 최대 max_turns * 2개 항목 (최근 것만)
    max_items = max_turns * 2
    trimmed = history[-max_items:] if len(history) > max_items else history

    lines: list[str] = []
    for item in trimmed:
        role = item.get("role", "")
        content = item.get("content", "")
        # 200자로 truncate
        if len(content) > 200:
            content = content[:200] + "..."
        if role == "user":
            lines.append(f"사용자: {content}")
        elif role == "assistant":
            lines.append(f"봇: {content}")

    if not lines:
        return ""

    return "[이전 대화]\n" + "\n".join(lines)


def _context_quality_tag(context_quality: str) -> str:
    """컨텍스트 품질에 따른 프롬프트 태그를 반환한다.

    Args:
        context_quality: "none" | "low" | "sufficient"

    Returns:
        삽입할 태그 문자열. "sufficient"이면 빈 문자열.
    """
    if context_quality == "none":
        return (
            "[참고 자료 없음] 관련 자료를 찾지 못했습니다. "
            "구조화 데이터만으로 답변하세요. 추측하지 마세요.\n\n"
        )
    if context_quality == "low":
        return (
            "[참고 자료 부족] 관련 자료가 제한적입니다. "
            "확인된 정보만 답하고 추측하지 마세요.\n\n"
        )
    return ""


def _format_documents(docs: list[dict], max_docs: int = 4) -> str:
    """검색된 문서들을 텍스트로 포맷.

    Args:
        docs: 검색된 문서 리스트.
        max_docs: 프롬프트에 포함할 최대 문서 수.
    """
    if not docs:
        return "(관련 문서 없음)"

    # perf: limit injected docs to reduce prompt size and generation latency
    parts = []
    for i, doc in enumerate(docs[:max_docs], 1):
        content = doc.get("content", "")
        collection = doc.get("collection", "unknown")
        doc_type = doc.get("document_type", "")
        label = "[예상/전망 자료] " if doc_type == "preview" else ""
        parts.append(f"{label}[문서 {i} | {collection}]\n{content}")
    return "\n\n".join(parts)


async def generate(
    question: str,
    documents: list[dict],
    match_context: str = "",
    structured_data: str = "",
    *,
    complexity: str = "simple",
    plog: PipelineLogger | None = None,
    history: list[dict] | None = None,
    context_quality: str = "sufficient",
) -> dict:
    """검색된 문서를 기반으로 답변을 생성한다.

    Args:
        question: 사용자 질문.
        documents: 검색된 문서 리스트.
        match_context: 현재 경기 컨텍스트 (선택).
        structured_data: FotMob 구조화 데이터 (선택).
        complexity: 질문 복잡도 ('simple' 또는 'detailed', 기본='simple').
        plog: 구조화 로거 (선택).
        history: 이전 대화 히스토리 (선택, 기본=[]).
        context_quality: 검색 결과 품질 ('none'|'low'|'sufficient', 기본='sufficient').

    Returns:
        {"answer": str, "source_docs": list[int], "generation_time_ms": int}
    """
    start = time.monotonic()
    client = _get_client()

    quality_tag = _context_quality_tag(context_quality)
    formatted_docs = _format_documents(documents)
    kst = timezone(timedelta(hours=9))
    now_str = datetime.now(kst).strftime("%Y년 %m월 %d일 %H:%M KST")
    system = SYSTEM_PROMPT.replace(
        "{current_datetime}", now_str
    ).replace(
        "{match_context}", match_context or "(경기 컨텍스트 없음)"
    ).replace(
        "{structured_data}", structured_data or "(구조화 데이터 없음)"
    ).replace("{retrieved_documents}", f"{quality_tag}{formatted_docs}")

    match_status = _detect_match_status(match_context)
    directive = _build_dynamic_directive(match_status, complexity)

    history_section = _format_history(history or [])
    if history_section:
        prompt = f"{system}\n\n{history_section}\n\n{directive}\n질문: {question}"
    else:
        prompt = f"{system}\n\n{directive}\n질문: {question}"
    response = None
    primary_exhausted = False
    for attempt in range(3):
        attempt_start = time.monotonic()
        try:
            response = await client.aio.models.generate_content(
                model=MODEL,
                contents=prompt,
                config=genai.types.GenerateContentConfig(
                    temperature=0.3,
                    max_output_tokens=900,
                ),
            )
            attempt_latency = int((time.monotonic() - attempt_start) * 1000)
            if plog:
                plog.info(
                    f"Gemini API 호출 성공 (attempt {attempt + 1})",
                    pipeline_stage="generate", event="api_call_success",
                    provider="gemini", model=MODEL, latency_ms=attempt_latency,
                    attempt=attempt + 1, status_code=200,
                )
            break
        except ClientError as e:
            attempt_latency = int((time.monotonic() - attempt_start) * 1000)
            is_rate_limit = "429" in str(e)
            error_type = "rate_limit" if is_rate_limit else "client_error"

            if plog:
                plog.warning(
                    f"Gemini API 호출 실패: {e}",
                    pipeline_stage="generate", event="api_call_error",
                    provider="gemini", model=MODEL, latency_ms=attempt_latency,
                    attempt=attempt + 1,
                    error_type=error_type,
                    status_code=429 if is_rate_limit else 400,
                )

            if is_rate_limit and attempt < 2:
                wait = (attempt + 1) * 5
                if plog:
                    plog.info(
                        f"Gemini 429 — {wait}초 후 재시도 ({attempt + 1}/3)",
                        pipeline_stage="generate", event="rate_limit_retry",
                        provider="gemini", attempt=attempt + 1,
                    )
                else:
                    logger.warning("Gemini 429 — %d초 후 재시도 (%d/3)", wait, attempt + 1)
                await asyncio.sleep(wait)
            elif is_rate_limit:
                primary_exhausted = True
                break
            else:
                raise GenerationError(f"Gemini API 클라이언트 오류: {e}") from e
        except asyncio.TimeoutError as e:
            attempt_latency = int((time.monotonic() - attempt_start) * 1000)
            if plog:
                plog.warning(
                    f"Gemini API 타임아웃 (attempt {attempt + 1})",
                    pipeline_stage="generate", event="api_call_timeout",
                    provider="gemini", latency_ms=attempt_latency,
                    attempt=attempt + 1, error_type="timeout",
                )
            raise PipelineTimeoutError(f"Gemini API 타임아웃: {e}") from e

    # 주 모델 429 연속 실패 → 보조 모델(Gemini Pro)로 전환
    if primary_exhausted:
        if plog:
            plog.warning(
                f"주 모델({MODEL}) 429 연속 실패, 보조 모델({FALLBACK_MODEL})로 전환",
                pipeline_stage="generate", event="model_fallback",
                model_fallback=True, fallback_model=FALLBACK_MODEL,
                primary_error="rate_limit",
            )
        else:
            logger.warning("주 모델(%s) 429 연속 실패, 보조 모델(%s)로 전환", MODEL, FALLBACK_MODEL)

        fallback_start = time.monotonic()
        try:
            fallback_response = await client.aio.models.generate_content(
                model=FALLBACK_MODEL,
                contents=prompt,
                config=genai.types.GenerateContentConfig(
                    temperature=0.3,
                    max_output_tokens=900,
                ),
            )
            fallback_latency = int((time.monotonic() - fallback_start) * 1000)
            if plog:
                plog.info(
                    f"보조 모델({FALLBACK_MODEL}) 호출 성공",
                    pipeline_stage="generate", event="api_call_success",
                    provider="gemini", model=FALLBACK_MODEL,
                    latency_ms=fallback_latency, fallback_success=True,
                )

            answer_text = fallback_response.text if fallback_response.text else ""
            answer = _trim_to_last_sentence(_strip_markdown(answer_text))
            elapsed_ms = int((time.monotonic() - start) * 1000)
            source_ids = [doc.get("id") for doc in documents if doc.get("id")]
            return {
                "answer": answer,
                "source_docs": source_ids,
                "generation_time_ms": elapsed_ms,
            }
        except Exception as e:
            fallback_latency = int((time.monotonic() - fallback_start) * 1000)
            if plog:
                plog.error(
                    f"보조 모델({FALLBACK_MODEL})도 실패: {e}",
                    pipeline_stage="generate", event="fallback_failed",
                    provider="gemini", model=FALLBACK_MODEL,
                    latency_ms=fallback_latency, fallback_success=False,
                )
            raise RateLimitError(
                f"주 모델({MODEL})과 보조 모델({FALLBACK_MODEL}) 모두 실패: {e}"
            ) from e

    answer = _trim_to_last_sentence(_strip_markdown(response.text))
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
    *,
    complexity: str = "simple",
    plog: PipelineLogger | None = None,
    history: list[dict] | None = None,
    context_quality: str = "sufficient",
) -> AsyncIterator[str]:
    """스트리밍으로 답변을 생성한다. 텍스트 청크를 yield.

    Args:
        question: 사용자 질문.
        documents: 검색된 문서 리스트.
        match_context: 현재 경기 컨텍스트 (선택).
        structured_data: FotMob 구조화 데이터 (선택).
        complexity: 질문 복잡도 ('simple' 또는 'detailed', 기본='simple').
        plog: 구조화 로거 (선택).
        history: 이전 대화 히스토리 (선택, 기본=[]).
        context_quality: 검색 결과 품질 ('none'|'low'|'sufficient', 기본='sufficient').

    Yields:
        텍스트 청크 문자열.
    """
    client = _get_client()

    quality_tag = _context_quality_tag(context_quality)
    formatted_docs = _format_documents(documents)
    kst = timezone(timedelta(hours=9))
    now_str = datetime.now(kst).strftime("%Y년 %m월 %d일 %H:%M KST")
    system = SYSTEM_PROMPT.replace(
        "{current_datetime}", now_str
    ).replace(
        "{match_context}", match_context or "(경기 컨텍스트 없음)"
    ).replace(
        "{structured_data}", structured_data or "(구조화 데이터 없음)"
    ).replace("{retrieved_documents}", f"{quality_tag}{formatted_docs}")

    match_status = _detect_match_status(match_context)
    directive = _build_dynamic_directive(match_status, complexity)

    history_section = _format_history(history or [])
    if history_section:
        prompt = f"{system}\n\n{history_section}\n\n{directive}\n질문: {question}"
    else:
        prompt = f"{system}\n\n{directive}\n질문: {question}"
    stream = None
    primary_exhausted = False
    for attempt in range(3):
        attempt_start = time.monotonic()
        try:
            stream = await client.aio.models.generate_content_stream(
                model=MODEL,
                contents=prompt,
                config=genai.types.GenerateContentConfig(
                    temperature=0.3,
                    max_output_tokens=900,
                ),
            )
            attempt_latency = int((time.monotonic() - attempt_start) * 1000)
            if plog:
                plog.info(
                    f"Gemini 스트리밍 API 연결 성공 (attempt {attempt + 1})",
                    pipeline_stage="generate_stream", event="stream_connected",
                    provider="gemini", model=MODEL, latency_ms=attempt_latency,
                    attempt=attempt + 1, status_code=200,
                )
            break
        except ClientError as e:
            attempt_latency = int((time.monotonic() - attempt_start) * 1000)
            is_rate_limit = "429" in str(e)
            error_type = "rate_limit" if is_rate_limit else "client_error"

            if plog:
                plog.warning(
                    f"Gemini 스트리밍 API 호출 실패: {e}",
                    pipeline_stage="generate_stream", event="api_call_error",
                    provider="gemini", model=MODEL, latency_ms=attempt_latency,
                    attempt=attempt + 1,
                    error_type=error_type,
                    status_code=429 if is_rate_limit else 400,
                )

            if is_rate_limit and attempt < 2:
                wait = (attempt + 1) * 10
                if plog:
                    plog.info(
                        f"Gemini 429 (stream) — {wait}초 후 재시도 ({attempt + 1}/3)",
                        pipeline_stage="generate_stream", event="rate_limit_retry",
                        provider="gemini", attempt=attempt + 1,
                    )
                else:
                    logger.warning("Gemini 429 (stream) — %d초 후 재시도 (%d/3)", wait, attempt + 1)
                await asyncio.sleep(wait)
            elif is_rate_limit:
                primary_exhausted = True
                break
            else:
                raise GenerationError(f"Gemini 스트리밍 API 클라이언트 오류: {e}") from e
        except asyncio.TimeoutError as e:
            attempt_latency = int((time.monotonic() - attempt_start) * 1000)
            if plog:
                plog.warning(
                    f"Gemini 스트리밍 API 타임아웃 (attempt {attempt + 1})",
                    pipeline_stage="generate_stream", event="api_call_timeout",
                    provider="gemini", latency_ms=attempt_latency,
                    attempt=attempt + 1, error_type="timeout",
                )
            raise PipelineTimeoutError(f"Gemini 스트리밍 API 타임아웃: {e}") from e

    # 주 모델 429 연속 실패 → 보조 모델(Gemini Pro)로 스트리밍 전환
    if primary_exhausted:
        if plog:
            plog.warning(
                f"주 모델({MODEL}) 429 연속 실패 (stream), 보조 모델({FALLBACK_MODEL})로 전환",
                pipeline_stage="generate_stream", event="model_fallback",
                model_fallback=True, fallback_model=FALLBACK_MODEL,
                primary_error="rate_limit",
            )
        else:
            logger.warning("주 모델(%s) 429 연속 실패 (stream), 보조 모델(%s)로 전환", MODEL, FALLBACK_MODEL)

        fallback_start = time.monotonic()
        try:
            fallback_stream = await client.aio.models.generate_content_stream(
                model=FALLBACK_MODEL,
                contents=prompt,
                config=genai.types.GenerateContentConfig(
                    temperature=0.3,
                    max_output_tokens=900,
                ),
            )
            fallback_latency = int((time.monotonic() - fallback_start) * 1000)
            if plog:
                plog.info(
                    f"보조 모델({FALLBACK_MODEL}) 스트리밍 연결 성공",
                    pipeline_stage="generate_stream", event="stream_connected",
                    provider="gemini", model=FALLBACK_MODEL,
                    latency_ms=fallback_latency, fallback_success=True,
                )
            async for chunk in fallback_stream:
                if chunk.text:
                    yield chunk.text
        except Exception as e:
            fallback_latency = int((time.monotonic() - fallback_start) * 1000)
            if plog:
                plog.error(
                    f"보조 모델({FALLBACK_MODEL}) 스트리밍도 실패: {e}",
                    pipeline_stage="generate_stream", event="fallback_failed",
                    provider="gemini", model=FALLBACK_MODEL,
                    latency_ms=fallback_latency, fallback_success=False,
                )
            raise RateLimitError(
                f"주 모델({MODEL})과 보조 모델({FALLBACK_MODEL}) 스트리밍 모두 실패: {e}"
            ) from e
        return

    async for chunk in stream:
        if chunk.text:
            yield chunk.text
