#!/bin/bash
#
# Pre-commit Hook 스크립트
# 커밋 전 빠른 품질 게이트 (목표: 5초 이내)
# 버전: 1.0.0
# 최종 갱신: 2026-02-03
#
# Git hook 등록:
#   cp .claude/scripts/pre-commit.sh .git/hooks/pre-commit
#   또는
#   bash .claude/scripts/install-hooks.sh
#
# 수동 실행:
#   bash .claude/scripts/pre-commit.sh
#

set -eo pipefail

# =============================================================================
# 설정
# =============================================================================
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

FAIL_COUNT=0
WARN_COUNT=0

# =============================================================================
# 유틸리티
# =============================================================================
log_pass() {
    echo -e "${GREEN}✅ PASS${NC}: $1"
}

log_fail() {
    echo -e "${RED}❌ FAIL${NC}: $1"
    ((FAIL_COUNT++))
}

log_warn() {
    echo -e "${YELLOW}⚠️  WARN${NC}: $1"
    ((WARN_COUNT++))
}

cmd_exists() {
    command -v "$1" &> /dev/null
}

# =============================================================================
# Staged 파일 목록
# =============================================================================
STAGED_FILES=$(git diff --cached --name-only --diff-filter=ACM 2>/dev/null || echo "")

if [ -z "$STAGED_FILES" ]; then
    echo -e "${CYAN}ℹ️  Staged 파일 없음 — 검사 건너뜀${NC}"
    exit 0
fi

STAGED_PY=$(echo "$STAGED_FILES" | grep "\.py$" || true)
STAGED_TS=$(echo "$STAGED_FILES" | grep -E "\.(ts|tsx)$" || true)
STAGED_JS=$(echo "$STAGED_FILES" | grep -E "\.(js|jsx)$" || true)
STAGED_ENV=$(echo "$STAGED_FILES" | grep "\.env" || true)

echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${CYAN}🔍 Pre-commit Check — $(echo "$STAGED_FILES" | wc -l | xargs)개 파일${NC}"
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# =============================================================================
# 1. .env 파일 커밋 차단
# =============================================================================
if [ -n "$STAGED_ENV" ]; then
    log_fail ".env 파일이 staged됨 — 커밋 불가"
    echo -e "${RED}   → $STAGED_ENV${NC}"
    echo -e "${YELLOW}   해결: git reset HEAD <.env 파일>${NC}"
fi

# =============================================================================
# 2. 하드코딩 시크릿 검사
# =============================================================================
SECRET_PATTERN='(API_KEY|SECRET|PASSWORD|TOKEN|PRIVATE_KEY|ACCESS_KEY)\s*=\s*["\x27][A-Za-z0-9+/=]{8,}'

for file in $STAGED_FILES; do
    if [ -f "$file" ]; then
        SECRETS=$(grep -E "$SECRET_PATTERN" "$file" 2>/dev/null | grep -v "\.env\|example\|test\|mock" || true)
        if [ -n "$SECRETS" ]; then
            log_fail "하드코딩 시크릿 발견: $file"
            echo -e "${RED}   → $(echo "$SECRETS" | head -1)${NC}"
        fi
    fi
done

if [ "$FAIL_COUNT" -eq 0 ]; then
    log_pass "하드코딩 시크릿 없음"
fi

# =============================================================================
# 3. Python 린트 (staged 파일만, 빠른 체크)
# =============================================================================
if [ -n "$STAGED_PY" ]; then
    if cmd_exists ruff; then
        RUFF_ERRORS=""
        for file in $STAGED_PY; do
            if [ -f "$file" ]; then
                RESULT=$(ruff check "$file" --select=E,F --quiet 2>&1 || true)
                [ -n "$RESULT" ] && RUFF_ERRORS+="$RESULT\n"
            fi
        done
        if [ -n "$RUFF_ERRORS" ]; then
            log_fail "Python ruff 에러"
            echo -e "${RED}$(echo -e "$RUFF_ERRORS" | head -3)${NC}"
        else
            log_pass "Python ruff 통과"
        fi
    else
        echo -e "${YELLOW}ℹ️  ruff 미설치 — Python 린트 건너뜀${NC}"
    fi
fi

# =============================================================================
# 4. TypeScript 컴파일 체크
# =============================================================================
if [ -n "$STAGED_TS" ]; then
    # tsconfig.json 찾기
    TS_CONFIG=""
    [ -f "tsconfig.json" ] && TS_CONFIG="tsconfig.json"
    [ -f "dashboard/frontend/tsconfig.json" ] && TS_CONFIG="dashboard/frontend/tsconfig.json"

    if [ -n "$TS_CONFIG" ] && cmd_exists tsc; then
        TSC_DIR=$(dirname "$TS_CONFIG")
        cd "$TSC_DIR"
        if ! tsc --noEmit 2>/dev/null; then
            log_fail "TypeScript 컴파일 에러"
        else
            log_pass "TypeScript 컴파일 통과"
        fi
        cd - > /dev/null
    else
        echo -e "${YELLOW}ℹ️  tsc 미설치 또는 tsconfig 없음 — TS 체크 건너뜀${NC}"
    fi
fi

# =============================================================================
# 5. console.log / print 경고 (차단 안 함)
# =============================================================================
DEBUG_STATEMENTS=""
for file in $STAGED_FILES; do
    if [ -f "$file" ]; then
        case "$file" in
            *.py)
                PRINTS=$(grep -n "^\s*print(" "$file" 2>/dev/null | head -2 || true)
                [ -n "$PRINTS" ] && DEBUG_STATEMENTS+="$file: print()\n"
                ;;
            *.ts|*.tsx|*.js|*.jsx)
                CONSOLE=$(grep -n "console\.log" "$file" 2>/dev/null | head -2 || true)
                [ -n "$CONSOLE" ] && DEBUG_STATEMENTS+="$file: console.log()\n"
                ;;
        esac
    fi
done

if [ -n "$DEBUG_STATEMENTS" ]; then
    log_warn "디버그 문 발견 (커밋은 허용)"
    echo -e "${YELLOW}$(echo -e "$DEBUG_STATEMENTS" | head -3)${NC}"
fi

# =============================================================================
# 결과
# =============================================================================
echo ""
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

if [ "$FAIL_COUNT" -gt 0 ]; then
    echo -e "${RED}❌ Pre-commit 실패 — 커밋 차단 (FAIL: $FAIL_COUNT)${NC}"
    echo -e "${YELLOW}위 문제를 수정 후 다시 시도하세요.${NC}"
    exit 1
else
    if [ "$WARN_COUNT" -gt 0 ]; then
        echo -e "${YELLOW}⚠️  Pre-commit 통과 (경고: $WARN_COUNT)${NC}"
    else
        echo -e "${GREEN}✅ Pre-commit 통과${NC}"
    fi
    exit 0
fi
