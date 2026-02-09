#!/bin/bash
#
# 배포 설정 스크립트
# 버전: 1.0.0
#
# 사용법:
#   bash .claude/scripts/deploy-setup.sh [프로젝트경로] [배포대상]
#
# 배포대상:
#   railway - Backend를 Railway에 배포
#   vercel  - Frontend를 Vercel에 배포
#   flyio   - Backend를 Fly.io에 배포
#   all     - Backend(Railway) + Frontend(Vercel) 모두
#
# 예시:
#   bash .claude/scripts/deploy-setup.sh ./projects/my-app all
#   bash .claude/scripts/deploy-setup.sh . railway
#

set -e

# =============================================================================
# 설정
# =============================================================================
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
TEMPLATES_DIR="$(dirname "$SCRIPT_DIR")/templates/deploy"

# 색상
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

# =============================================================================
# 입력 검증
# =============================================================================
if [ $# -lt 2 ]; then
    echo -e "${RED}사용법: $0 [프로젝트경로] [배포대상]${NC}"
    echo ""
    echo -e "${CYAN}배포대상:${NC}"
    echo "  railway - Backend를 Railway에 배포"
    echo "  vercel  - Frontend를 Vercel에 배포"
    echo "  flyio   - Backend를 Fly.io에 배포"
    echo "  all     - Backend(Railway) + Frontend(Vercel) 모두"
    echo ""
    echo -e "${CYAN}예시:${NC}"
    echo "  $0 ./projects/my-app all"
    exit 1
fi

PROJECT_PATH="$1"
DEPLOY_TARGET="$2"

# 프로젝트 경로 검증
if [ ! -d "$PROJECT_PATH" ]; then
    echo -e "${RED}프로젝트 디렉토리를 찾을 수 없습니다: $PROJECT_PATH${NC}"
    exit 1
fi

# 배포 대상 검증
if [[ ! "$DEPLOY_TARGET" =~ ^(railway|vercel|flyio|all)$ ]]; then
    echo -e "${RED}지원하지 않는 배포 대상: $DEPLOY_TARGET${NC}"
    echo -e "${CYAN}지원 대상: railway, vercel, flyio, all${NC}"
    exit 1
fi

# 절대 경로로 변환
PROJECT_PATH="$(cd "$PROJECT_PATH" && pwd)"

echo -e "${CYAN}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  배포 설정 스크립트"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -e "${NC}"
echo -e "프로젝트: ${GREEN}$PROJECT_PATH${NC}"
echo -e "배포 대상: ${GREEN}$DEPLOY_TARGET${NC}"
echo ""

# =============================================================================
# 프로젝트 유형 감지
# =============================================================================
detect_project_type() {
    local has_backend=false
    local has_frontend=false

    if [ -d "$PROJECT_PATH/backend" ] && [ -f "$PROJECT_PATH/backend/main.py" ]; then
        has_backend=true
    fi

    if [ -d "$PROJECT_PATH/frontend" ] && [ -f "$PROJECT_PATH/frontend/package.json" ]; then
        has_frontend=true
    fi

    if [ "$has_backend" = true ] && [ "$has_frontend" = true ]; then
        echo "fullstack"
    elif [ "$has_backend" = true ]; then
        echo "api-only"
    elif [ "$has_frontend" = true ]; then
        echo "frontend-only"
    else
        echo "unknown"
    fi
}

PROJECT_TYPE=$(detect_project_type)
echo -e "프로젝트 유형: ${GREEN}$PROJECT_TYPE${NC}"
echo ""

if [ "$PROJECT_TYPE" = "unknown" ]; then
    echo -e "${RED}프로젝트 유형을 감지할 수 없습니다.${NC}"
    echo -e "${YELLOW}backend/main.py 또는 frontend/package.json이 필요합니다.${NC}"
    exit 1
fi

# =============================================================================
# GitHub Actions 워크플로우 설정
# =============================================================================
setup_github_workflows() {
    echo -e "${YELLOW}[1/4] GitHub Actions 워크플로우 설정 중...${NC}"

    mkdir -p "$PROJECT_PATH/.github/workflows"

    # Backend 워크플로우
    if [[ "$DEPLOY_TARGET" =~ ^(railway|flyio|all)$ ]]; then
        if [[ "$PROJECT_TYPE" =~ ^(api-only|fullstack)$ ]]; then
            cp "$TEMPLATES_DIR/github-actions-fastapi.yml" "$PROJECT_PATH/.github/workflows/backend.yml"

            # Fly.io 선택 시 주석 조정
            if [ "$DEPLOY_TARGET" = "flyio" ]; then
                # Railway 주석 처리, Fly.io 주석 해제
                sed -i '' 's/deploy-railway:/# deploy-railway:/' "$PROJECT_PATH/.github/workflows/backend.yml" 2>/dev/null || true
                sed -i '' 's/# deploy-flyio:/deploy-flyio:/' "$PROJECT_PATH/.github/workflows/backend.yml" 2>/dev/null || true
            fi

            echo -e "${GREEN}  ✓ backend.yml 생성됨${NC}"
        fi
    fi

    # Frontend 워크플로우
    if [[ "$DEPLOY_TARGET" =~ ^(vercel|all)$ ]]; then
        if [[ "$PROJECT_TYPE" =~ ^(frontend-only|fullstack)$ ]]; then
            cp "$TEMPLATES_DIR/github-actions-react.yml" "$PROJECT_PATH/.github/workflows/frontend.yml"
            echo -e "${GREEN}  ✓ frontend.yml 생성됨${NC}"
        fi
    fi
}

# =============================================================================
# Dockerfile 생성
# =============================================================================
setup_dockerfile() {
    echo -e "${YELLOW}[2/4] Dockerfile 설정 중...${NC}"

    # Backend Dockerfile
    if [[ "$PROJECT_TYPE" =~ ^(api-only|fullstack)$ ]]; then
        if [ ! -f "$PROJECT_PATH/Dockerfile" ]; then
            cat > "$PROJECT_PATH/Dockerfile" << 'DOCKERFILE'
# Backend Dockerfile
# 멀티스테이지 빌드

# ============================================
# 빌드 스테이지
# ============================================
FROM python:3.11-slim as builder

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt .
RUN pip wheel --no-cache-dir --no-deps --wheel-dir /app/wheels -r requirements.txt

# ============================================
# 실행 스테이지
# ============================================
FROM python:3.11-slim

WORKDIR /app

RUN adduser --disabled-password --gecos "" appuser

COPY --from=builder /app/wheels /wheels
COPY --from=builder /app/requirements.txt .

RUN pip install --no-cache /wheels/*

COPY backend/ .

RUN chown -R appuser:appuser /app
USER appuser

ENV HOST=0.0.0.0
ENV PORT=8000
ENV DEBUG=false

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import httpx; httpx.get('http://localhost:8000/health')" || exit 1

EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
DOCKERFILE
            echo -e "${GREEN}  ✓ Dockerfile 생성됨${NC}"
        else
            echo -e "${CYAN}  ✓ Dockerfile 이미 존재함${NC}"
        fi
    fi

    # .dockerignore
    if [ ! -f "$PROJECT_PATH/.dockerignore" ]; then
        cat > "$PROJECT_PATH/.dockerignore" << 'DOCKERIGNORE'
# Git
.git
.gitignore

# Python
__pycache__
*.py[cod]
.venv
venv
.pytest_cache
.mypy_cache
.coverage
htmlcov

# Node
node_modules
npm-debug.log

# IDE
.idea
.vscode
*.swp

# Environment
.env
.env.local
.env.*.local

# Build
dist
build
*.egg-info

# Docker
Dockerfile*
docker-compose*

# CI/CD
.github
DOCKERIGNORE
        echo -e "${GREEN}  ✓ .dockerignore 생성됨${NC}"
    else
        echo -e "${CYAN}  ✓ .dockerignore 이미 존재함${NC}"
    fi
}

# =============================================================================
# Fly.io 설정 (선택적)
# =============================================================================
setup_flyio() {
    if [ "$DEPLOY_TARGET" != "flyio" ]; then
        return
    fi

    echo -e "${YELLOW}[2.5/4] Fly.io 설정 중...${NC}"

    if [ ! -f "$PROJECT_PATH/fly.toml" ]; then
        PROJECT_NAME=$(basename "$PROJECT_PATH" | tr '[:upper:]' '[:lower:]' | tr '_' '-' | cut -c1-23)

        cat > "$PROJECT_PATH/fly.toml" << FLYTOML
app = "$PROJECT_NAME"
primary_region = "nrt"  # Tokyo

[build]
  dockerfile = "Dockerfile"

[env]
  PORT = "8000"

[http_service]
  internal_port = 8000
  force_https = true
  auto_stop_machines = true
  auto_start_machines = true
  min_machines_running = 0

[[services]]
  protocol = "tcp"
  internal_port = 8000

  [[services.ports]]
    port = 80
    handlers = ["http"]

  [[services.ports]]
    port = 443
    handlers = ["tls", "http"]

  [[services.http_checks]]
    interval = "30s"
    timeout = "5s"
    path = "/health"
FLYTOML
        echo -e "${GREEN}  ✓ fly.toml 생성됨${NC}"
    fi
}

# =============================================================================
# Vercel 설정 (선택적)
# =============================================================================
setup_vercel() {
    if [[ ! "$DEPLOY_TARGET" =~ ^(vercel|all)$ ]]; then
        return
    fi

    if [[ ! "$PROJECT_TYPE" =~ ^(frontend-only|fullstack)$ ]]; then
        return
    fi

    echo -e "${YELLOW}[2.6/4] Vercel 설정 중...${NC}"

    if [ ! -f "$PROJECT_PATH/frontend/vercel.json" ]; then
        cat > "$PROJECT_PATH/frontend/vercel.json" << 'VERCELJSON'
{
  "$schema": "https://openapi.vercel.sh/vercel.json",
  "buildCommand": "npm run build",
  "outputDirectory": "dist",
  "framework": "vite",
  "rewrites": [
    { "source": "/(.*)", "destination": "/index.html" }
  ]
}
VERCELJSON
        echo -e "${GREEN}  ✓ frontend/vercel.json 생성됨${NC}"
    fi
}

# =============================================================================
# 환경변수 목록 출력
# =============================================================================
print_secrets_guide() {
    echo -e "${YELLOW}[3/4] 필요한 GitHub Secrets 목록...${NC}"
    echo ""

    echo -e "${CYAN}GitHub Repository > Settings > Secrets and variables > Actions 에서 등록:${NC}"
    echo ""

    if [[ "$DEPLOY_TARGET" =~ ^(railway|all)$ ]]; then
        echo -e "  ${GREEN}Backend (Railway):${NC}"
        echo "    - RAILWAY_TOKEN      : Railway API 토큰"
        echo "    - SUPABASE_URL       : Supabase 프로젝트 URL"
        echo "    - SUPABASE_KEY       : Supabase anon key"
        echo ""
    fi

    if [ "$DEPLOY_TARGET" = "flyio" ]; then
        echo -e "  ${GREEN}Backend (Fly.io):${NC}"
        echo "    - FLY_API_TOKEN      : Fly.io API 토큰"
        echo "    - SUPABASE_URL       : Supabase 프로젝트 URL"
        echo "    - SUPABASE_KEY       : Supabase anon key"
        echo ""
    fi

    if [[ "$DEPLOY_TARGET" =~ ^(vercel|all)$ ]]; then
        echo -e "  ${GREEN}Frontend (Vercel):${NC}"
        echo "    - VERCEL_TOKEN       : Vercel API 토큰"
        echo "    - VERCEL_ORG_ID      : Vercel 조직 ID"
        echo "    - VERCEL_PROJECT_ID  : Vercel 프로젝트 ID"
        echo ""
        echo -e "  ${CYAN}Vercel 설정 방법:${NC}"
        echo "    1. vercel login"
        echo "    2. cd frontend && vercel link"
        echo "    3. .vercel/project.json 에서 ID 확인"
        echo ""
    fi
}

# =============================================================================
# 완료
# =============================================================================
finish() {
    echo -e "${YELLOW}[4/4] 설정 완료...${NC}"
    echo ""

    # 생성된 파일 목록
    echo -e "${CYAN}생성/수정된 파일:${NC}"
    if [ -f "$PROJECT_PATH/.github/workflows/backend.yml" ]; then
        echo "  - .github/workflows/backend.yml"
    fi
    if [ -f "$PROJECT_PATH/.github/workflows/frontend.yml" ]; then
        echo "  - .github/workflows/frontend.yml"
    fi
    if [ -f "$PROJECT_PATH/Dockerfile" ]; then
        echo "  - Dockerfile"
    fi
    if [ -f "$PROJECT_PATH/.dockerignore" ]; then
        echo "  - .dockerignore"
    fi
    if [ -f "$PROJECT_PATH/fly.toml" ]; then
        echo "  - fly.toml"
    fi
    if [ -f "$PROJECT_PATH/frontend/vercel.json" ]; then
        echo "  - frontend/vercel.json"
    fi

    echo ""
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${GREEN}  ✅ 배포 설정 완료${NC}"
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
    echo -e "${YELLOW}다음 단계:${NC}"
    echo "  1. 위에 안내된 GitHub Secrets를 등록하세요"
    echo "  2. git add . && git commit -m 'Add CI/CD configuration'"
    echo "  3. git push origin main"
    echo "  4. GitHub Actions 탭에서 배포 상태 확인"
    echo ""
}

# =============================================================================
# 실행
# =============================================================================
setup_github_workflows
setup_dockerfile
setup_flyio
setup_vercel
print_secrets_guide
finish
