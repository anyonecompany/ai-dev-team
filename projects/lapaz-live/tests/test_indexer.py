"""Supabase 인덱서 모듈 테스트.

SupabaseIndexer는 생성 시 Supabase 연결이 필요하므로,
_build_content_text만 직접 테스트하고 인스턴스 생성은 Supabase 접근 가능 시만 실행.
"""

import os
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


@pytest.fixture
def indexer():
    """SupabaseIndexer 인스턴스 (Supabase 환경변수 필요)."""
    from src.config import SUPABASE_URL, SUPABASE_SERVICE_KEY
    from src.embeddings.indexer import SupabaseIndexer

    return SupabaseIndexer(
        supabase_url=SUPABASE_URL,
        supabase_key=SUPABASE_SERVICE_KEY,
    )


def test_supabase_indexer_import():
    """SupabaseIndexer 클래스 임포트 테스트."""
    from src.embeddings.indexer import SupabaseIndexer

    assert SupabaseIndexer is not None
    assert hasattr(SupabaseIndexer, "index_player")
    assert hasattr(SupabaseIndexer, "_build_content_text")


def test_content_text_build(indexer):
    """_build_content_text 메서드 테스트."""
    profile = {
        "name_kr": "브루노 페르난데스",
        "name_en": "Bruno Fernandes",
        "team": "MUN",
        "team_kr": "맨체스터 유나이티드",
        "position": "MF",
        "play_style": "패스 마스터, 롱레인지 슈팅",
        "career_summary": "포르투갈 출신 미드필더",
        "one_line_summary": "맨유의 핵심 미드필더",
        "fun_facts": ["득점 왕", "캡틴"],
    }
    content = indexer._build_content_text(profile)
    assert isinstance(content, str)
    assert "브루노 페르난데스" in content
    assert "Bruno Fernandes" in content
    assert "MUN" in content
    assert len(content) > 50
