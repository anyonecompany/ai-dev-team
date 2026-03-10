"""질문 분류기: Claude Sonnet으로 7개 카테고리 분류 + 키워드 추출."""

import json
import logging
import os
from pathlib import Path

import anthropic
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), "..", "..", ".env"))

logger = logging.getLogger(__name__)

PROMPTS_DIR = Path(__file__).parent / "prompts"
CLASSIFIER_PROMPT = (PROMPTS_DIR / "classifier_prompt.txt").read_text(encoding="utf-8")
FEW_SHOT_EXAMPLES = json.loads(
    (PROMPTS_DIR / "few_shot_examples.json").read_text(encoding="utf-8")
)

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

MODEL = "claude-haiku-4-5-20251001"

_anthropic_client = None


def _get_client() -> anthropic.AsyncAnthropic:
    """Anthropic 클라이언트 싱글톤."""
    global _anthropic_client
    if _anthropic_client is None:
        _anthropic_client = anthropic.AsyncAnthropic()
    return _anthropic_client


def _build_few_shot_section() -> str:
    """Few-shot 예시를 텍스트로 변환."""
    lines = ["## 예시"]
    for ex in FEW_SHOT_EXAMPLES:
        lines.append(
            f'- "{ex["question"]}" → {{"category": "{ex["category"]}", '
            f'"keywords": {json.dumps(ex["keywords"], ensure_ascii=False)}, '
            f'"confidence": 0.9}}'
        )
    return "\n".join(lines)


async def classify(question: str) -> dict:
    """질문을 7개 카테고리 중 하나로 분류하고 키워드를 추출한다.

    Args:
        question: 사용자 질문 텍스트.

    Returns:
        {"category": str, "keywords": list[str], "confidence": float}
    """
    client = _get_client()

    prompt = CLASSIFIER_PROMPT.replace("{question}", question)
    few_shot = _build_few_shot_section()

    response = await client.messages.create(
        model=MODEL,
        max_tokens=256,
        messages=[
            {
                "role": "user",
                "content": f"{few_shot}\n\n{prompt}",
            }
        ],
    )

    text = response.content[0].text.strip()
    # JSON 블록 파싱 (```json ... ``` 형태 대응)
    if "```" in text:
        text = text.split("```json")[-1].split("```")[0].strip()

    try:
        result = json.loads(text)
    except json.JSONDecodeError:
        logger.warning("분류기 JSON 파싱 실패, 기본값 반환: %s", text)
        return {
            "category": "match_flow",
            "keywords": [question],
            "confidence": 0.3,
        }

    # 유효성 검증
    if result.get("category") not in VALID_CATEGORIES:
        result["category"] = "match_flow"
        result["confidence"] = 0.3

    return {
        "category": result["category"],
        "keywords": result.get("keywords", [question]),
        "confidence": float(result.get("confidence", 0.5)),
    }
