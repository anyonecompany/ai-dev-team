"""La Paz — 공유 설정, Supabase 클라이언트, 에이전트 IPC."""

from __future__ import annotations

import json
import logging
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

# ── 경로 ────────────────────────────────────────
PROJECT_ROOT = Path(__file__).parent.parent
load_dotenv(PROJECT_ROOT / ".env")

DATA_RAW = PROJECT_ROOT / "data" / "raw"
DATA_PROCESSED = PROJECT_ROOT / "data" / "processed"
VECTORSTORE_DIR = PROJECT_ROOT / "ai" / "vectorstore"
LOGS_DIR = PROJECT_ROOT / "logs"
EVALUATION_DIR = PROJECT_ROOT / "evaluation"
AGENT_STATUS_DIR = LOGS_DIR / "status"

for _d in [DATA_RAW, DATA_PROCESSED, VECTORSTORE_DIR, LOGS_DIR, EVALUATION_DIR, AGENT_STATUS_DIR]:
    _d.mkdir(parents=True, exist_ok=True)

# ── 환경변수 ────────────────────────────────────
SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_SERVICE_KEY = os.environ.get("SUPABASE_SERVICE_KEY", "")
DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY", "")
GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY", "")
FOOTBALL_DATA_TOKEN = os.environ.get("FOOTBALL_DATA_TOKEN", "")
API_FOOTBALL_KEY = os.environ.get("API_FOOTBALL_KEY", "")


# ── Supabase 클라이언트 ─────────────────────────
def get_supabase():
    """Service-role Supabase 클라이언트."""
    from supabase import create_client

    if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
        raise RuntimeError("SUPABASE_URL / SUPABASE_SERVICE_KEY 환경변수 필요")
    return create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)


# ── Supabase 헬퍼 ──────────────────────────────
def sb_upsert(table: str, rows: list[dict], on_conflict: str = "id") -> int:
    """Supabase upsert. 삽입된 행 수 반환."""
    if not rows:
        return 0
    sb = get_supabase()
    resp = sb.table(table).upsert(rows, on_conflict=on_conflict).execute()
    return len(resp.data) if resp.data else 0


def sb_insert(table: str, rows: list[dict]) -> int:
    """Supabase insert (중복 시 무시)."""
    if not rows:
        return 0
    sb = get_supabase()
    try:
        resp = sb.table(table).insert(rows).execute()
        return len(resp.data) if resp.data else 0
    except Exception:
        # 중복 키 등 → 개별 삽입
        count = 0
        for row in rows:
            try:
                sb.table(table).insert(row).execute()
                count += 1
            except Exception:
                pass
        return count


def sb_select(table: str, columns: str = "*", filters: dict | None = None,
              limit: int = 1000) -> list[dict]:
    """Supabase select with auto-pagination.

    PostgREST는 한 번에 최대 1000행만 반환하므로 .range()로 페이징한다.
    limit=0 이면 전체 행을 가져온다.
    """
    sb = get_supabase()
    PAGE = 1000
    target = limit if limit > 0 else float("inf")
    all_rows: list[dict] = []
    offset = 0

    while len(all_rows) < target:
        end = offset + PAGE - 1
        q = sb.table(table).select(columns).range(offset, end)
        if filters:
            for col, val in filters.items():
                q = q.eq(col, val)
        resp = q.execute()
        rows = resp.data or []
        all_rows.extend(rows)
        if len(rows) < PAGE:
            break  # 마지막 페이지
        offset += PAGE

    return all_rows[:limit] if limit > 0 else all_rows


def sb_rpc(fn_name: str, params: dict | None = None) -> Any:
    """Supabase RPC 호출."""
    sb = get_supabase()
    resp = sb.rpc(fn_name, params or {}).execute()
    return resp.data


# ── 로깅 ────────────────────────────────────────
def get_agent_logger(agent_name: str) -> logging.Logger:
    """에이전트별 로거. LOG_LEVEL 환경변수로 레벨 조정 (기본 INFO)."""
    logger = logging.getLogger(agent_name)
    level = os.environ.get("LOG_LEVEL", "INFO").upper()
    logger.setLevel(getattr(logging, level, logging.INFO))
    if not logger.handlers:
        fmt = logging.Formatter(
            f"[%(asctime)s] [{agent_name}] %(levelname)s: %(message)s",
            datefmt="%H:%M:%S",
        )
        fh = logging.FileHandler(LOGS_DIR / f"{agent_name}.log", encoding="utf-8")
        fh.setFormatter(fmt)
        ch = logging.StreamHandler(sys.stdout)
        ch.setFormatter(fmt)
        logger.addHandler(fh)
        logger.addHandler(ch)
    return logger


# ── 에이전트 IPC ────────────────────────────────
def publish_status(agent_name: str, status: str, detail: str = "") -> None:
    """에이전트 상태를 JSON 파일 + Supabase agent_status 에 동기화."""
    now = datetime.now(timezone.utc).isoformat()
    payload = {"agent": agent_name, "status": status, "detail": detail, "timestamp": now}
    # 로컬 JSON
    (AGENT_STATUS_DIR / f"{agent_name}.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2)
    )
    # Supabase
    try:
        sb = get_supabase()
        row = {
            "agent_name": agent_name,
            "status": status,
            "detail": detail[:500] if detail else "",
            "updated_at": now,
        }
        if status == "running":
            row["started_at"] = now
        if status == "completed":
            row["completed_at"] = now
        sb.table("agent_status").upsert(row, on_conflict="agent_name").execute()
    except Exception:
        pass  # Supabase 실패해도 로컬 IPC 유지


def read_status(agent_name: str) -> dict:
    """다른 에이전트 상태 읽기 (로컬 JSON)."""
    f = AGENT_STATUS_DIR / f"{agent_name}.json"
    if f.exists():
        return json.loads(f.read_text())
    return {"status": "not_started"}


def wait_for_agent(agent_name: str, target: str, timeout: int = 900) -> bool:
    """특정 에이전트가 목표 상태에 도달할 때까지 대기."""
    start = time.time()
    while time.time() - start < timeout:
        if read_status(agent_name).get("status") == target:
            return True
        time.sleep(5)
    return False


# ── 팬 행동 추적 ────────────────────────────────
def track_fan_event(
    event_type: str,
    user_id: str | None = None,
    session_id: str | None = None,
    entity_type: str | None = None,
    entity_id: str | None = None,
    payload: dict | None = None,
) -> None:
    """fan_events 테이블에 행동 로그 기록."""
    try:
        sb = get_supabase()
        sb.table("fan_events").insert({
            "user_id": user_id,
            "session_id": session_id,
            "event_type": event_type,
            "entity_type": entity_type,
            "entity_id": entity_id,
            "payload": payload or {},
        }).execute()
    except Exception:
        pass  # 트래킹 실패가 서비스 중단으로 이어지면 안 됨
