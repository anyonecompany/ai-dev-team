# Phase 2: Monday.com 올인원 보드 + CLAUDE.md 튜닝 + QA 개선 (최종)

## 개요

기존 `_archive/dashboard/backend/services/monday_sync.py`의 좋은 패턴(rate limit 재시도, fire-and-forget, 마일스톤/산출물 추적)을 살려서 올인원 보드 구조로 통합한다.

1. `integrations/monday/monday_sync.py` 전면 재작성
2. `.claude/CLAUDE.md` 세부 튜닝
3. QA 커맨드 개선
4. 테스트 스크립트 작성
5. 커밋 + push

---

## 1. integrations/monday/monday_sync.py 전면 재작성

기존 파일을 **삭제 후** 아래 내용으로 새로 생성한다.

```python
"""
Monday.com 올인원 보드 동기화 모듈.

보드: AI Dev Team Hub (1개)
그룹:
  - 📁 프로젝트: 프로젝트별 진행 현황 + 마일스톤 + 산출물
  - 🧪 QA 결과: QA 실행 결과 기록
  - 🤖 에이전트 활동: 에이전트별 작업 로그

기존 대시보드의 rate limit 재시도, fire-and-forget 패턴을 계승.
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
from datetime import datetime, timezone
from typing import Any, Optional

import httpx

logger = logging.getLogger(__name__)

# ─── 환경변수 ────────────────────────────────────────────
# .env는 호출 측에서 load_dotenv()로 미리 로드되어 있다고 가정
MONDAY_API_TOKEN = os.getenv("MONDAY_API_TOKEN", "")
MONDAY_API_URL = "https://api.monday.com/v2"

# ─── 상수 ────────────────────────────────────────────────
BOARD_NAME = "AI Dev Team Hub"

GROUP_PROJECTS = "📁 프로젝트"
GROUP_QA = "🧪 QA 결과"
GROUP_AGENT_LOG = "🤖 에이전트 활동"

MAX_RETRIES = 3
RETRY_DELAY = 1.0  # 초 (exponential backoff 기준)

# ─── 캐시 ────────────────────────────────────────────────
_board_id: int | None = None
_group_ids: dict[str, str] = {}
_column_ids: dict[str, str] = {}  # 컬럼 title → id 매핑

# ─── 매핑 파일 ───────────────────────────────────────────
_MAPPING_DIR = os.path.dirname(os.path.abspath(__file__))


def _mapping_path(filename: str) -> str:
    return os.path.join(_MAPPING_DIR, filename)


def _load_json(filename: str) -> dict:
    path = _mapping_path(filename)
    if os.path.exists(path):
        with open(path) as f:
            return json.load(f)
    return {}


def _save_json(filename: str, data: dict) -> None:
    path = _mapping_path(filename)
    with open(path, "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _today_str() -> str:
    return _now().strftime("%Y-%m-%d")


# ─── 상태 유틸 ───────────────────────────────────────────

TASK_STATUS_MAP = {
    "TODO": "TODO",
    "IN_PROGRESS": "진행중",
    "REVIEW": "리뷰",
    "DONE": "완료",
    "BLOCKED": "차단됨",
}

AGENT_NAMES = [
    "Orchestrator",
    "PM-Planner",
    "Architect",
    "Designer",
    "BE-Developer",
    "FE-Developer",
    "AI-Engineer",
    "QA-DevOps",
    "Security-Developer",
]


def _qa_label(val: bool | None) -> dict:
    """QA 결과를 Monday.com 상태 라벨로 변환."""
    if val is None:
        return {"label": "SKIP"}
    return {"label": "PASS" if val else "FAIL"}


# ============================================================================
# GraphQL API (rate limit 재시도 포함)
# ============================================================================

def is_monday_enabled() -> bool:
    """Monday.com 연동이 활성화되어 있는지 확인."""
    return bool(MONDAY_API_TOKEN)


async def _api(query: str, variables: dict[str, Any] | None = None) -> dict[str, Any]:
    """Monday.com GraphQL API 호출 (rate limit 재시도 포함).

    - ComplexityBudgetExhausted / 429 시 exponential backoff
    - MAX_RETRIES 횟수까지 재시도
    - 실패 시 빈 dict 반환 (fire-and-forget 호환)
    """
    if not MONDAY_API_TOKEN:
        logger.debug("monday_api_token_not_set")
        return {}

    headers = {
        "Authorization": MONDAY_API_TOKEN,
        "Content-Type": "application/json",
        "API-Version": "2024-10",
    }
    payload: dict[str, Any] = {"query": query}
    if variables:
        payload["variables"] = variables

    for attempt in range(MAX_RETRIES):
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.post(MONDAY_API_URL, json=payload, headers=headers)
                resp.raise_for_status()
                data = resp.json()

                if "errors" in data:
                    errors = data["errors"]
                    is_rate_limited = any(
                        "ComplexityBudgetExhausted" in str(e)
                        or "rate limit" in str(e).lower()
                        for e in errors
                    )
                    if is_rate_limited and attempt < MAX_RETRIES - 1:
                        wait = RETRY_DELAY * (2 ** attempt)
                        logger.warning("monday_rate_limited", attempt=attempt + 1, wait=wait)
                        await asyncio.sleep(wait)
                        continue

                    logger.warning("monday_graphql_error", errors=errors, query=query[:100])
                    return {}

                return data.get("data", {})

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 429 and attempt < MAX_RETRIES - 1:
                wait = RETRY_DELAY * (2 ** attempt)
                logger.warning("monday_429", attempt=attempt + 1, wait=wait)
                await asyncio.sleep(wait)
                continue
            logger.error("monday_http_error", status=e.response.status_code, detail=str(e))
            return {}

        except Exception as e:
            logger.error("monday_request_error", error=str(e), attempt=attempt + 1)
            if attempt < MAX_RETRIES - 1:
                await asyncio.sleep(RETRY_DELAY * (2 ** attempt))
                continue
            return {}

    return {}


# ============================================================================
# Fire-and-forget 유틸
# ============================================================================

def fire_and_forget(coro) -> None:
    """비동기 코루틴을 fire-and-forget으로 실행.

    Monday.com API 호출이 메인 워크플로우를 블로킹하지 않도록.
    """
    async def wrapper():
        try:
            await coro
        except Exception as e:
            logger.error("monday_fire_and_forget_error", error=str(e))

    try:
        loop = asyncio.get_running_loop()
        loop.create_task(wrapper())
    except RuntimeError:
        # 이벤트 루프가 없으면 직접 실행
        asyncio.run(wrapper())


# ============================================================================
# 보드/그룹 초기화
# ============================================================================

async def ensure_board() -> int | None:
    """'AI Dev Team Hub' 보드를 찾거나 생성한다."""
    global _board_id, _column_ids

    if _board_id:
        return _board_id

    # .env MONDAY_BOARD_ID가 있으면 사용
    env_id = os.getenv("MONDAY_BOARD_ID", "")
    if env_id and env_id.isdigit():
        _board_id = int(env_id)
        # 컬럼 ID 로드
        await _load_column_ids()
        return _board_id

    # 기존 보드 검색
    result = await _api("{ boards(limit: 100) { id name } }")
    for board in result.get("boards", []):
        if board["name"] == BOARD_NAME:
            _board_id = int(board["id"])
            logger.info("monday_board_found", board_id=_board_id)
            await _load_column_ids()
            return _board_id

    # 없으면 생성
    result = await _api(
        'mutation ($name: String!) { create_board(board_name: $name, board_kind: public) { id } }',
        {"name": BOARD_NAME},
    )
    if result.get("create_board"):
        _board_id = int(result["create_board"]["id"])
        logger.info("monday_board_created", board_id=_board_id)
        await _ensure_columns()
        return _board_id

    logger.error("monday_board_ensure_failed")
    return None


async def _load_column_ids() -> None:
    """보드의 컬럼 title → id 매핑을 로드."""
    global _column_ids
    if not _board_id:
        return

    result = await _api(
        "query ($id: [ID!]!) { boards(ids: $id) { columns { id title type } } }",
        {"id": _board_id},
    )
    for board in result.get("boards", []):
        for col in board.get("columns", []):
            _column_ids[col["title"]] = col["id"]


async def _ensure_columns() -> None:
    """올인원 보드에 필요한 컬럼을 생성 (없는 것만)."""
    if not _board_id:
        return

    await _load_column_ids()

    # 필요한 컬럼 정의
    REQUIRED_COLUMNS = [
        ("상태", "status", {"labels": {"0": "TODO", "1": "진행중", "2": "리뷰", "3": "완료", "4": "차단됨"}}),
        ("담당 에이전트", "dropdown", None),
        ("기술 스택", "tags", None),
        ("QA 종합", "status", {"labels": {"0": "PASS", "1": "FAIL", "2": "SKIP"}}),
        ("린트", "status", {"labels": {"0": "PASS", "1": "FAIL", "2": "SKIP"}}),
        ("타입체크", "status", {"labels": {"0": "PASS", "1": "FAIL", "2": "SKIP"}}),
        ("테스트", "status", {"labels": {"0": "PASS", "1": "FAIL", "2": "SKIP"}}),
        ("빌드", "status", {"labels": {"0": "PASS", "1": "FAIL", "2": "SKIP"}}),
        ("GitHub 링크", "link", None),
        ("설명", "long_text", None),
        ("날짜", "date", None),
        ("진행률", "numbers", None),
    ]

    for title, col_type, defaults in REQUIRED_COLUMNS:
        if title in _column_ids:
            continue

        variables: dict[str, Any] = {
            "board_id": str(_board_id),
            "title": title,
            "column_type": col_type,
        }

        if defaults:
            variables["defaults"] = json.dumps(defaults)
            query = """mutation($board_id: ID!, $title: String!, $column_type: ColumnType!, $defaults: JSON) {
                create_column(board_id: $board_id, title: $title, column_type: $column_type, defaults: $defaults) { id title }
            }"""
        else:
            query = """mutation($board_id: ID!, $title: String!, $column_type: ColumnType!) {
                create_column(board_id: $board_id, title: $title, column_type: $column_type) { id title }
            }"""

        result = await _api(query, variables)
        if result.get("create_column"):
            _column_ids[title] = result["create_column"]["id"]
            logger.info("monday_column_created", title=title, id=_column_ids[title])


async def ensure_groups() -> dict[str, str]:
    """3개 그룹(프로젝트/QA/에이전트활동)을 찾거나 생성한다."""
    global _group_ids

    if _group_ids:
        return _group_ids

    board_id = await ensure_board()
    if not board_id:
        return {}

    result = await _api(
        "query ($id: [ID!]!) { boards(ids: $id) { groups { id title } } }",
        {"id": board_id},
    )
    existing = {}
    for board in result.get("boards", []):
        for group in board.get("groups", []):
            existing[group["title"]] = group["id"]

    for group_name in [GROUP_PROJECTS, GROUP_QA, GROUP_AGENT_LOG]:
        if group_name in existing:
            _group_ids[group_name] = existing[group_name]
        else:
            res = await _api(
                "mutation ($bid: ID!, $name: String!) { create_group(board_id: $bid, group_name: $name) { id } }",
                {"bid": board_id, "name": group_name},
            )
            gid = res.get("create_group", {}).get("id", "")
            if gid:
                _group_ids[group_name] = gid
                logger.info("monday_group_created", group=group_name, id=gid)

    return _group_ids


async def _ensure_ready() -> tuple[int | None, dict[str, str]]:
    """보드 + 그룹이 준비되었는지 확인."""
    board_id = await ensure_board()
    groups = await ensure_groups()
    return board_id, groups


# ============================================================================
# 아이템 생성/수정 공통
# ============================================================================

async def _create_item(
    group_name: str,
    item_name: str,
    column_values: dict[str, Any] | None = None,
) -> str:
    """지정된 그룹에 아이템 생성."""
    board_id, groups = await _ensure_ready()
    if not board_id or group_name not in groups:
        return ""

    cv = json.dumps(column_values) if column_values else "{}"

    result = await _api(
        """mutation ($bid: ID!, $gid: String!, $name: String!, $cv: JSON!) {
            create_item(board_id: $bid, group_id: $gid, item_name: $name, column_values: $cv) { id }
        }""",
        {"bid": board_id, "gid": groups[group_name], "name": item_name, "cv": cv},
    )
    item_id = result.get("create_item", {}).get("id", "")
    if item_id:
        logger.info("monday_item_created", group=group_name, name=item_name, id=item_id)
    return item_id


async def _update_item(item_id: str, column_values: dict[str, Any]) -> bool:
    """아이템 컬럼 값 업데이트."""
    board_id = await ensure_board()
    if not board_id or not item_id:
        return False

    result = await _api(
        """mutation ($bid: ID!, $iid: ID!, $cv: JSON!) {
            change_multiple_column_values(board_id: $bid, item_id: $iid, column_values: $cv) { id }
        }""",
        {"bid": board_id, "iid": item_id, "cv": json.dumps(column_values)},
    )
    return bool(result.get("change_multiple_column_values"))


async def _add_update(item_id: str, body: str) -> None:
    """아이템에 댓글(업데이트) 추가."""
    await _api(
        'mutation ($iid: ID!, $body: String!) { create_update(item_id: $iid, body: $body) { id } }',
        {"iid": item_id, "body": body},
    )


def _col(title: str) -> str:
    """컬럼 title로 id를 조회. 없으면 title 그대로 반환."""
    return _column_ids.get(title, title)


def _cv(**kwargs) -> dict[str, Any]:
    """컬럼 값 딕셔너리를 컬럼 ID 기반으로 생성.

    사용법: _cv(상태={"label": "TODO"}, 날짜={"date": "2026-02-09"})
    """
    return {_col(k): v for k, v in kwargs.items()}


# ============================================================================
# 📁 프로젝트 관리
# ============================================================================

async def create_project(
    project_name: str,
    description: str = "",
    tech_stack: list[str] | None = None,
    github_link: str = "",
) -> str:
    """📁 프로젝트 그룹에 프로젝트 아이템 생성."""
    columns = _cv(
        상태={"label": "TODO"},
        날짜={"date": _today_str()},
    )
    if description:
        columns[_col("설명")] = description
    if tech_stack:
        columns[_col("기술 스택")] = {"tags": tech_stack}
    if github_link:
        columns[_col("GitHub 링크")] = {"url": github_link, "text": "GitHub"}

    item_id = await _create_item(GROUP_PROJECTS, project_name, columns)

    if item_id:
        mapping = _load_json(".monday_project_map.json")
        mapping[project_name] = {"item_id": item_id, "created": _now().isoformat()}
        _save_json(".monday_project_map.json", mapping)

    return item_id


async def update_project_status(project_name: str, status: str) -> bool:
    """프로젝트 상태 업데이트. status: TODO/진행중/리뷰/완료/차단됨"""
    mapping = _load_json(".monday_project_map.json")
    item_id = mapping.get(project_name, {}).get("item_id", "")
    if not item_id:
        return False

    columns = _cv(상태={"label": status})
    if status == "완료":
        columns[_col("날짜")] = {"date": _today_str()}
    return await _update_item(item_id, columns)


async def update_project_progress(
    project_name: str,
    total: int,
    completed: int,
    blocked: int,
    phase: str = "",
) -> bool:
    """프로젝트 진행률 업데이트."""
    mapping = _load_json(".monday_project_map.json")
    item_id = mapping.get(project_name, {}).get("item_id", "")
    if not item_id:
        return False

    pct = round((completed / total * 100) if total > 0 else 0, 1)

    columns = _cv(진행률=str(pct))
    if phase:
        columns[_col("설명")] = f"Phase: {phase} | {completed}/{total} done, {blocked} blocked"

    # 상태 자동 판정
    if pct >= 100:
        columns[_col("상태")] = {"label": "완료"}
    elif completed > 0:
        columns[_col("상태")] = {"label": "진행중"}

    return await _update_item(item_id, columns)


async def log_project_milestone(
    project_name: str,
    milestone_name: str,
    completed: bool = False,
) -> str:
    """프로젝트 마일스톤을 프로젝트 그룹에 기록."""
    columns = _cv(
        상태={"label": "완료" if completed else "진행중"},
        담당_에이전트={"labels": ["Orchestrator"]},
        날짜={"date": _today_str()},
    )
    return await _create_item(GROUP_PROJECTS, f"[Milestone] {project_name}: {milestone_name}", columns)


async def log_project_deliverables(
    project_name: str,
    files: list[dict[str, Any]],
) -> str:
    """프로젝트 산출물을 프로젝트 그룹에 기록."""
    if not files:
        return ""

    file_summary = ", ".join(f.get("filepath", "unknown") for f in files[:10])
    if len(files) > 10:
        file_summary += f" (+{len(files) - 10} more)"

    columns = _cv(
        상태={"label": "완료"},
        설명=f"{len(files)} files: {file_summary}",
        날짜={"date": _today_str()},
    )
    item_id = await _create_item(
        GROUP_PROJECTS,
        f"[Deliverables] {project_name} ({len(files)} files)",
        columns,
    )

    if item_id:
        # 상세 파일 목록을 댓글로 추가
        details = "\n".join(
            f"- {f.get('filepath', '?')} ({f.get('language', '?')}, {f.get('size', '?')} bytes)"
            for f in files
        )
        await _add_update(item_id, f"산출물 목록:\n{details}")

    return item_id


# ============================================================================
# 🧪 QA 결과 기록
# ============================================================================

async def log_qa_result(
    project_name: str,
    lint: bool | None = None,
    typecheck: bool | None = None,
    tests: bool | None = None,
    build: bool | None = None,
    details: str = "",
    agent: str = "QA-DevOps",
) -> str:
    """🧪 QA 결과 그룹에 실행 결과 기록."""
    results = [lint, typecheck, tests, build]
    has_any = any(v is not None for v in results)
    all_passed = all(v is True for v in results if v is not None) if has_any else None

    now = _now()
    columns = _cv(
        상태={"label": "완료"},
        날짜={"date": now.strftime("%Y-%m-%d")},
    )
    columns[_col("QA 종합")] = _qa_label(all_passed)
    columns[_col("린트")] = _qa_label(lint)
    columns[_col("타입체크")] = _qa_label(typecheck)
    columns[_col("테스트")] = _qa_label(tests)
    columns[_col("빌드")] = _qa_label(build)

    if details:
        columns[_col("설명")] = details

    item_name = f"QA: {project_name} ({now.strftime('%m/%d %H:%M')})"
    return await _create_item(GROUP_QA, item_name, columns)


async def sync_project_qa(
    project_name: str,
    results: dict[str, bool | None],
    details: str = "",
) -> str:
    """QA 결과 기록 + 프로젝트 상태 자동 업데이트."""
    item_id = await log_qa_result(
        project_name=project_name,
        lint=results.get("lint"),
        typecheck=results.get("typecheck"),
        tests=results.get("tests"),
        build=results.get("build"),
        details=details,
    )

    all_passed = all(v is True for v in results.values() if v is not None)
    await update_project_status(project_name, "완료" if all_passed else "차단됨")

    return item_id


# ============================================================================
# 🤖 에이전트 활동 로그
# ============================================================================

async def log_agent_activity(
    agent: str,
    action: str,
    description: str = "",
    github_link: str = "",
    status: str = "완료",
) -> str:
    """🤖 에이전트 활동 그룹에 활동 로그 기록."""
    columns = _cv(
        상태={"label": status},
        날짜={"date": _today_str()},
    )
    if description:
        columns[_col("설명")] = description
    if github_link:
        columns[_col("GitHub 링크")] = {"url": github_link, "text": "GitHub"}

    return await _create_item(GROUP_AGENT_LOG, f"{agent}: {action}", columns)


# ============================================================================
# 초기화
# ============================================================================

async def initialize() -> None:
    """Monday.com 연동 초기화: 보드/그룹/컬럼 확인 및 생성."""
    if not is_monday_enabled():
        logger.warning("monday_token_not_configured")
        return

    await ensure_board()
    await ensure_groups()
    logger.info("monday_initialized", board_id=_board_id, groups=list(_group_ids.keys()))


def get_board_url() -> str:
    """Monday.com 보드 URL."""
    if _board_id:
        return f"https://view.monday.com/board/{_board_id}"
    return ""
```

