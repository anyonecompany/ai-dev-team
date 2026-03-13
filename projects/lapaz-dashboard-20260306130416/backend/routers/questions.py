"""GET /api/questions, PATCH /api/questions/{id}/status 라우터."""

from fastapi import APIRouter, HTTPException, Query

from models.schemas import (
    QuestionsListResponse,
    QuestionResponse,
    StatusUpdateRequest,
    StatusUpdateResponse,
)
from services import question_service

router = APIRouter()


@router.get("/questions", response_model=QuestionsListResponse)
async def list_questions(
    status: str | None = Query(None),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
) -> QuestionsListResponse:
    """질문 목록을 조회한다."""
    questions, total = await question_service.get_questions(status, limit, offset)
    return QuestionsListResponse(
        questions=[QuestionResponse(**q) for q in questions],
        total=total,
    )


@router.patch("/questions/{question_id}/status", response_model=StatusUpdateResponse)
async def update_question_status(
    question_id: str,
    req: StatusUpdateRequest,
) -> StatusUpdateResponse:
    """질문 상태를 변경한다."""
    result = await question_service.update_status(question_id, req.status)
    if result is None:
        raise HTTPException(status_code=404, detail="해당 질문을 찾을 수 없습니다.")
    return StatusUpdateResponse(**result)
