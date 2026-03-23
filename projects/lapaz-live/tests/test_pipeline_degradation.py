"""파이프라인 graceful degradation 테스트.

각 단계 실패 시 파이프라인이 죽지 않고 부분 응답을 반환하는지 검증한다.
"""

import asyncio
import logging
import sys
from pathlib import Path
from unittest.mock import AsyncMock, patch, MagicMock

# 프로젝트 루트를 path에 추가
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.rag.pipeline import (
    _ask_inner,
    _DATA_UNAVAILABLE_ANSWER,
    _DEFAULT_CLASSIFICATION,
    OUT_OF_SCOPE_ANSWER,
)
from src.rag.logging_utils import PipelineLogger
import time

# 로깅 설정 (degradation_path 확인용)
logging.basicConfig(level=logging.WARNING, format="%(message)s")


def make_plog():
    """테스트용 PipelineLogger 생성."""
    return PipelineLogger("test-degradation", "test")


def run(coro):
    """비동기 코루틴 실행 헬퍼."""
    return asyncio.get_event_loop().run_until_complete(coro)


# 정상 응답 mock 데이터
MOCK_CLASSIFICATION = {
    "category": "match_flow",
    "keywords": ["맨유"],
    "confidence": 0.9,
}
MOCK_EMBEDDING = [0.1] * 10
MOCK_DOCUMENTS = [{"id": 1, "collection": "test", "content": "테스트 문서"}]
MOCK_STRUCTURED = "=== 테스트 구조화 데이터 ==="
MOCK_GENERATION = {
    "answer": "테스트 답변입니다.",
    "source_docs": [1],
    "generation_time_ms": 100,
}


def test_1_classify_failure():
    """시나리오 1: 분류기 실패 → 기본 카테고리로 정상 응답."""
    print("\n[테스트 1] 분류기 실패 시나리오")

    with patch("src.rag.pipeline.classify", new_callable=AsyncMock) as mock_classify, \
         patch("src.rag.pipeline.embed_query", new_callable=AsyncMock) as mock_embed, \
         patch("src.rag.pipeline.retrieve", new_callable=AsyncMock) as mock_retrieve, \
         patch("src.rag.pipeline.build_structured_context", new_callable=AsyncMock) as mock_struct, \
         patch("src.rag.pipeline.generate", new_callable=AsyncMock) as mock_gen:

        mock_classify.side_effect = RuntimeError("분류기 강제 에러")
        mock_embed.return_value = MOCK_EMBEDDING
        mock_retrieve.return_value = MOCK_DOCUMENTS
        mock_struct.return_value = MOCK_STRUCTURED
        mock_gen.return_value = MOCK_GENERATION

        plog = make_plog()
        start = time.monotonic()
        result = run(_ask_inner("맨유 전술은?", "", start, plog))

        assert result["answer"] == "테스트 답변입니다.", f"답변 불일치: {result['answer']}"
        assert result["category"] == "general_football", f"카테고리 불일치: {result['category']}"
        assert result["confidence"] == 0.0, f"confidence 불일치: {result['confidence']}"
        assert result.get("is_degraded") is True, "is_degraded 미기록"
        assert "classification_failed" in result.get("degradation_path", ""), \
            f"degradation_path 미기록: {result.get('degradation_path')}"

        print(f"  PASS: category={result['category']}, degradation_path={result['degradation_path']}")


def test_2_vector_search_failure():
    """시나리오 2: 벡터 검색(임베딩) 실패 → 키워드 검색으로 응답."""
    print("\n[테스트 2] 임베딩(벡터 검색) 실패 시나리오")

    with patch("src.rag.pipeline.classify", new_callable=AsyncMock) as mock_classify, \
         patch("src.rag.pipeline.embed_query", new_callable=AsyncMock) as mock_embed, \
         patch("src.rag.pipeline.retrieve", new_callable=AsyncMock) as mock_retrieve, \
         patch("src.rag.pipeline.build_structured_context", new_callable=AsyncMock) as mock_struct, \
         patch("src.rag.pipeline.generate", new_callable=AsyncMock) as mock_gen:

        mock_classify.return_value = MOCK_CLASSIFICATION
        mock_embed.side_effect = RuntimeError("Voyage API 에러")
        mock_retrieve.return_value = MOCK_DOCUMENTS  # 키워드 검색은 성공
        mock_struct.return_value = MOCK_STRUCTURED
        mock_gen.return_value = MOCK_GENERATION

        plog = make_plog()
        start = time.monotonic()
        result = run(_ask_inner("맨유 전술은?", "", start, plog))

        assert result["answer"] == "테스트 답변입니다.", f"답변 불일치: {result['answer']}"
        assert result.get("is_degraded") is True, "is_degraded 미기록"
        assert "embedding_failed" in result.get("degradation_path", ""), \
            f"degradation_path 미기록: {result.get('degradation_path')}"
        # retrieve에 query_embedding=None이 전달되었는지 확인
        call_kwargs = mock_retrieve.call_args
        assert call_kwargs.kwargs.get("query_embedding") is None or \
               (len(call_kwargs.args) > 4 and call_kwargs.args[4] is None) or \
               call_kwargs[1].get("query_embedding") is None, \
            "query_embedding이 None으로 전달되지 않음"

        print(f"  PASS: degradation_path={result['degradation_path']}")