---

## 2. .claude/CLAUDE.md 세부 튜닝

CLAUDE.md에서 아래 변경을 수행한다.

### 2-1. "프로젝트 정보" 테이블 수정

기존:
```
| 현재 단계 | MVP 완료 / 고도화 진행 중 |
| 버전 | v0.2.0 |
```

변경:
```
| 현재 단계 | Claude 에이전트 팀 구조 전환 완료 |
| 버전 | v1.0.0 |
| GitHub | https://github.com/anyonecompany/ai-dev-team |
```

### 2-2. "기술 스택" 섹션을 교체

기존 Backend/Frontend/인프라 3개 섹션 전체를 아래로 교체:

```markdown
## 기술 스택

### 핵심 (Claude 에이전트 팀)
- 에이전트 오케스트레이션: Claude 에이전트 팀 (Opus 4.6 기반)
- 프로젝트 관리: Monday.com (올인원 보드 "AI Dev Team Hub")
- 알림: Slack 웹훅
- 코드 저장소: GitHub (anyonecompany/ai-dev-team)

### 프로젝트별 기술 스택 (필요에 따라 선택)
- Backend: Python 3.11+ / FastAPI / Supabase (PostgreSQL)
- Frontend: React 18+ / TypeScript / Vite / Zustand / Tailwind CSS
- 인프라: Docker / Vercel / Railway / GitHub Actions

### 외부 연동
- Slack: 웹훅 기반 알림 (`integrations/slack/slack_notifier.py`)
- Monday.com: GraphQL API 올인원 보드 (`integrations/monday/monday_sync.py`)
- GitHub: gh CLI + API
```

