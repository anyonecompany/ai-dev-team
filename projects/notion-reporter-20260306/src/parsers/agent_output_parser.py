"""에이전트 출력 파싱 유틸리티."""

import json
from pathlib import Path


def parse_completion_json(file_path: str) -> dict:
    """JSON 파일에서 completion report 데이터 로드.

    Expected JSON format:
    {
        "task_name": "...",
        "status": "...",
        "summary": "...",
        "decisions": [...],
        "tech_refs": [...],
        "new_tasks": [...]
    }
    """
    data = json.loads(Path(file_path).read_text(encoding="utf-8"))

    required = ["task_name"]
    for key in required:
        if key not in data:
            raise ValueError(f"JSON \ud544\uc218 \ud544\ub4dc \ub204\ub77d: {key}")

    return {
        "task_name": data["task_name"],
        "status": data.get("status", "\u2705 \uc644\ub8cc"),
        "summary": data.get("summary", ""),
        "decisions": data.get("decisions", []),
        "tech_refs": data.get("tech_refs", []),
        "new_tasks": data.get("new_tasks", []),
    }
