"""POST /api/ask — RAG 질문 처리 라우터 (일반 + SSE 스트리밍)."""

import json
import logging
import time

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from models.schemas import AskRequest, AskResponse
from services import question_service, rag_service
from services.error_log_service import log_error, resolve_error_type

from rag.exceptions import RateLimitError, PipelineTimeoutError, DataSourceError, GenerationError
from rag.logging_utils import PipelineLogger, generate_request_id

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/ask", response_model=AskResponse, status_code=201)
async def ask_question(req: AskRequest) -> AskResponse:
    """팬 질문에 대한 답변을 생성하고 DB에 저장한다."""
    request_id = generate_request_id()
    plog = PipelineLogger(request_id, "rag.router")
    match_ctx = req.match_context.model_dump() if req.match_context else None

    # 대화 히스토리 정제: None→[], 6개 초과→최근 6개
    history = req.history or []
    if len(history) > 6:
        history = history[-6:]

    start = time.monotonic()
    plog.info(
        "요청 수신",
        pipeline_stage="router", event="request_received",
        question=req.question[:80],
        force_football=req.force_football,
    )

    try:
        rag_result = await rag_service.generate_answer(req.question, match_ctx, request_id=request_id, force_football=req.force_football, history=history)
    except RateLimitError as exc:
        latency = int((time.monotonic() - start) * 1000)
        plog.error(
            "LLM API 요청 제한 초과",
            pipeline_stage="router", event="request_error",
            error_type="RateLimitError", latency_ms=latency,
            exc_info=True,
        )
        await log_error(
            request_id=request_id, question=req.question,
            error_type="rate_limit", pipeline_stage="router",
            error_message=str(exc), latency_ms=latency,
            match_id=match_ctx.get("match_id") if match_ctx else None,
        )
        raise HTTPException(status_code=429, detail="현재 요청이 많습니다. 10초 후 다시 질문해주세요.")
    except PipelineTimeoutError as exc:
        latency = int((time.monotonic() - start) * 1000)
        plog.error(
            "외부 API 타임아웃",
            pipeline_stage="router", event="request_error",
            error_type="PipelineTimeoutError", latency_ms=latency,
            exc_info=True,
        )
        await log_error(
            request_id=request_id, question=req.question,
            error_type="timeout", pipeline_stage="router",
            error_message=str(exc), latency_ms=latency,
            match_id=match_ctx.get("match_id") if match_ctx else None,
        )
        raise HTTPException(status_code=504, detail="데이터를 불러오는 데 시간이 걸리고 있습니다. 다시 시도해주세요.")
    except DataSourceError as exc:
        latency = int((time.monotonic() - start) * 1000)
        plog.error(
            "데이터 소스 연결 실패",
            pipeline_stage="router", event="request_error",
            error_type="DataSourceError", latency_ms=latency,
            exc_info=True,
        )
        await log_error(
            request_id=request_id, question=req.question,
            error_type="data_source", pipeline_stage="router",
            error_message=str(exc), latency_ms=latency,
            match_id=match_ctx.get("match_id") if match_ctx else None,
        )
        raise HTTPException(status_code=503, detail="현재 일부 데이터를 불러올 수 없습니다.")
    except Exception as exc:
        latency = int((time.monotonic() - start) * 1000)
        plog.error(
            "RAG 파이프라인 오류",
            pipeline_stage="router", event="request_error",
            error_type=type(exc).__name__, latency_ms=latency,
            exc_info=True,
        )
        await log_error(
            request_id=request_id, question=req.question,
            error_type=resolve_error_type(exc), pipeline_stage="router",
            error_message=str(exc), latency_ms=latency,
            match_id=match_ctx.get("match_id") if match_ctx else None,
        )
        raise HTTPException(status_code=500, detail="일시적인 오류가 발생했습니다. 다시 시도해주세요.")

    # DB 저장
    record = await question_service.create_question({
        **rag_result,
        "match_context": match_ctx,
    })

    latency = int((time.monotonic() - start) * 1000)
    plog.info(
        "요청 완료",
        pipeline_stage="router", event="request_done",
        latency_ms=latency,
        category=rag_result.get("category", ""),
    )

    return AskResponse(**record)


