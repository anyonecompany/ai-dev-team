"""프로필 빌더 모듈 테스트."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.processors.profile_builder import ProfileBuilder


def test_profile_builder_import():
    """ProfileBuilder 임포트 및 인스턴스 생성 테스트."""
    builder = ProfileBuilder()
    assert builder is not None
    assert hasattr(builder, "build_from_namuwiki")
    assert hasattr(builder, "build_from_wikipedia")
    assert hasattr(builder, "build_minimal")


def test_build_from_wikipedia():
    """ProfileBuilder.build_from_wikipedia 프로필 생성 테스트."""
    builder = ProfileBuilder()
    raw_data = {
        "extract": "Bruno Fernandes is a Portuguese professional footballer." * 5,
        "description": "Portuguese footballer",
    }
    player_info = {
        "name_kr": "브루노 페르난데스",
        "name_en": "Bruno Fernandes",
        "team": "MUN",
        "position": "MF",
    }
    profile = builder.build_from_wikipedia(raw_data, player_info)
    assert profile is not None

    required_fields = ["name_kr", "name_en", "team", "position", "play_style"]
    for field in required_fields:
        assert field in profile, f"필수 필드 누락: {field}"

    assert profile["name_kr"] == "브루노 페르난데스"
    assert profile["source"] == "wikipedia"


def test_build_minimal():
    """ProfileBuilder.build_minimal 최소 프로필 생성 테스트."""
    builder = ProfileBuilder()
    player_info = {
        "name_kr": "테스트 선수",
        "name_en": "Test Player",
        "team": "AVL",
        "position": "FW",
    }
    profile = builder.build_minimal(player_info)
    assert profile["name_kr"] == "테스트 선수"
    assert profile["source"] == "minimal"
    assert isinstance(profile["fun_facts"], list)
