# FastAPI Error Handling & Logging Pattern

> 카테고리: Backend / FastAPI
> 출처: dashboard/backend/main.py, core/logging.py
> 최종 갱신: 2026-02-03

## 개요

structlog 기반 구조화 로깅과 요청/응답 미들웨어를 사용한 에러 처리 패턴.
개발/프로덕션 환경별 로그 포맷 자동 전환을 지원합니다.

## 구현

### 1. 로깅 설정 (core/logging.py)

```python
"""구조화 로깅 설정 (structlog 기반)."""

import logging
import sys
from typing import Any, Dict

import structlog
from structlog.types import Processor

from core.config import settings


def setup_logging() -> None:
    """structlog 및 표준 로깅 설정."""
    log_level = logging.DEBUG if settings.DEBUG else logging.INFO

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

    # uvicorn 로거 레벨 조정
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)


def get_logger(name: str = None) -> structlog.BoundLogger:
    """로거 인스턴스 반환."""
    logger = structlog.get_logger()
    if name:
        logger = logger.bind(logger_name=name)
    return logger
```

### 2. 요청 로깅 미들웨어 (main.py)

```python
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import Request

class LoggingMiddleware(BaseHTTPMiddleware):
    """요청/응답 로깅 미들웨어."""

    async def dispatch(self, request: Request, call_next):
        import time
        import uuid
        from structlog.contextvars import clear_contextvars, bind_contextvars

        # 컨텍스트 초기화 및 바인딩
        clear_contextvars()
        request_id = str(uuid.uuid4())[:8]
        bind_contextvars(request_id=request_id)

        req_logger = get_logger("request")

        # 헬스체크는 로깅 생략
        if request.url.path in ["/health", "/", "/docs", "/openapi.json"]:
            return await call_next(request)

        start_time = time.time()
        req_logger.info(
            "요청 수신",
            method=request.method,
            path=request.url.path,
        )

        try:
            response = await call_next(request)
            duration_ms = (time.time() - start_time) * 1000

            req_logger.info(
                "응답 완료",
                status=response.status_code,
                duration_ms=round(duration_ms, 2),
            )
            return response

        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            req_logger.exception(
                "요청 처리 실패",
                error=str(e),
                duration_ms=round(duration_ms, 2),
            )
            raise


app.add_middleware(LoggingMiddleware)
```

## 로그 출력 예시

### 개발 환경 (DEBUG=true)
```
2026-02-03T10:00:00 [info     ] 요청 수신               method=GET path=/api/tasks request_id=a1b2c3d4
2026-02-03T10:00:00 [info     ] 응답 완료               status=200 duration_ms=45.23 request_id=a1b2c3d4
```

### 프로덕션 환경 (DEBUG=false)
```json
{"event":"요청 수신","method":"GET","path":"/api/tasks","request_id":"a1b2c3d4","timestamp":"2026-02-03T10:00:00"}
```

## 장점

1. **구조화된 로그**: JSON 형식으로 파싱/분석 용이
2. **요청 추적**: request_id로 전체 요청 흐름 추적 가능
3. **환경별 포맷**: 개발/프로덕션 자동 전환
4. **성능 측정**: duration_ms로 응답 시간 자동 기록
5. **노이즈 감소**: 헬스체크 등 불필요한 로그 필터링

## 의존성

```txt
structlog>=24.0.0
```

## 관련 패턴

- [config.py - 환경 설정](#)
- [dependencies.py - 의존성 주입](#)
