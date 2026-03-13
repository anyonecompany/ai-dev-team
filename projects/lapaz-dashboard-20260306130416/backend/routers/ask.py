"""POST /api/ask — RAG 질문 처리 라우터."""

import logging

from fastapi import APIRouter, HTTPException

from models.schemas import AskRequest, AskResponse
from services import question_service, rag_service

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/ask", response_model=AskResponse, status_code=201)
async def ask_question(req: AskRequest) -> AskResponse:
    """팬 질문에 대한 답변을 생성하고 DB에 저장한다."""
    match_ctx = req.match_context.model_dump() if req.match_context else None

    try:
        rag_result = await rag_service.generate_answer(req.question, match_ctx)
    except Exception:
        logger.exception("RAG 파이프라인 오류")
        raise HTTPException(status_code=500, detail="답변 생성 중 오류가 발생했습니다.")

    # DB 저장
    record = await question_service.create_question({
        **rag_result,
        "match_context": match_ctx,
    })

    return AskResponse(**record)
