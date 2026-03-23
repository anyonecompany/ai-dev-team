"""질문 분류기: Gemini Flash Lite로 7개 카테고리 분류 + 키워드 추출."""

from __future__ import annotations

import json
import logging
import os
import time
from pathlib import Path
from typing import TYPE_CHECKING

from google import genai
from dotenv import load_dotenv

if TYPE_CHECKING:
    from .logging_utils import PipelineLogger

load_dotenv(os.path.join(os.path.dirname(__file__), "..", "..", ".env"))

logger = logging.getLogger(__name__)

PROMPTS_DIR = Path(__file__).parent / "prompts"
DATA_DIR = Path(__file__).parent / "data"
CLASSIFIER_PROMPT = (PROMPTS_DIR / "classifier_prompt.txt").read_text(encoding="utf-8")
FEW_SHOT_EXAMPLES = json.loads(
    (PROMPTS_DIR / "few_shot_examples.json").read_text(encoding="utf-8")
)

# 선수명 사전 로드 (없으면 빈 셋)
_PLAYER_NAMES: set[str] = set()
_player_names_path = DATA_DIR / "player_names.json"
if _player_names_path.exists():
    try:
        _player_data = json.loads(_player_names_path.read_text(encoding="utf-8"))
        _PLAYER_NAMES = {name.lower() for name in _player_data.get("players", [])}
        logger.info("선수명 사전 로드 완료: %d명", len(_PLAYER_NAMES))
    except Exception as e:
        logger.warning("선수명 사전 로드 실패, 빈 셋으로 대체: %s", e)

VALID_CATEGORIES = [
    "player_info",
    "tactical_intent",
    "match_flow",
    "player_form",
    "fan_simulation",
    "season_narrative",
    "rules_judgment",
    "out_of_scope",
]

MODEL = "gemini-2.5-flash-lite"

_gemini_client = None

SIMPLE_EXCLAMATIONS = ["ㅋ", "ㅎ", "ㄷ", "ㅇㅇ", "ㄴㄴ", "와", "오"]
DETAILED_KEYWORDS = ["분석", "비교", "설명", "왜", "어떻게", "전술", "패턴", "추세", "통계", "vs"]


def _classify_complexity(question: str) -> str:
    """질문의 복잡도를 simple/detailed로 분류한다.

    Fast Path 휴리스틱:
    - 15자 이하 + 물음표 없음 또는 감탄사 포함 → simple
    - 분석/비교/전술 등 키워드 → detailed
    - 기본값: simple (경기 중 팬 질문 대부분이 간단하므로)
    """
    stripped = question.strip()
    lowered = stripped.lower()

    # 분석/비교 키워드 → detailed (길이보다 우선)
    if any(kw in lowered for kw in DETAILED_KEYWORDS):
        return "detailed"

    # 감탄사 포함 + 짧은 텍스트 → simple
    if any(exc in lowered for exc in SIMPLE_EXCLAMATIONS):
        if len(stripped) <= 15:
            return "simple"

    # 15자 이하 + 물음표 없음 → simple
    if len(stripped) <= 15 and "?" not in stripped and "？" not in stripped:
        return "simple"

    # 기본값: simple
    return "simple"


FAST_OUT_OF_SCOPE_TERMS = [
    "날씨", "기온", "비가 ", "비 올", "비 온", "눈이 ", "환율", "비트코인", "코인", "주식", "증시",
    "대선", "대통령", "영화", "드라마", "맛집",
    "코드 짜", "코딩", "파이썬", "자바스크립트", "프로그래밍", "알고리즘 풀",
    "레시피", "요리", "다이어트", "운동 루틴", "헬스",
]