### 2-3. "작업 프로토콜" 섹션을 교체

기존 "작업 시작 전", "작업 중", "작업 완료 후" 전체를 아래로 교체:

```markdown
## 작업 프로토콜

### 새 프로젝트 시작
1. `projects/` 하위에 `{project-name}-{YYYYMMDDHHMMSS}` 폴더 생성
2. README.md, .gitignore, 기본 구조 생성
3. Monday.com에 프로젝트 등록 → `create_project()`
4. Slack에 프로젝트 생성 알림 → `notify_project_created()`
5. 에이전트 활동 로그 기록 → `log_agent_activity()`

### 작업 중
1. Monday.com 프로젝트 상태를 "진행중"으로 → `update_project_status()`
2. 주요 작업마다 에이전트 활동 로그 기록
3. 마일스톤 달성 시 기록 → `log_project_milestone()`
4. 코드 변경 시 커밋 + push

### 작업 완료 후
1. QA 실행 → `/qa` 커맨드
2. QA 통과 시:
   - Monday.com에 QA 결과 기록 → `log_qa_result()`
   - 프로젝트 상태 "완료"로 업데이트
   - 산출물 기록 → `log_project_deliverables()`
   - Slack에 결과 알림
   - 커밋 + push
3. QA 실패 시:
   - `/qa-fix`로 자동 수정 시도 (최대 3회)
   - Monday.com에 실패 결과 기록, 상태 "차단됨"
```

