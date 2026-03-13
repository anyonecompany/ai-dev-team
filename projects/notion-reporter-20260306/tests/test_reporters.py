"""Reporter 모듈 단위 테스트 (Notion API mock)."""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


def _mock_env(monkeypatch):
    monkeypatch.setenv("NOTION_API_KEY", "test_key")
    monkeypatch.setenv("NOTION_TASK_DB_ID", "task_db")
    monkeypatch.setenv("NOTION_PROJECT_DB_ID", "proj_db")
    monkeypatch.setenv("NOTION_DECISION_DB_ID", "dec_db")
    monkeypatch.setenv("NOTION_TECHREF_DB_ID", "tech_db")


class TestTaskReporter:
    def test_add_task_builds_correct_properties(self, monkeypatch):
        _mock_env(monkeypatch)

        mock_client = MagicMock()
        mock_client.query_db.return_value = [{"id": "proj-123"}]
        mock_client.create_page.return_value = {"id": "task-456"}

        with patch("src.reporters.task_reporter.get_client", return_value=mock_client):
            from src.reporters.task_reporter import add_task
            result = add_task("Test Task", priority="\ud83d\udd34 P0", project_name="MyProject")

        assert result["id"] == "task-456"
        call_args = mock_client.create_page.call_args
        props = call_args[0][1] if len(call_args[0]) > 1 else call_args[1].get("properties", call_args[0][1])
        assert "\ud0dc\uc2a4\ud06c\uba85" in props

    def test_update_status_not_found(self, monkeypatch):
        _mock_env(monkeypatch)

        mock_client = MagicMock()
        mock_client.query_db.return_value = []

        with patch("src.reporters.task_reporter.get_client", return_value=mock_client):
            from src.reporters.task_reporter import update_status
            result = update_status("NonExistent", "\u2705 \uc644\ub8cc")

        assert result is None


class TestDecisionReporter:
    def test_add_decision(self, monkeypatch):
        _mock_env(monkeypatch)

        mock_client = MagicMock()
        mock_client.create_page.return_value = {"id": "dec-789"}

        with patch("src.reporters.decision_reporter.get_client", return_value=mock_client):
            from src.reporters.decision_reporter import add_decision
            result = add_decision(
                title="Use FastAPI",
                category="\uae30\uc220\uc120\ud0dd",
                decision="FastAPI \uc0ac\uc6a9",
                rationale="\ube60\ub978 \uac1c\ubc1c \uc18d\ub3c4",
            )

        assert result["id"] == "dec-789"


class TestTechRefReporter:
    def test_text_to_blocks(self, monkeypatch):
        _mock_env(monkeypatch)
        from src.reporters.techref_reporter import _text_to_blocks

        blocks = _text_to_blocks("# Heading\n- item1\n- item2\nparagraph")
        assert len(blocks) == 4
        assert blocks[0]["type"] == "heading_2"
        assert blocks[1]["type"] == "bulleted_list_item"
        assert blocks[3]["type"] == "paragraph"


class TestAgentOutputParser:
    def test_parse_completion_json(self, monkeypatch, tmp_path):
        _mock_env(monkeypatch)
        import json
        f = tmp_path / "report.json"
        f.write_text(json.dumps({"task_name": "Test", "summary": "Done"}))

        from src.parsers.agent_output_parser import parse_completion_json
        data = parse_completion_json(str(f))
        assert data["task_name"] == "Test"
        assert data["status"] == "\u2705 \uc644\ub8cc"
