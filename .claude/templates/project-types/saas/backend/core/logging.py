"""구조화 로깅 설정 (structlog 기반).

JSON 형식의 구조화된 로그를 출력합니다.
"""

import logging
import sys

import structlog
from structlog.types import Processor

from core.config import settings


def setup_logging() -> None:
    """structlog 및 표준 로깅 설정."""

    # 로그 레벨 설정
    log_level = logging.DEBUG if settings.DEBUG else logging.INFO

    # structlog 프로세서 체인
    shared_processors: list[Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.StackInfoRenderer(),
        structlog.dev.set_exc_info,
        structlog.processors.TimeStamper(fmt="iso"),
    ]

    if settings.DEBUG:
        # 개발 환경: 컬러풀한 콘솔 출력
        structlog.configure(
            processors=shared_processors + [
                structlog.dev.ConsoleRenderer(colors=True)
            ],
            wrapper_class=structlog.make_filtering_bound_logger(log_level),
            context_class=dict,
            logger_factory=structlog.PrintLoggerFactory(),
            cache_logger_on_first_use=True,
        )
    else:
        # 프로덕션: JSON 출력
        structlog.configure(
            processors=shared_processors + [
                structlog.processors.dict_tracebacks,
                structlog.processors.JSONRenderer(ensure_ascii=False),
            ],
            wrapper_class=structlog.make_filtering_bound_logger(log_level),
            context_class=dict,
            logger_factory=structlog.PrintLoggerFactory(),
            cache_logger_on_first_use=True,
        )

    # 표준 logging도 structlog로 라우팅
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=log_level,
    )

    # uvicorn 로거 레벨 조정
    logging.getLogger("uvicorn").setLevel(log_level)
    logging.getLogger("uvicorn.error").setLevel(log_level)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)


def get_logger(name: str = None) -> structlog.BoundLogger:
    """로거 인스턴스 반환.

    Args:
        name: 로거 이름 (모듈명 등)

    Returns:
        structlog BoundLogger
    """
    logger = structlog.get_logger()
    if name:
        logger = logger.bind(logger_name=name)
    return logger