### 2-4. "디렉토리 구조" 섹션 교체

기존 `.claude/` 내부 구조만 있는 것을 루트 구조 포함으로 교체:

```markdown
## 디렉토리 구조

### 루트
```
ai-dev-team/
├── .claude/              ← 에이전트 설정, 커맨드, 템플릿
├── projects/             ← 모든 개발 프로젝트 (하위 폴더로 자동 생성)
├── integrations/         ← 외부 서비스 연동
│   ├── slack/            ← Slack 웹훅 알림
│   ├── monday/           ← Monday.com 올인원 보드
│   └── shared/           ← 공용 포맷팅 유틸
├── tasks/                ← 글로벌 태스크 관리
├── scripts/              ← 공용 스크립트
└── _archive/             ← 아카이브 (참조만, 수정 금지)
```

### .claude/ 내부
```
.claude/
├── CLAUDE.md              ← 마스터 헌장
├── agents/                ← 에이전트 프로필
├── commands/              ← 커맨드 (/qa, /qa-fix, /qa-report)
├── docs/                  ← 운영 문서, 법규 가이드
├── tasks/                 ← 태스크 관리
├── templates/             ← 프로젝트/태스크 템플릿
├── handoff/               ← 인수인계 문서
├── context/               ← 프로젝트 컨텍스트
├── scripts/               ← 자동화 스크립트
├── knowledge/             ← 지식 베이스
├── reports/               ← QA/활동 리포트
└── settings.local.json    ← 로컬 설정
```
```