def test_3_all_retrieval_failure():
    """시나리오 3: 검색 전체 실패 → 구조화 데이터만으로 응답."""
    print("\n[테스트 3] 검색 전체 실패 시나리오")

    with patch("src.rag.pipeline.classify", new_callable=AsyncMock) as mock_classify, \
         patch("src.rag.pipeline.embed_query", new_callable=AsyncMock) as mock_embed, \
         patch("src.rag.pipeline.retrieve", new_callable=AsyncMock) as mock_retrieve, \
         patch("src.rag.pipeline.build_structured_context", new_callable=AsyncMock) as mock_struct, \
         patch("src.rag.pipeline.generate", new_callable=AsyncMock) as mock_gen:

        mock_classify.return_value = MOCK_CLASSIFICATION
        mock_embed.return_value = MOCK_EMBEDDING
        mock_retrieve.side_effect = RuntimeError("Supabase 연결 실패")
        mock_struct.return_value = MOCK_STRUCTURED
        mock_gen.return_value = MOCK_GENERATION

        plog = make_plog()
        start = time.monotonic()
        result = run(_ask_inner("맨유 전술은?", "", start, plog))

        assert result["answer"] == "테스트 답변입니다.", f"답변 불일치: {result['answer']}"
        assert result.get("is_degraded") is True, "is_degraded 미기록"
        assert "retrieve_failed" in result.get("degradation_path", ""), \
            f"degradation_path 미기록: {result.get('degradation_path')}"
        # generate에 documents=[]가 전달되었는지 확인
        gen_call = mock_gen.call_args
        assert gen_call.kwargs.get("documents") == [] or \
               (len(gen_call.args) > 1 and gen_call.args[1] == []), \
            "빈 documents가 generate에 전달되지 않음"

        print(f"  PASS: degradation_path={result['degradation_path']}")


def test_4_all_data_failure():
    """시나리오 4: 검색 + 구조화 데이터 모두 실패 → 안내 메시지."""
    print("\n[테스트 4] 검색 + 구조화 데이터 모두 실패 시나리오")

    with patch("src.rag.pipeline.classify", new_callable=AsyncMock) as mock_classify, \
         patch("src.rag.pipeline.embed_query", new_callable=AsyncMock) as mock_embed, \
         patch("src.rag.pipeline.retrieve", new_callable=AsyncMock) as mock_retrieve, \
         patch("src.rag.pipeline.build_structured_context", new_callable=AsyncMock) as mock_struct, \
         patch("src.rag.pipeline.generate", new_callable=AsyncMock) as mock_gen:

        mock_classify.return_value = MOCK_CLASSIFICATION
        mock_embed.return_value = MOCK_EMBEDDING
        mock_retrieve.side_effect = RuntimeError("Supabase 연결 실패")
        mock_struct.side_effect = RuntimeError("API 서버 다운")
        mock_gen.return_value = MOCK_GENERATION  # 호출되면 안 됨

        plog = make_plog()
        start = time.monotonic()
        result = run(_ask_inner("맨유 전술은?", "", start, plog))

        assert result["answer"] == _DATA_UNAVAILABLE_ANSWER, f"안내 메시지 불일치: {result['answer']}"
        assert result.get("is_degraded") is True, "is_degraded 미기록"
        assert "no_data→fallback_answer" in result.get("degradation_path", ""), \
            f"degradation_path에 no_data 미포함: {result.get('degradation_path')}"
        # generate가 호출되지 않았는지 확인
        mock_gen.assert_not_called()

        print(f"  PASS: answer='{result['answer'][:30]}...', degradation_path={result['degradation_path']}")


