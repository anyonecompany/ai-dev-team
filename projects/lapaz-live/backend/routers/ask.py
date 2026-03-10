"""POST /api/ask — RAG 질문 처리 라우터 (일반 + SSE 스트리밍)."""

import json
import logging

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

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


@router.post("/ask/stream")
async def ask_question_stream(req: AskRequest) -> StreamingResponse:
    """SSE 스트리밍으로 답변을 실시간 전송한다.

    클라이언트는 EventSource 또는 fetch + ReadableStream으로 수신.
    각 이벤트: data: {"type": "metadata"|"chunk"|"answer"|"done", ...}
    """
    match_ctx = req.match_context.model_dump() if req.match_context else None
    ctx_str = json.dumps(match_ctx, ensure_ascii=False) if match_ctx else ""

    async def event_generator():
        try:
            async for chunk_json in rag_service.generate_answer_stream(
                req.question, ctx_str
            ):
                yield f"data: {chunk_json}\n\n"
        except Exception:
            logger.exception("스트리밍 RAG 파이프라인 오류")
            yield f"data: {json.dumps({'type': 'error', 'message': '답변 생성 중 오류가 발생했습니다.'}, ensure_ascii=False)}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