### 2-5. 맨 하단 중복 섹션 삭제

CLAUDE.md 맨 끝에 Phase 1에서 추가된 중복 섹션들을 삭제:
- "## 프로젝트 구조" (중복)
- "## 프로젝트 생성 규칙" (중복)
- "## QA 규칙" (중복)
- "## 연동 규칙" (중복)
- "## 금지 사항 (구조 개편 이후 추가)" (중복)

이 내용들은 위에서 이미 통합되었으므로 삭제한다.

### 2-6. "변경 이력" 테이블에 추가

```
| 3.0.0 | 2026-02-09 | Claude 에이전트 팀 구조 전환, Monday.com 올인원 보드, QA 커맨드 신설 |
```

---

## 3. QA 커맨드 개선

### .claude/commands/qa.md 재작성

```markdown
# /qa - QA 전체 실행

대상 프로젝트에 전체 QA를 실행하고 결과를 Monday.com과 Slack에 공유한다.

## 사용법
```
/qa                    # 가장 최근 수정된 프로젝트 대상
/qa {project-name}     # 특정 프로젝트 대상
```

## 절차

### 1. 프로젝트 감지
- 인자가 있으면 `projects/{project-name}*` 에서 찾기
- 없으면 `projects/` 하위에서 가장 최근 수정된 폴더

### 2. 프로젝트 유형 감지
- `package.json` → Node.js/React
- `requirements.txt` 또는 `pyproject.toml` → Python
- 둘 다 → Fullstack (둘 다 실행)

### 3. 검증 실행

**Python:**
```bash
ruff check . 2>&1
mypy . 2>&1 || pyright .
pytest --tb=short 2>&1
```

**Node.js/React:**
```bash
npm run lint 2>&1 || npx eslint . 2>&1
npx tsc --noEmit 2>&1
npm test 2>&1
npm run build 2>&1
```

### 4. 결과 종합
각 항목별 PASS/FAIL/SKIP 판정

### 5. 연동 (Python으로 실행)
```python
import asyncio, sys, os
sys.path.insert(0, os.path.expanduser("~/ai-dev-team"))
from dotenv import load_dotenv; load_dotenv(os.path.expanduser("~/ai-dev-team/.env"))

