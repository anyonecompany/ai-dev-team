#!/bin/bash
# AI Dev Team Dashboard - QA 스크립트
# 린트, 타입 체크, 테스트, 빌드를 순차적으로 실행합니다.

set -e  # 에러 발생 시 중단

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 루트 디렉토리
ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
BACKEND_DIR="$ROOT_DIR/dashboard/backend"
FRONTEND_DIR="$ROOT_DIR/dashboard/frontend"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  AI Dev Team Dashboard - QA Script${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# 결과 카운터
PASSED=0
FAILED=0
SKIPPED=0

run_check() {
    local name="$1"
    local cmd="$2"
    local dir="$3"

    echo -e "${YELLOW}▶ $name${NC}"

    if [ -n "$dir" ]; then
        cd "$dir"
    fi

    if eval "$cmd" > /tmp/qa_output.txt 2>&1; then
        echo -e "${GREEN}  ✓ PASSED${NC}"
        ((PASSED++))
    else
        echo -e "${RED}  ✗ FAILED${NC}"
        echo -e "${RED}  Output:${NC}"
        cat /tmp/qa_output.txt | head -20
        ((FAILED++))
    fi

    cd "$ROOT_DIR"
    echo ""
}

skip_check() {
    local name="$1"
    local reason="$2"
    echo -e "${YELLOW}▶ $name${NC}"
    echo -e "  ⊘ SKIPPED: $reason"
    ((SKIPPED++))
    echo ""
}

# ============================================================================
# Backend Checks
# ============================================================================

echo -e "${BLUE}--- Backend Checks ---${NC}"
echo ""

# Python 버전 확인
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version 2>&1)
    echo -e "Python: $PYTHON_VERSION"
else
    echo -e "${RED}Python3 not found${NC}"
fi
echo ""

# Backend 린트 (ruff 또는 flake8)
if [ -d "$BACKEND_DIR" ]; then
    if command -v ruff &> /dev/null; then
        run_check "Backend Lint (ruff)" "ruff check . --ignore E501" "$BACKEND_DIR"
    elif command -v flake8 &> /dev/null; then
        run_check "Backend Lint (flake8)" "flake8 --max-line-length=120 --ignore=E501,W503" "$BACKEND_DIR"
    else
        skip_check "Backend Lint" "ruff/flake8 not installed"
    fi

    # Backend 테스트
    if [ -d "$BACKEND_DIR/tests" ]; then
        if command -v pytest &> /dev/null; then
            run_check "Backend Tests" "pytest tests/ -v --tb=short" "$BACKEND_DIR"
        else
            skip_check "Backend Tests" "pytest not installed"
        fi
    else
        skip_check "Backend Tests" "tests/ directory not found"
    fi

    # Import 검증
    run_check "Backend Import Check" "python3 -c 'from main import app; print(\"Import OK\")'" "$BACKEND_DIR"
else
    skip_check "Backend Checks" "Backend directory not found"
fi

# ============================================================================
# Frontend Checks
# ============================================================================

echo -e "${BLUE}--- Frontend Checks ---${NC}"
echo ""

# Node 버전 확인
if command -v node &> /dev/null; then
    NODE_VERSION=$(node --version 2>&1)
    echo -e "Node: $NODE_VERSION"
else
    echo -e "${RED}Node not found${NC}"
fi
echo ""

if [ -d "$FRONTEND_DIR" ]; then
    # 의존성 설치 확인
    if [ ! -d "$FRONTEND_DIR/node_modules" ]; then
        echo -e "${YELLOW}Installing frontend dependencies...${NC}"
        cd "$FRONTEND_DIR" && npm install
        cd "$ROOT_DIR"
    fi

    # TypeScript 타입 체크
    if [ -f "$FRONTEND_DIR/tsconfig.json" ]; then
        run_check "TypeScript Type Check" "npm run type-check 2>/dev/null || npx tsc --noEmit" "$FRONTEND_DIR"
    else
        skip_check "TypeScript Type Check" "tsconfig.json not found"
    fi

    # ESLint (있으면)
    if [ -f "$FRONTEND_DIR/.eslintrc.json" ] || [ -f "$FRONTEND_DIR/.eslintrc.js" ]; then
        run_check "Frontend Lint (ESLint)" "npm run lint" "$FRONTEND_DIR"
    else
        skip_check "Frontend Lint" "ESLint config not found"
    fi

    # 빌드 테스트
    run_check "Frontend Build" "npm run build" "$FRONTEND_DIR"
else
    skip_check "Frontend Checks" "Frontend directory not found"
fi

# ============================================================================
# Integration Checks
# ============================================================================

echo -e "${BLUE}--- Integration Checks ---${NC}"
echo ""

# 백엔드 서버 연결 테스트 (이미 실행 중인 경우)
if command -v curl &> /dev/null; then
    if curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/health 2>/dev/null | grep -q "200"; then
        run_check "Backend Health Check" "curl -s http://localhost:8000/health | grep -q healthy"
    else
        skip_check "Backend Health Check" "Backend server not running"
    fi
else
    skip_check "Backend Health Check" "curl not installed"
fi

# ============================================================================
# Summary
# ============================================================================

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  Summary${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo -e "${GREEN}  Passed:  $PASSED${NC}"
echo -e "${RED}  Failed:  $FAILED${NC}"
echo -e "${YELLOW}  Skipped: $SKIPPED${NC}"
echo ""

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}✓ All checks passed!${NC}"
    exit 0
else
    echo -e "${RED}✗ Some checks failed${NC}"
    exit 1
fi