# perf: expanded fast-path triggers to cover more question patterns and avoid Haiku API calls
FAST_RULES: list[tuple[str, list[str]]] = [
    ("rules_judgment", ["오프사이드", "var", "판정", "반칙", "룰", "규칙", "레드카드", "옐로카드", "페널티"]),
    ("tactical_intent", [
        "전술", "포메이션", "빌드업", "압박", "수비 문제", "라인업", "교체 이유",
        "수비", "공격", "미드필드", "역습", "하이프레스", "맨마킹", "전술 특징",
        "예상 라인업",
    ]),
    ("player_form", ["부상", "상태", "폼", "컨디션", "복귀", "부상자", "활약", "득점"]),
    ("player_info", ["핵심 선수", "누구인가요", "누구야", "프로필", "어떤 선수", "선수 소개"]),
    ("season_narrative", [
        "시즌 성적", "성적", "상대전적", "ucl", "챔스", "이적", "홈/원정", "홈 원정",
        "이적 현황", "이적 시장", "진출 가능성", "순위", "강등", "우승",
    ]),
    ("match_flow", [
        "주목해야", "포인트", "흐름", "왜", "승부 예측", "예상", "이번 경기",
        "경기 전망", "승부처", "키 매치업", "변수",
    ]),
    ("fan_simulation", ["팬", "응원", "시뮬", "만약", "가정"]),
]


def _get_client() -> genai.Client:
    """Gemini 클라이언트 싱글톤."""
    global _gemini_client
    if _gemini_client is None:
        api_key = os.getenv("GEMINI_API_KEY")
        _gemini_client = genai.Client(api_key=api_key)
    return _gemini_client


def _build_few_shot_section() -> str:
    """Few-shot 예시를 텍스트로 변환."""
    lines = ["## 예시"]
    for ex in FEW_SHOT_EXAMPLES:
        complexity = ex.get("complexity", "simple")
        lines.append(
            f'- "{ex["question"]}" → {{"category": "{ex["category"]}", '
            f'"keywords": {json.dumps(ex["keywords"], ensure_ascii=False)}, '
            f'"confidence": 0.9, "complexity": "{complexity}"}}'
        )
    return "\n".join(lines)


def _fast_classify(question: str) -> dict | None:
    """파일럿 질문 분포에 최적화된 휴리스틱 분류."""
    lowered = question.strip().lower()
    complexity = _classify_complexity(question)
    if not lowered:
        return {
            "category": "out_of_scope",
            "keywords": [],
            "confidence": 1.0,
            "complexity": "simple",
            "_detected_keywords": [],
        }

    matched_oos = [term for term in FAST_OUT_OF_SCOPE_TERMS if term in lowered]
    if matched_oos:
        return {
            "category": "out_of_scope",
            "keywords": [question],
            "confidence": 0.98,
            "complexity": complexity,
            "_detected_keywords": matched_oos,
        }

    for category, triggers in FAST_RULES:
        matched = [trigger for trigger in triggers if trigger.lower() in lowered]
        if matched:
            return {
                "category": category,
                "keywords": matched[:3] or [question],
                "confidence": 0.9,
                "complexity": complexity,
            }

    football_terms = [
        # 기존
        "맨유", "맨체스터", "아스톤", "빌라", "프리미어", "리그", "감독", "선수", "경기",
        # 수비
        "태클", "인터셉트", "클리어런스", "블록", "수비 지표", "공중볼", "듀얼",
        # 공격
        "xg", "유효슈팅", "슈팅", "키패스", "드리블", "크로스", "찬스 메이킹",
        # 패스
        "패스 성공률", "롱패스", "숏패스", "스루패스", "패스",
        # GK
        "세이브", "클린시트", "실점", "선방", "골킥",
        # 통계
        "경고", "퇴장", "파울", "오프사이드", "코너킥", "프리킥", "페널티킥",
        # 시즌/대회
        "pl", "프리미어리그", "챔피언스리그", "ucl", "fa컵", "efl", "라리가", "분데스리가", "세리에a",
        # 영어 약어
        "xa", "ppda", "xgot", "sca", "gca",
    ]
    if any(term in lowered for term in football_terms):
        return {
            "category": "match_flow",
            "keywords": [question],
            "confidence": 0.75,
            "complexity": complexity,
        }

    # 선수명 매칭 (대소문자 무시)
    if _PLAYER_NAMES:
        for player_name in _PLAYER_NAMES:
            if player_name in lowered:
                return {
                    "category": "player_info",
                    "keywords": [question],
                    "confidence": 0.8,
                    "complexity": complexity,
                }

    return None


