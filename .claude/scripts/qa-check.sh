#!/bin/bash
#
# Self-QA Loop 자동 실행 스크립트
# 버전: 3.0.0
# 최종 갱신: 2026-02-03
#
# 사용법: bash .claude/scripts/qa-check.sh [대상경로]
# 대상경로 미지정 시 프로젝트 루트에서 전체 실행
#

set +e  # 에러 발생해도 계속 진행

# =============================================================================
# 설정
# =============================================================================
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="${1:-$(dirname "$(dirname "$SCRIPT_DIR")")}"
REPORTS_DIR="$SCRIPT_DIR/../reports"
TIMESTAMP=$(date '+%Y%m%d-%H%M%S')
REPORT_FILE="$REPORTS_DIR/qa-$TIMESTAMP.md"

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
GRAY='\033[0;90m'
NC='\033[0m'

# 카운터
PASS_COUNT=0
FAIL_COUNT=0
WARN_COUNT=0
SKIP_COUNT=0

# 리포트 버퍼
REPORT_CONTENT=""

# =============================================================================
# 유틸리티 함수
# =============================================================================

# 리포트 디렉토리 생성
mkdir -p "$REPORTS_DIR"

# 상태 출력 및 기록
log_result() {
    local stage="$1"
    local name="$2"
    local status="$3"
    local detail="${4:-}"

    case "$status" in
        PASS)
            echo -e "${GREEN}  ✅ PASS${NC}: $name"
            [ -n "$detail" ] && echo -e "${CYAN}     → $detail${NC}"
            ((PASS_COUNT++))
            REPORT_CONTENT+="- $name: **PASS** $detail\n"
            ;;
        FAIL)
            echo -e "${RED}  ❌ FAIL${NC}: $name"
            [ -n "$detail" ] && echo -e "${RED}     → $detail${NC}"
            ((FAIL_COUNT++))
            REPORT_CONTENT+="- $name: **FAIL** $detail\n"
            ;;
        WARN)
            echo -e "${YELLOW}  ⚠️  WARN${NC}: $name"
            [ -n "$detail" ] && echo -e "${YELLOW}     → $detail${NC}"
            ((WARN_COUNT++))
            REPORT_CONTENT+="- $name: **WARN** $detail\n"
            ;;
        SKIP)
            echo -e "${GRAY}  ⏭️  SKIP${NC}: $name"
            [ -n "$detail" ] && echo -e "${GRAY}     → $detail${NC}"
            ((SKIP_COUNT++))
            REPORT_CONTENT+="- $name: **SKIP** $detail\n"
            ;;
    esac
}

# 명령어 존재 확인
cmd_exists() {
    command -v "$1" &> /dev/null
}

# 프로젝트 유형 감지
detect_project() {
    HAS_PYTHON=false
    HAS_NODE=false

    [ -f "$PROJECT_ROOT/dashboard/backend/requirements.txt" ] || \
    [ -f "$PROJECT_ROOT/requirements.txt" ] || \
    [ -f "$PROJECT_ROOT/pyproject.toml" ] && HAS_PYTHON=true

    [ -f "$PROJECT_ROOT/dashboard/frontend/package.json" ] || \
    [ -f "$PROJECT_ROOT/package.json" ] && HAS_NODE=true
}

# =============================================================================
# 헤더 출력
# =============================================================================
echo -e "${BLUE}╔══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║           Self-QA Loop v3.0 — 5단계 자동 검증                 ║${NC}"
echo -e "${BLUE}║           $(date '+%Y-%m-%d %H:%M:%S')                              ║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${CYAN}대상 경로:${NC} $PROJECT_ROOT"
echo ""

detect_project
echo -e "${CYAN}프로젝트 유형:${NC} Python=$HAS_PYTHON, Node=$HAS_NODE"
echo ""

# 리포트 헤더
REPORT_CONTENT="# Self-QA Report\n"
REPORT_CONTENT+="- 일시: $(date '+%Y-%m-%d %H:%M:%S')\n"
REPORT_CONTENT+="- 대상: $PROJECT_ROOT\n"
REPORT_CONTENT+="- Python: $HAS_PYTHON, Node: $HAS_NODE\n\n"