@router.post("/ask/stream")
async def ask_question_stream(req: AskRequest) -> StreamingResponse:
    """SSE 스트리밍으로 답변을 실시간 전송한다.

    클라이언트는 EventSource 또는 fetch + ReadableStream으로 수신.
    각 이벤트: data: {"type": "metadata"|"chunk"|"answer"|"done", ...}
    """
    request_id = generate_request_id()
    plog = PipelineLogger(request_id, "rag.router")
    match_ctx = req.match_context.model_dump() if req.match_context else None
    ctx_str = json.dumps(match_ctx, ensure_ascii=False) if match_ctx else ""

    # 대화 히스토리 정제: None→[], 6개 초과→최근 6개
    history = req.history or []
    if len(history) > 6:
        history = history[-6:]

    start = time.monotonic()
    plog.info(
        "스트리밍 요청 수신",
        pipeline_stage="router", event="stream_request_received",
        question=req.question[:80],
        force_football=req.force_football,
    )

    async def event_generator():
        metadata: dict = {}
        answer_parts: list[str] = []
        try:
            async for chunk_json in rag_service.generate_answer_stream(
                req.question, ctx_str, request_id=request_id, force_football=req.force_football, history=history
            ):
                event = json.loads(chunk_json)
                event_type = event.get("type")

                if event_type == "metadata":
                    metadata = event
                elif event_type in {"chunk", "answer"}:
                    text = event.get("text") or ""
                    if text:
                        answer_parts.append(text)
                elif event_type == "done":
                    cleaned_answer = event.get("cleaned_answer") or "".join(answer_parts).strip()
                    record = await question_service.create_question({
                        "question": req.question,
                        "answer": cleaned_answer,
                        "category": metadata.get("category", "match_flow"),
                        "confidence": metadata.get("confidence", 0.0),
                        "source_count": event.get("source_count", 0),
                        "generation_time_ms": event.get("generation_time_ms", 0),
                        "total_time_ms": event.get("total_time_ms", 0),
                        "match_context": match_ctx,
                    })
                    event = {
                        **event,
                        "id": record["id"],
                        "status": record["status"],
                    }

                    latency = int((time.monotonic() - start) * 1000)
                    plog.info(
                        "스트리밍 요청 완료",
                        pipeline_stage="router", event="stream_request_done",
                        latency_ms=latency,
                        category=metadata.get("category", ""),
                    )

                yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"
        except RateLimitError as exc:
            latency = int((time.monotonic() - start) * 1000)
            plog.error(
                "스트리밍 LLM API 요청 제한 초과",
                pipeline_stage="router", event="stream_request_error",
                error_type="RateLimitError", latency_ms=latency,
                exc_info=True,
            )
            await log_error(
                request_id=request_id, question=req.question,
                error_type="rate_limit", pipeline_stage="router",
                error_message=str(exc), latency_ms=latency,
                match_id=match_ctx.get("match_id") if match_ctx else None,
            )
            yield f"data: {json.dumps({'type': 'error', 'error_type': 'rate_limit', 'message': '현재 요청이 많습니다. 10초 후 다시 질문해주세요.'}, ensure_ascii=False)}\n\n"
        except PipelineTimeoutError as exc:
            latency = int((time.monotonic() - start) * 1000)
            plog.error(
                "스트리밍 외부 API 타임아웃",
                pipeline_stage="router", event="stream_request_error",
                error_type="PipelineTimeoutError", latency_ms=latency,
                exc_info=True,
            )
            await log_error(
                request_id=request_id, question=req.question,
                error_type="timeout", pipeline_stage="router",
                error_message=str(exc), latency_ms=latency,
                match_id=match_ctx.get("match_id") if match_ctx else None,
            )
            yield f"data: {json.dumps({'type': 'error', 'error_type': 'timeout', 'message': '데이터를 불러오는 데 시간이 걸리고 있습니다. 다시 시도해주세요.'}, ensure_ascii=False)}\n\n"
        except DataSourceError as exc:
            latency = int((time.monotonic() - start) * 1000)
            plog.error(
                "스트리밍 데이터 소스 연결 실패",
                pipeline_stage="router", event="stream_request_error",
                error_type="DataSourceError", latency_ms=latency,
                exc_info=True,
            )
            await log_error(
                request_id=request_id, question=req.question,
                error_type="data_source", pipeline_stage="router",
                error_message=str(exc), latency_ms=latency,
                match_id=match_ctx.get("match_id") if match_ctx else None,
            )
            yield f"data: {json.dumps({'type': 'error', 'error_type': 'data_source', 'message': '현재 일부 데이터를 불러올 수 없습니다.'}, ensure_ascii=False)}\n\n"
        except Exception as exc:
            latency = int((time.monotonic() - start) * 1000)
            plog.error(
                "스트리밍 RAG 파이프라인 오류",
                pipeline_stage="router", event="stream_request_error",
                error_type=type(exc).__name__, latency_ms=latency,
                exc_info=True,
            )
            await log_error(
                request_id=request_id, question=req.question,
                error_type=resolve_error_type(exc), pipeline_stage="router",
                error_message=str(exc), latency_ms=latency,
                match_id=match_ctx.get("match_id") if match_ctx else None,
            )
            yield f"data: {json.dumps({'type': 'error', 'error_type': 'unknown', 'message': '일시적인 오류가 발생했습니다. 다시 시도해주세요.'}, ensure_ascii=False)}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