def test_5_normal_request():
    """시나리오 5: 정상 요청 → 기존과 동일하게 동작."""
    print("\n[테스트 5] 정상 요청 시나리오")

    with patch("src.rag.pipeline.classify", new_callable=AsyncMock) as mock_classify, \
         patch("src.rag.pipeline.embed_query", new_callable=AsyncMock) as mock_embed, \
         patch("src.rag.pipeline.retrieve", new_callable=AsyncMock) as mock_retrieve, \
         patch("src.rag.pipeline.build_structured_context", new_callable=AsyncMock) as mock_struct, \
         patch("src.rag.pipeline.generate", new_callable=AsyncMock) as mock_gen:

        mock_classify.return_value = MOCK_CLASSIFICATION
        mock_embed.return_value = MOCK_EMBEDDING
        mock_retrieve.return_value = MOCK_DOCUMENTS
        mock_struct.return_value = MOCK_STRUCTURED
        mock_gen.return_value = MOCK_GENERATION

        plog = make_plog()
        start = time.monotonic()
        result = run(_ask_inner("맨유 전술은?", "", start, plog))

        assert result["answer"] == "테스트 답변입니다.", f"답변 불일치: {result['answer']}"
        assert result["category"] == "match_flow", f"카테고리 불일치: {result['category']}"
        assert result["confidence"] == 0.9, f"confidence 불일치: {result['confidence']}"
        assert result.get("is_degraded") is None, f"정상 요청인데 is_degraded 설정됨: {result.get('is_degraded')}"
        assert result.get("degradation_path") is None, \
            f"정상 요청인데 degradation_path 설정됨: {result.get('degradation_path')}"

        print(f"  PASS: category={result['category']}, confidence={result['confidence']}, is_degraded=None")


def test_6_structured_only_failure():
    """시나리오 6: 구조화 데이터만 실패 → 검색 결과로 응답."""
    print("\n[테스트 6] 구조화 데이터만 실패 시나리오")

    with patch("src.rag.pipeline.classify", new_callable=AsyncMock) as mock_classify, \
         patch("src.rag.pipeline.embed_query", new_callable=AsyncMock) as mock_embed, \
         patch("src.rag.pipeline.retrieve", new_callable=AsyncMock) as mock_retrieve, \
         patch("src.rag.pipeline.build_structured_context", new_callable=AsyncMock) as mock_struct, \
         patch("src.rag.pipeline.generate", new_callable=AsyncMock) as mock_gen:

        mock_classify.return_value = MOCK_CLASSIFICATION
        mock_embed.return_value = MOCK_EMBEDDING
        mock_retrieve.return_value = MOCK_DOCUMENTS
        mock_struct.side_effect = RuntimeError("API 서버 다운")
        mock_gen.return_value = MOCK_GENERATION

        plog = make_plog()
        start = time.monotonic()
        result = run(_ask_inner("맨유 전술은?", "", start, plog))

        assert result["answer"] == "테스트 답변입니다.", f"답변 불일치: {result['answer']}"
        assert result.get("is_degraded") is True, "is_degraded 미기록"
        assert "structured_data_failed" in result.get("degradation_path", ""), \
            f"degradation_path에 structured_data_failed 미포함: {result.get('degradation_path')}"
        # generate에 structured_data=""가 전달되었는지 확인
        gen_call = mock_gen.call_args
        assert gen_call.kwargs.get("structured_data") == "", \
            f"structured_data가 빈 문자열로 전달되지 않음: {gen_call.kwargs.get('structured_data')}"

        print(f"  PASS: degradation_path={result['degradation_path']}")


if __name__ == "__main__":
    print("=" * 60)
    print("파이프라인 Graceful Degradation 테스트")
    print("=" * 60)

    tests = [
        test_1_classify_failure,
        test_2_vector_search_failure,
        test_3_all_retrieval_failure,
        test_4_all_data_failure,
        test_5_normal_request,
        test_6_structured_only_failure,
    ]

    passed = 0
    failed = 0
    for test_fn in tests:
        try:
            test_fn()
            passed += 1
        except Exception as e:
            failed += 1
            print(f"  FAIL: {e}")

    print(f"\n{'=' * 60}")
    print(f"결과: {passed} PASS / {failed} FAIL (총 {len(tests)})")
    print(f"{'=' * 60}")

    sys.exit(0 if failed == 0 else 1)