from integrations.slack.slack_notifier import notify_qa_result
from integrations.monday.monday_sync import sync_project_qa

asyncio.run(notify_qa_result("{project_name}", {passed}, "{details}"))
asyncio.run(sync_project_qa("{project_name}", {results_dict}, "{details}"))
```

### 6. 리포트 저장
`.claude/reports/qa-{project-name}-{YYYYMMDD-HHmm}.md`
```

### .claude/commands/qa-fix.md 재작성

```markdown
# /qa-fix - QA 실행 + 자동 수정

QA를 실행하고 실패 항목을 자동 수정한 뒤 재검증한다.

## 사용법
```
/qa-fix                    # 가장 최근 프로젝트
/qa-fix {project-name}     # 특정 프로젝트
```

## 절차

1. `/qa`와 동일하게 전체 QA 실행
2. 실패 항목별 자동 수정:
   - **린트 실패** → `ruff format .` / `npx eslint --fix .`
   - **타입 에러** → 에러 분석 후 코드 수정
   - **테스트 실패** → 테스트 또는 소스 코드 수정
   - **빌드 실패** → 에러 분석 후 수정
3. 수정 후 QA 재실행
4. **최대 3회 반복** (무한 루프 방지)
5. 결과를 Slack/Monday에 공유
6. 성공 시 커밋: `fix: auto-fix QA failures in {project-name}`
7. 실패 시 Monday 상태 "차단됨", 에이전트 활동 로그에 실패 기록
```

