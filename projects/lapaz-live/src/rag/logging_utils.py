"""구조화 JSON 로깅 유틸리티.

파이프라인 전체에서 일관된 JSON 로그를 출력한다.
필수 필드: timestamp, request_id, pipeline_stage, event, latency_ms, error_type, provider.
"""

import json
import logging
import time
import uuid
from datetime import datetime, timezone
from typing import Any


class JSONFormatter(logging.Formatter):
    """로그 레코드를 JSON 한 줄로 포맷한다."""

    def format(self, record: logging.LogRecord) -> str:
        """로그 레코드를 JSON 문자열로 변환한다."""
        log_entry: dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # 구조화 필드가 extra에 있으면 병합
        for key in (
            "request_id", "pipeline_stage", "event", "latency_ms",
            "error_type", "provider", "category", "confidence",
            "search_method", "doc_count", "top_similarity",
            "status_code", "attempt", "source", "source_count",
            "cached",
        ):
            value = getattr(record, key, None)
            if value is not None:
                log_entry[key] = value

        # exc_info 처리
        if record.exc_info and record.exc_info[1]:
            log_entry["error_type"] = log_entry.get(
                "error_type", type(record.exc_info[1]).__name__
            )
            log_entry["error_detail"] = str(record.exc_info[1])

        return json.dumps(log_entry, ensure_ascii=False, default=str)


def setup_json_logging() -> None:
    """루트 로거에 JSON 포맷터를 설정한다.

    이미 JSONFormatter가 적용되어 있으면 중복 설정하지 않는다.
    """
    root_logger = logging.getLogger()

    # 중복 방지
    for handler in root_logger.handlers:
        if isinstance(handler.formatter, JSONFormatter):
            return

    handler = logging.StreamHandler()
    handler.setFormatter(JSONFormatter())

    root_logger.handlers.clear()
    root_logger.addHandler(handler)
    root_logger.setLevel(logging.INFO)


def generate_request_id() -> str:
    """요청별 고유 ID를 생성한다."""
    return uuid.uuid4().hex[:12]


class PipelineLogger:
    """파이프라인 단계별 구조화 로깅을 제공한다.

    request_id를 바인딩하여 모든 로그에 자동 포함한다.
    """

    def __init__(self, request_id: str, logger_name: str = "rag.pipeline") -> None:
        self._request_id = request_id
        self._logger = logging.getLogger(logger_name)

    @property
    def request_id(self) -> str:
        """바인딩된 request_id를 반환한다."""
        return self._request_id

    def _log(
        self,
        level: int,
        message: str,
        *,
        pipeline_stage: str = "",
        event: str = "",
        latency_ms: int | None = None,
        error_type: str | None = None,
        provider: str | None = None,
        exc_info: bool = False,
        **extra: Any,
    ) -> None:
        """구조화 필드를 포함한 로그를 출력한다."""
        fields: dict[str, Any] = {
            "request_id": self._request_id,
            "pipeline_stage": pipeline_stage,
            "event": event,
        }
        if latency_ms is not None:
            fields["latency_ms"] = latency_ms
        if error_type is not None:
            fields["error_type"] = error_type
        if provider is not None:
            fields["provider"] = provider
        fields.update(extra)

        self._logger.log(level, message, extra=fields, exc_info=exc_info)

    def stage_start(self, stage: str, **extra: Any) -> float:
        """단계 시작을 로깅하고 시작 시각을 반환한다."""
        self._log(logging.INFO, f"{stage} 시작", pipeline_stage=stage, event="start", **extra)
        return time.monotonic()

    def stage_done(self, stage: str, start: float, **extra: Any) -> None:
        """단계 완료를 로깅한다."""
        latency = int((time.monotonic() - start) * 1000)
        self._log(
            logging.INFO, f"{stage} 완료 ({latency}ms)",
            pipeline_stage=stage, event="done", latency_ms=latency, **extra,
        )

    def stage_error(self, stage: str, start: float, error: Exception, **extra: Any) -> None:
        """단계 실패를 로깅한다."""
        latency = int((time.monotonic() - start) * 1000)
        self._log(
            logging.ERROR, f"{stage} 실패: {error}",
            pipeline_stage=stage, event="error", latency_ms=latency,
            error_type=type(error).__name__, exc_info=True, **extra,
        )

    def info(self, message: str, *, pipeline_stage: str = "", event: str = "", **extra: Any) -> None:
        """INFO 레벨 구조화 로그."""
        self._log(logging.INFO, message, pipeline_stage=pipeline_stage, event=event, **extra)

    def warning(self, message: str, *, pipeline_stage: str = "", event: str = "", **extra: Any) -> None:
        """WARNING 레벨 구조화 로그."""
        self._log(logging.WARNING, message, pipeline_stage=pipeline_stage, event=event, **extra)

    def error(self, message: str, *, pipeline_stage: str = "", event: str = "", exc_info: bool = False, **extra: Any) -> None:
        """ERROR 레벨 구조화 로그."""
        self._log(logging.ERROR, message, pipeline_stage=pipeline_stage, event=event, exc_info=exc_info, **extra)
