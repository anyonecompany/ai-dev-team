"""questions 테이블 CRUD 서비스."""

import json
import uuid
from datetime import datetime, timezone

import aiosqlite

from config import DB_PATH


async def init_db() -> None:
    """questions 테이블 및 인덱스를 생성한다."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS questions (
                id TEXT PRIMARY KEY,
                question TEXT NOT NULL,
                answer TEXT NOT NULL,
                category TEXT NOT NULL,
                confidence REAL NOT NULL DEFAULT 0.0,
                source_count INTEGER NOT NULL DEFAULT 0,
                generation_time_ms INTEGER NOT NULL DEFAULT 0,
                status TEXT NOT NULL DEFAULT 'draft',
                match_context TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)
        await db.execute(
            "CREATE INDEX IF NOT EXISTS idx_questions_status ON questions(status)"
        )
        await db.execute(
            "CREATE INDEX IF NOT EXISTS idx_questions_created_at ON questions(created_at DESC)"
        )
        await db.commit()


def _row_to_dict(row: aiosqlite.Row, columns: list[str]) -> dict:
    """DB row를 딕셔너리로 변환한다."""
    d = dict(zip(columns, row))
    if d.get("match_context"):
        d["match_context"] = json.loads(d["match_context"])
    return d


async def create_question(data: dict) -> dict:
    """질문/답변 레코드를 생성한다."""
    now = datetime.now(timezone.utc).isoformat()
    question_id = str(uuid.uuid4())
    match_ctx = json.dumps(data.get("match_context")) if data.get("match_context") else None

    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """INSERT INTO questions
               (id, question, answer, category, confidence, source_count,
                generation_time_ms, status, match_context, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, 'draft', ?, ?, ?)""",
            (
                question_id,
                data["question"],
                data["answer"],
                data["category"],
                data["confidence"],
                data["source_count"],
                data["generation_time_ms"],
                match_ctx,
                now,
                now,
            ),
        )
        await db.commit()

    return {
        "id": question_id,
        "question": data["question"],
        "answer": data["answer"],
        "category": data["category"],
        "confidence": data["confidence"],
        "source_count": data["source_count"],
        "generation_time_ms": data["generation_time_ms"],
        "status": "draft",
    }


async def get_questions(
    status: str | None = None,
    limit: int = 20,
    offset: int = 0,
) -> tuple[list[dict], int]:
    """질문 목록을 조회한다."""
    columns = [
        "id", "question", "answer", "category", "confidence",
        "source_count", "generation_time_ms", "status",
        "match_context", "created_at", "updated_at",
    ]

    where = ""
    params: list = []
    if status:
        where = "WHERE status = ?"
        params.append(status)

    async with aiosqlite.connect(DB_PATH) as db:
        # 전체 개수
        count_row = await db.execute_fetchall(
            f"SELECT COUNT(*) FROM questions {where}", params
        )
        total = count_row[0][0]

        # 목록 조회
        rows = await db.execute_fetchall(
            f"""SELECT {', '.join(columns)} FROM questions
                {where} ORDER BY created_at DESC LIMIT ? OFFSET ?""",
            [*params, limit, offset],
        )

    questions = [_row_to_dict(row, columns) for row in rows]
    return questions, total


async def update_status(question_id: str, status: str) -> dict | None:
    """질문 상태를 변경한다."""
    now = datetime.now(timezone.utc).isoformat()

    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "UPDATE questions SET status = ?, updated_at = ? WHERE id = ?",
            (status, now, question_id),
        )
        await db.commit()
        if cursor.rowcount == 0:
            return None

    return {"id": question_id, "status": status, "updated_at": now}


async def get_question_by_id(question_id: str) -> dict | None:
    """ID로 질문을 조회한다."""
    columns = [
        "id", "question", "answer", "category", "confidence",
        "source_count", "generation_time_ms", "status",
        "match_context", "created_at", "updated_at",
    ]

    async with aiosqlite.connect(DB_PATH) as db:
        rows = await db.execute_fetchall(
            f"SELECT {', '.join(columns)} FROM questions WHERE id = ?",
            (question_id,),
        )

    if not rows:
        return None
    return _row_to_dict(rows[0], columns)
