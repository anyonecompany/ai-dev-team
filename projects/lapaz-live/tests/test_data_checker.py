"""DataChecker 유닛 테스트."""

import json
import sys
import tempfile
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.validators.data_checker import DataChecker


@pytest.fixture
def checker():
    return DataChecker()


@pytest.fixture
def valid_players():
    """유효한 40명 선수 데이터."""
    players = []
    for i in range(20):
        players.append({
            "name_kr": f"맨유선수{i}",
            "name_en": f"MUN Player {i}",
            "team": "MUN",
            "position": "MF",
            "play_style": "패스형",
            "content": "x" * 150,
            "fun_facts": ["fact1"],
            "birth_date": "2000-01-01",
        })
    for i in range(20):
        players.append({
            "name_kr": f"빌라선수{i}",
            "name_en": f"AVL Player {i}",
            "team": "AVL",
            "position": "FW",
            "play_style": "공격형",
            "content": "y" * 150,
            "fun_facts": ["fact2"],
            "birth_date": "1999-06-15",
        })
    return players


def test_valid_data_passes(checker, valid_players, tmp_path):
    """유효한 데이터는 통과 (flat list)."""
    (tmp_path / "players_all.json").write_text(
        json.dumps(valid_players, ensure_ascii=False), encoding="utf-8"
    )
    results = checker.check_all(str(tmp_path))
    assert results["passed"] is True
    assert results["total_players"] == 40


def test_missing_file(checker, tmp_path):
    """파일 없으면 실패."""
    results = checker.check_all(str(tmp_path))
    assert results["passed"] is False
    assert len(results["errors"]) > 0


def test_too_few_players(checker, tmp_path):
    """선수 수 부족 시 실패."""
    players = [
        {"name_kr": "테스트", "name_en": "Test", "team": "MUN",
         "position": "MF", "play_style": "패스형", "content": "x" * 150}
    ]
    (tmp_path / "players_all.json").write_text(
        json.dumps(players, ensure_ascii=False), encoding="utf-8"
    )
    results = checker.check_all(str(tmp_path))
    assert results["passed"] is False


def test_missing_required_field(checker, tmp_path):
    """필수 필드 누락 감지."""
    players = [{"name_en": "Test", "team": "MUN"}]
    (tmp_path / "players_all.json").write_text(
        json.dumps(players, ensure_ascii=False), encoding="utf-8"
    )
    results = checker.check_all(str(tmp_path))
    assert len(results["missing_fields"]) > 0


def test_duplicate_detection(checker, tmp_path):
    """중복 선수 감지."""
    players = [
        {"name_kr": "선수A", "name_en": "Dup", "team": "MUN",
         "position": "MF", "play_style": "패스형", "content": "x" * 150},
        {"name_kr": "선수A복사", "name_en": "Dup", "team": "MUN",
         "position": "MF", "play_style": "패스형", "content": "x" * 150},
    ]
    (tmp_path / "players_all.json").write_text(
        json.dumps(players, ensure_ascii=False), encoding="utf-8"
    )
    results = checker.check_all(str(tmp_path))
    assert len(results["duplicates"]) > 0


def test_short_content_detection(checker, tmp_path):
    """짧은 content 감지."""
    players = [
        {"name_kr": "선수", "name_en": "Short", "team": "MUN",
         "position": "MF", "play_style": "패스형", "content": "짧음"}
    ]
    (tmp_path / "players_all.json").write_text(
        json.dumps(players, ensure_ascii=False), encoding="utf-8"
    )
    results = checker.check_all(str(tmp_path))
    assert len(results["short_content"]) > 0