# =============================================================================
# 1단계: 정적 분석
# =============================================================================
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}📋 1단계: 정적 분석${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
REPORT_CONTENT+="\n## 1단계: 정적 분석\n"

# Python 정적 분석
if [ "$HAS_PYTHON" = true ]; then
    BACKEND_DIR="$PROJECT_ROOT/dashboard/backend"
    [ ! -d "$BACKEND_DIR" ] && BACKEND_DIR="$PROJECT_ROOT"

    if cmd_exists ruff; then
        if ruff check "$BACKEND_DIR" --quiet 2>/dev/null; then
            log_result 1 "Python ruff" PASS "린트 에러 없음"
        else
            RUFF_ERRORS=$(ruff check "$BACKEND_DIR" 2>&1 | head -5)
            log_result 1 "Python ruff" FAIL "$RUFF_ERRORS"
        fi
    elif cmd_exists pylint; then
        if pylint "$BACKEND_DIR" --exit-zero --score=n --disable=C,R 2>/dev/null | grep -q "^$"; then
            log_result 1 "Python pylint" PASS "린트 에러 없음"
        else
            log_result 1 "Python pylint" WARN "일부 경고 발생"
        fi
    elif cmd_exists flake8; then
        if flake8 "$BACKEND_DIR" --count --select=E,F --show-source --statistics 2>/dev/null | grep -q "^0$"; then
            log_result 1 "Python flake8" PASS "린트 에러 없음"
        else
            log_result 1 "Python flake8" WARN "일부 경고 발생"
        fi
    else
        log_result 1 "Python linter" SKIP "ruff/pylint/flake8 미설치"
    fi
else
    log_result 1 "Python linter" SKIP "Python 프로젝트 아님"
fi

# Node 정적 분석
if [ "$HAS_NODE" = true ]; then
    FRONTEND_DIR="$PROJECT_ROOT/dashboard/frontend"
    [ ! -d "$FRONTEND_DIR" ] && FRONTEND_DIR="$PROJECT_ROOT"

    if [ -f "$FRONTEND_DIR/package.json" ]; then
        cd "$FRONTEND_DIR"
        if grep -q '"lint"' package.json 2>/dev/null; then
            if npm run lint --silent 2>/dev/null; then
                log_result 1 "Node ESLint" PASS "린트 에러 없음"
            else
                log_result 1 "Node ESLint" WARN "린트 경고 발생"
            fi
        elif cmd_exists eslint; then
            if eslint src --ext ts,tsx --quiet 2>/dev/null; then
                log_result 1 "Node ESLint" PASS "린트 에러 없음"
            else
                log_result 1 "Node ESLint" WARN "린트 경고 발생"
            fi
        else
            log_result 1 "Node ESLint" SKIP "ESLint 미설치"
        fi
        cd "$PROJECT_ROOT"
    fi
else
    log_result 1 "Node linter" SKIP "Node 프로젝트 아님"
fi

# 파일 길이 검사
LONG_FILES=$(find "$PROJECT_ROOT" -name "*.py" -o -name "*.ts" -o -name "*.tsx" 2>/dev/null | \
    xargs wc -l 2>/dev/null | awk '$1 > 300 && !/total/ {print $2 ": " $1 "줄"}' | head -5)
if [ -n "$LONG_FILES" ]; then
    log_result 1 "파일 길이 검사" WARN "300줄 초과: $LONG_FILES"
else
    log_result 1 "파일 길이 검사" PASS "모든 파일 300줄 이하"
fi

echo ""

# =============================================================================
# 2단계: 타입 체크
# =============================================================================
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}🔍 2단계: 타입 체크${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
REPORT_CONTENT+="\n## 2단계: 타입 체크\n"

# Python mypy
if [ "$HAS_PYTHON" = true ]; then
    BACKEND_DIR="$PROJECT_ROOT/dashboard/backend"
    [ ! -d "$BACKEND_DIR" ] && BACKEND_DIR="$PROJECT_ROOT"

    if cmd_exists mypy; then
        if mypy "$BACKEND_DIR" --ignore-missing-imports --no-error-summary 2>/dev/null | grep -q "Success"; then
            log_result 2 "Python mypy" PASS "타입 에러 없음"
        else
            MYPY_ERRORS=$(mypy "$BACKEND_DIR" --ignore-missing-imports 2>&1 | grep "error:" | head -3)
            if [ -n "$MYPY_ERRORS" ]; then
                log_result 2 "Python mypy" WARN "$MYPY_ERRORS"
            else
                log_result 2 "Python mypy" PASS "타입 에러 없음"
            fi
        fi
    else
        log_result 2 "Python mypy" SKIP "mypy 미설치"
    fi
else
    log_result 2 "Python mypy" SKIP "Python 프로젝트 아님"
fi

# TypeScript tsc
if [ "$HAS_NODE" = true ]; then
    FRONTEND_DIR="$PROJECT_ROOT/dashboard/frontend"
    [ ! -d "$FRONTEND_DIR" ] && FRONTEND_DIR="$PROJECT_ROOT"

    if [ -f "$FRONTEND_DIR/tsconfig.json" ]; then
        cd "$FRONTEND_DIR"
        if grep -q '"type-check"' package.json 2>/dev/null; then
            if npm run type-check --silent 2>/dev/null; then
                log_result 2 "TypeScript tsc" PASS "타입 에러 없음"
            else
                log_result 2 "TypeScript tsc" FAIL "타입 에러 발생"
            fi
        elif cmd_exists tsc; then
            if tsc --noEmit 2>/dev/null; then
                log_result 2 "TypeScript tsc" PASS "타입 에러 없음"
            else
                log_result 2 "TypeScript tsc" FAIL "타입 에러 발생"
            fi
        else
            log_result 2 "TypeScript tsc" SKIP "tsc 미설치"
        fi
        cd "$PROJECT_ROOT"
    else
        log_result 2 "TypeScript tsc" SKIP "tsconfig.json 없음"
    fi
else
    log_result 2 "TypeScript tsc" SKIP "Node 프로젝트 아님"
fi

echo ""

# =============================================================================
# 3단계: 테스트 실행
# =============================================================================
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}🧪 3단계: 테스트 실행${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
REPORT_CONTENT+="\n## 3단계: 테스트\n"

# Python pytest
if [ "$HAS_PYTHON" = true ]; then
    BACKEND_DIR="$PROJECT_ROOT/dashboard/backend"
    [ ! -d "$BACKEND_DIR" ] && BACKEND_DIR="$PROJECT_ROOT"

    if cmd_exists pytest; then
        cd "$BACKEND_DIR"
        PYTEST_OUTPUT=$(pytest --tb=short -q 2>&1 || true)
        if echo "$PYTEST_OUTPUT" | grep -q "passed"; then
            PASSED=$(echo "$PYTEST_OUTPUT" | grep -oE "[0-9]+ passed" | head -1)
            log_result 3 "Python pytest" PASS "$PASSED"

            # 커버리지 체크
            if cmd_exists pytest && pytest --cov --cov-report=term-missing -q 2>&1 | grep -q "TOTAL"; then
                COV=$(pytest --cov --cov-report=term-missing -q 2>&1 | grep "TOTAL" | awk '{print $NF}')
                COV_NUM=${COV//%/}
                if [ "${COV_NUM:-0}" -ge 80 ]; then
                    log_result 3 "테스트 커버리지" PASS "$COV"
                else
                    log_result 3 "테스트 커버리지" WARN "$COV (80% 미만)"
                fi
            fi
        elif echo "$PYTEST_OUTPUT" | grep -q "failed\|error"; then
            log_result 3 "Python pytest" FAIL "테스트 실패"
        else
            log_result 3 "Python pytest" SKIP "테스트 없음"
        fi
        cd "$PROJECT_ROOT"
    else
        log_result 3 "Python pytest" SKIP "pytest 미설치"
    fi
else
    log_result 3 "Python pytest" SKIP "Python 프로젝트 아님"
fi

# Node test
if [ "$HAS_NODE" = true ]; then
    FRONTEND_DIR="$PROJECT_ROOT/dashboard/frontend"
    [ ! -d "$FRONTEND_DIR" ] && FRONTEND_DIR="$PROJECT_ROOT"

    if [ -f "$FRONTEND_DIR/package.json" ]; then
        cd "$FRONTEND_DIR"
        if grep -q '"test"' package.json 2>/dev/null; then
            if npm test --silent 2>/dev/null; then
                log_result 3 "Node test" PASS "테스트 통과"
            else
                log_result 3 "Node test" WARN "테스트 실패 또는 없음"
            fi
        else
            log_result 3 "Node test" SKIP "test 스크립트 없음"
        fi
        cd "$PROJECT_ROOT"
    fi
else
    log_result 3 "Node test" SKIP "Node 프로젝트 아님"
fi

echo ""

# =============================================================================
# 4단계: 보안 스캔
# =============================================================================
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}🔒 4단계: 보안 스캔${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
REPORT_CONTENT+="\n## 4단계: 보안 스캔\n"

# Python 의존성 취약점
if [ "$HAS_PYTHON" = true ]; then
    if cmd_exists pip-audit; then
        BACKEND_DIR="$PROJECT_ROOT/dashboard/backend"
        [ ! -d "$BACKEND_DIR" ] && BACKEND_DIR="$PROJECT_ROOT"
        cd "$BACKEND_DIR"
        if pip-audit -r requirements.txt --progress-spinner=off 2>/dev/null | grep -q "No known vulnerabilities"; then
            log_result 4 "Python pip-audit" PASS "알려진 취약점 없음"
        else
            VULNS=$(pip-audit -r requirements.txt 2>&1 | grep -c "vulnerability" || echo "0")
            log_result 4 "Python pip-audit" WARN "$VULNS개 취약점 발견"
        fi
        cd "$PROJECT_ROOT"
    else
        log_result 4 "Python pip-audit" SKIP "pip-audit 미설치"
    fi
fi

# Node 의존성 취약점
if [ "$HAS_NODE" = true ]; then
    FRONTEND_DIR="$PROJECT_ROOT/dashboard/frontend"
    [ ! -d "$FRONTEND_DIR" ] && FRONTEND_DIR="$PROJECT_ROOT"

    if [ -f "$FRONTEND_DIR/package-lock.json" ]; then
        cd "$FRONTEND_DIR"
        AUDIT_RESULT=$(npm audit --audit-level=high 2>&1 || true)
        if echo "$AUDIT_RESULT" | grep -q "found 0 vulnerabilities"; then
            log_result 4 "Node npm audit" PASS "high/critical 취약점 없음"
        elif echo "$AUDIT_RESULT" | grep -qE "high|critical"; then
            log_result 4 "Node npm audit" WARN "취약점 발견"
        else
            log_result 4 "Node npm audit" PASS "high/critical 취약점 없음"
        fi
        cd "$PROJECT_ROOT"
    else
        log_result 4 "Node npm audit" SKIP "package-lock.json 없음"
    fi
fi

# 하드코딩 시크릿 검사
SECRET_PATTERNS='(API_KEY|SECRET|PASSWORD|TOKEN|PRIVATE_KEY)\s*=\s*["\x27][^"\x27]{8,}'
SECRET_FILES=$(grep -rIE "$SECRET_PATTERNS" "$PROJECT_ROOT" \
    --include="*.py" --include="*.ts" --include="*.tsx" --include="*.js" --include="*.jsx" \
    --exclude-dir=node_modules --exclude-dir=venv --exclude-dir=.git \
    --exclude="*.env*" 2>/dev/null | head -5 || true)

if [ -n "$SECRET_FILES" ]; then
    log_result 4 "하드코딩 시크릿" FAIL "의심 패턴 발견"
else
    log_result 4 "하드코딩 시크릿" PASS "하드코딩된 시크릿 없음"
fi

# .env가 .gitignore에 있는지 확인
if [ -f "$PROJECT_ROOT/.gitignore" ]; then
    if grep -q "\.env" "$PROJECT_ROOT/.gitignore"; then
        log_result 4 ".env in .gitignore" PASS ".env가 .gitignore에 포함됨"
    else
        log_result 4 ".env in .gitignore" WARN ".env가 .gitignore에 없음"
    fi
else
    log_result 4 ".env in .gitignore" WARN ".gitignore 없음"
fi

# .env가 git tracked인지 확인
if [ -d "$PROJECT_ROOT/.git" ]; then
    if git -C "$PROJECT_ROOT" ls-files --error-unmatch "*.env" 2>/dev/null; then
        log_result 4 ".env git tracked" FAIL ".env 파일이 git에 추적됨!"
    else
        log_result 4 ".env git tracked" PASS ".env 파일이 git에 추적되지 않음"
    fi
else
    log_result 4 ".env git tracked" SKIP "git 저장소 아님"
fi

echo ""

# =============================================================================
# 5단계: 종합 판정
# =============================================================================
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}📊 5단계: 종합 판정${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
REPORT_CONTENT+="\n## 5단계: 종합\n"
REPORT_CONTENT+="- PASS: ${PASS_COUNT}개\n"
REPORT_CONTENT+="- WARN: ${WARN_COUNT}개\n"
REPORT_CONTENT+="- FAIL: ${FAIL_COUNT}개\n"
REPORT_CONTENT+="- SKIP: ${SKIP_COUNT}개\n"

echo ""
echo -e "  ${GREEN}PASS${NC}: $PASS_COUNT개"
echo -e "  ${YELLOW}WARN${NC}: $WARN_COUNT개"
echo -e "  ${RED}FAIL${NC}: $FAIL_COUNT개"
echo -e "  ${GRAY}SKIP${NC}: $SKIP_COUNT개"
echo ""

if [ "$FAIL_COUNT" -gt 0 ]; then
    VERDICT="❌ 수정 필요"
    echo -e "${RED}╔══════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${RED}║  ❌ 수정 필요 — FAIL ${FAIL_COUNT}건 발견                              ║${NC}"
    echo -e "${RED}╚══════════════════════════════════════════════════════════════╝${NC}"
    EXIT_CODE=1
elif [ "$WARN_COUNT" -gt 0 ]; then
    VERDICT="⚠️ 납품 가능 (경고 확인 필요)"
    echo -e "${YELLOW}╔══════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${YELLOW}║  ⚠️  납품 가능 (경고 확인 필요) — WARN ${WARN_COUNT}건               ║${NC}"
    echo -e "${YELLOW}╚══════════════════════════════════════════════════════════════╝${NC}"
    EXIT_CODE=0
else
    VERDICT="✅ 납품 가능"
    echo -e "${GREEN}╔══════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║  ✅ 납품 가능 — 모든 검사 통과                                ║${NC}"
    echo -e "${GREEN}╚══════════════════════════════════════════════════════════════╝${NC}"
    EXIT_CODE=0
fi

REPORT_CONTENT+="- 판정: $VERDICT\n"

# 리포트 파일 저장
# 상단에 판정 추가
FINAL_REPORT="# Self-QA Report\n"
FINAL_REPORT+="- 일시: $(date '+%Y-%m-%d %H:%M:%S')\n"
FINAL_REPORT+="- 대상: $PROJECT_ROOT\n"
FINAL_REPORT+="- **판정: $VERDICT**\n\n"
FINAL_REPORT+="---\n\n"
FINAL_REPORT+="$REPORT_CONTENT"

echo -e "$FINAL_REPORT" > "$REPORT_FILE"

echo ""
echo -e "${CYAN}📄 리포트 저장: $REPORT_FILE${NC}"

exit $EXIT_CODE