### .claude/commands/qa-report.md 재작성

```markdown
# /qa-report - QA 결과 리포트 공유

가장 최근 QA 결과를 정리하여 Slack과 Monday.com에 공유한다.

## 사용법
```
/qa-report                    # 가장 최근 QA 결과
/qa-report {project-name}     # 특정 프로젝트 QA 결과
```

## 절차

1. `.claude/reports/` 에서 가장 최근 QA 리포트 파일 읽기
2. `integrations/shared/notification_format.py`의 `format_qa_report()` 로 포맷
3. Slack 채널에 리포트 전송
4. Monday.com QA 그룹에 결과 기록 (아직 없으면)
5. 터미널에도 결과 출력
```

---

## 4. 테스트 스크립트 작성

`integrations/test_integration.py` 를 새로 생성:

```python
#!/usr/bin/env python3
"""
Slack/Monday 연동 테스트 스크립트.

실행: cd ~/ai-dev-team && python3 integrations/test_integration.py
필요: pip3 install python-dotenv httpx
"""

import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"))
except ImportError:
    print("⚠️  python-dotenv 없음. pip3 install python-dotenv httpx")


async def test_slack():
    """Slack 알림 테스트."""
    print("\n═══ Slack 테스트 ═══")
    from integrations.slack.slack_notifier import send_notification, notify_project_created, notify_qa_result

    webhook = os.getenv("SLACK_WEBHOOK_URL", "")
    channel = os.getenv("SLACK_CHANNEL", "")
    print(f"  WEBHOOK: {'✅ 설정됨' if webhook else '❌ 미설정'}")
    print(f"  CHANNEL: {channel or '❌ 미설정'}")

    if not webhook:
        print("  ⏭️  건너뜀")
        return False

    try:
        await send_notification(channel, "🧪 [테스트] Slack 연동 테스트 메시지")
        print("  ✅ 기본 알림 전송 완료")

        await notify_project_created("연동-테스트-프로젝트")
        print("  ✅ 프로젝트 생성 알림 완료")

        await notify_qa_result("연동-테스트-프로젝트", True, "lint: PASS, typecheck: PASS")
        print("  ✅ QA 결과 알림 완료")

        print("  📱 Slack 채널을 확인하세요!")
        return True
    except Exception as e:
        print(f"  ❌ 실패: {e}")
        return False


async def test_monday():
    """Monday.com 연동 테스트."""
    print("\n═══ Monday.com 테스트 ═══")
    from integrations.monday.monday_sync import (
        is_monday_enabled, initialize, create_project,
        log_qa_result, log_agent_activity, get_board_url,
    )

    print(f"  API_TOKEN: {'✅ 설정됨' if is_monday_enabled() else '❌ 미설정'}")

    if not is_monday_enabled():
        print("  ⏭️  건너뜀")
        return False

    try:
        print("  → 초기화 (보드/그룹/컬럼 확인)...")
        await initialize()
        url = get_board_url()
        print(f"  ✅ 보드 URL: {url}")

        print("  → 테스트 프로젝트 생성...")
        proj_id = await create_project(
            "연동 테스트 프로젝트",
            description="Slack/Monday 연동 테스트용",
            tech_stack=["Python", "FastAPI"],
            github_link="https://github.com/anyonecompany/ai-dev-team",
        )
        print(f"  ✅ 프로젝트 ID: {proj_id}")

        print("  → QA 결과 기록...")
        qa_id = await log_qa_result(
            "연동 테스트 프로젝트",
            lint=True, typecheck=True, tests=True, build=None,
            details="테스트용 QA 결과",
        )
        print(f"  ✅ QA ID: {qa_id}")

        print("  → 에이전트 활동 로그...")
        log_id = await log_agent_activity(
            agent="QA-DevOps",
            action="연동 테스트 실행",
            description="Slack/Monday 연동 테스트 완료",
        )
        print(f"  ✅ 활동 로그 ID: {log_id}")

        print(f"\n  📊 Monday.com 보드 확인: {url}")
        return True
    except Exception as e:
        print(f"  ❌ 실패: {e}")
        return False


async def main():
    print("╔══════════════════════════════════════╗")
    print("║   AI Dev Team 연동 테스트            ║")
    print("╚══════════════════════════════════════╝")

    slack_ok = await test_slack()
    monday_ok = await test_monday()

    print("\n═══ 결과 요약 ═══")
    print(f"  Slack:     {'✅ 성공' if slack_ok else '❌ 실패/건너뜀'}")
    print(f"  Monday:    {'✅ 성공' if monday_ok else '❌ 실패/건너뜀'}")
    print()


if __name__ == "__main__":
    asyncio.run(main())
```

---

## 5. 실행 순서

```bash
cd ~/ai-dev-team

# 1. 의존성 설치
pip3 install python-dotenv httpx

# 2. 위의 모든 파일 작성/수정 완료 후 연동 테스트
python3 integrations/test_integration.py

# 3. 테스트 성공 확인 후 커밋 + push
git add -A
git commit -m "feat: Monday.com all-in-one board + CLAUDE.md v3 + QA commands

- monday_sync.py: single board with 3 groups, 12 columns, rate limit retry
- fire-and-forget pattern, milestone/deliverables tracking
- CLAUDE.md: v3.0.0 - Claude agent team structure
- QA commands: /qa, /qa-fix, /qa-report with Slack/Monday integration
- Integration test script"
git push
```