async def classify(question: str, *, plog: PipelineLogger | None = None) -> dict:
    """질문을 7개 카테고리 중 하나로 분류하고 키워드를 추출한다.

    Args:
        question: 사용자 질문 텍스트.
        plog: 구조화 로거 (선택).

    Returns:
        {"category": str, "keywords": list[str], "confidence": float}
    """
    start = time.monotonic()

    fast_result = _fast_classify(question)
    if fast_result is not None:
        latency = int((time.monotonic() - start) * 1000)
        if plog:
            plog.info(
                f"휴리스틱 분류: {fast_result['category']}",
                pipeline_stage="classify", event="fast_classify",
                category=fast_result["category"],
                confidence=fast_result["confidence"],
                latency_ms=latency,
                provider="heuristic",
            )
        # out_of_scope 오탐 분석용 구조화 로그
        if fast_result["category"] == "out_of_scope":
            detected = fast_result.pop("_detected_keywords", [])
            logger.info(
                "classification_out_of_scope | question=%s | confidence=%.2f | method=fast_path | detected_keywords=%s",
                question, fast_result["confidence"], detected,
                extra={
                    "event": "classification_out_of_scope",
                    "question": question,
                    "confidence": fast_result["confidence"],
                    "classification_method": "fast_path",
                    "detected_keywords": detected,
                },
            )
        else:
            fast_result.pop("_detected_keywords", None)
        return fast_result

    client = _get_client()

    prompt = CLASSIFIER_PROMPT.replace("{question}", question)
    few_shot = _build_few_shot_section()

    try:
        # perf: classifier should be fast; fallback to match_flow on error
        response = await client.aio.models.generate_content(
            model=MODEL,
            contents=f"{few_shot}\n\n{prompt}",
            config=genai.types.GenerateContentConfig(
                max_output_tokens=256,
            ),
        )
    except Exception as e:
        latency = int((time.monotonic() - start) * 1000)
        # perf: on timeout or API error, fallback to match_flow
        if plog:
            plog.warning(
                f"분류기 API 호출 실패, 기본값 반환: {e}",
                pipeline_stage="classify", event="api_error",
                error_type=type(e).__name__,
                provider="gemini",
                latency_ms=latency,
            )
        else:
            logger.warning("분류기 API 호출 실패, 기본값 반환: %s", e)
        return {
            "category": "match_flow",
            "keywords": [question],
            "confidence": 0.3,
            "complexity": _classify_complexity(question),
        }

    text = response.text.strip()
    # JSON 블록 파싱 (```json ... ``` 형태 대응)
    if "```" in text:
        text = text.split("```json")[-1].split("```")[0].strip()

    try:
        result = json.loads(text)
    except (json.JSONDecodeError, Exception) as e:
        latency = int((time.monotonic() - start) * 1000)
        if plog:
            plog.warning(
                f"분류기 JSON 파싱 실패: {e}",
                pipeline_stage="classify", event="parse_error",
                error_type="JSONDecodeError",
                provider="gemini",
                latency_ms=latency,
            )
        else:
            logger.warning("분류기 JSON 파싱 실패, 기본값 반환: %s (error: %s)", text, e)
        return {
            "category": "match_flow",
            "keywords": [question],
            "confidence": 0.3,
            "complexity": _classify_complexity(question),
        }

    # 유효성 검증
    if result.get("category") not in VALID_CATEGORIES:
        result["category"] = "match_flow"
        result["confidence"] = 0.3

    # LLM이 complexity를 반환했으면 사용, 아니면 휴리스틱으로 판단
    llm_complexity = result.get("complexity")
    if llm_complexity not in ("simple", "detailed"):
        llm_complexity = _classify_complexity(question)

    final = {
        "category": result["category"],
        "keywords": result.get("keywords", [question]),
        "confidence": float(result.get("confidence", 0.5)),
        "complexity": llm_complexity,
    }

    latency = int((time.monotonic() - start) * 1000)
    if plog:
        plog.info(
            f"LLM 분류: {final['category']}",
            pipeline_stage="classify", event="llm_classify",
            category=final["category"],
            confidence=final["confidence"],
            provider="gemini",
            latency_ms=latency,
        )

    # out_of_scope 오탐 분석용 구조화 로그
    if final["category"] == "out_of_scope":
        logger.info(
            "classification_out_of_scope | question=%s | confidence=%.2f | method=llm | detected_keywords=%s",
            question, final["confidence"], final["keywords"],
            extra={
                "event": "classification_out_of_scope",
                "question": question,
                "confidence": final["confidence"],
                "classification_method": "llm",
                "detected_keywords": final["keywords"],
            },
        )

    return final
