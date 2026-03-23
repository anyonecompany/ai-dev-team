"""generator 유틸 테스트."""

import sys
import types
from pathlib import Path

# src/ 를 sys.path에 추가하여 rag 패키지 내 상대 임포트가 동작하도록 한다.
_SRC_DIR = str(Path(__file__).resolve().parent.parent / "src")
if _SRC_DIR not in sys.path:
    sys.path.insert(0, _SRC_DIR)

if "google.genai" not in sys.modules:
    genai_module = types.ModuleType("google.genai")

    class _DummyClient:
        def __init__(self, *args, **kwargs):
            pass

    genai_module.Client = _DummyClient
    genai_module.types = types.SimpleNamespace(GenerateContentConfig=object)

    # google.genai.errors 스텁 (ClientError import 대응)
    errors_module = types.ModuleType("google.genai.errors")
    errors_module.ClientError = type("ClientError", (Exception,), {})
    genai_module.errors = errors_module
    sys.modules["google.genai.errors"] = errors_module

    google_module = sys.modules.setdefault("google", types.ModuleType("google"))
    google_module.genai = genai_module
    sys.modules["google.genai"] = genai_module

from rag.generator import _trim_to_last_sentence


def test_trim_to_last_sentence_keeps_complete_punctuated_text():
    text = "맨유는 최근 흐름이 좋습니다. 빌라도 압박 강도가 높아요."
    assert _trim_to_last_sentence(text) == text


def test_trim_to_last_sentence_trims_to_last_korean_ending_before_cutoff():
    text = "죄송해요, 오늘 맨유와 아스톤 빌라 경기의 주심이 누구인지에 대한 정보는 제가 가지고 있지 않"
    assert _trim_to_last_sentence(text) == "죄송해요."


def test_trim_to_last_sentence_trims_after_complete_korean_sentence_without_punctuation():
    text = "맨유가 중원 점유에서 우세합니다 하지만 측면 전환 속도는 더 끌어올려야"
    assert _trim_to_last_sentence(text) == "맨유가 중원 점유에서 우세합니다."
