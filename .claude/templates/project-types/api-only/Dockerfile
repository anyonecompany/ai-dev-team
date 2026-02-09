# __PROJECT_NAME__ Backend Dockerfile
# 멀티스테이지 빌드로 이미지 크기 최적화

# ============================================
# 빌드 스테이지
# ============================================
FROM python:3.11-slim as builder

WORKDIR /app

# 시스템 의존성 설치
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Python 의존성 설치
COPY backend/requirements.txt .
RUN pip wheel --no-cache-dir --no-deps --wheel-dir /app/wheels -r requirements.txt

# ============================================
# 실행 스테이지
# ============================================
FROM python:3.11-slim

WORKDIR /app

# 보안: non-root 사용자
RUN adduser --disabled-password --gecos "" appuser

# 빌드 결과물 복사
COPY --from=builder /app/wheels /wheels
COPY --from=builder /app/requirements.txt .

# 의존성 설치
RUN pip install --no-cache /wheels/*

# 애플리케이션 코드 복사
COPY backend/ .

# 권한 설정
RUN chown -R appuser:appuser /app
USER appuser

# 환경변수
ENV HOST=0.0.0.0
ENV PORT=8000
ENV DEBUG=false

# 헬스체크
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import httpx; httpx.get('http://localhost:8000/health')" || exit 1

# 실행
EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
