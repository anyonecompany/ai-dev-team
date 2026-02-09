#!/bin/bash
#
# QA 자동화 Git Hook 설치 스크립트
# 버전: 1.0.0
# 최종 갱신: 2026-02-03
#
# 사용법: bash .claude/scripts/install-hooks.sh
#

set -euo pipefail

# =============================================================================
# 설정
# =============================================================================
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(dirname "$(dirname "$SCRIPT_DIR")")"
GIT_HOOKS_DIR="$PROJECT_ROOT/.git/hooks"
PRE_COMMIT_SRC="$SCRIPT_DIR/pre-commit.sh"
PRE_COMMIT_DST="$GIT_HOOKS_DIR/pre-commit"

# 색상
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${CYAN}🔧 Git Hooks 설치${NC}"
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# =============================================================================
# 1. .git 디렉토리 확인
# =============================================================================
if [ ! -d "$PROJECT_ROOT/.git" ]; then
    echo -e "${RED}❌ .git 디렉토리가 없습니다.${NC}"
    echo -e "${YELLOW}   git init을 먼저 실행하세요.${NC}"
    exit 1
fi
echo -e "${GREEN}✅ .git 디렉토리 확인${NC}"

# =============================================================================
# 2. hooks 디렉토리 확인/생성
# =============================================================================
if [ ! -d "$GIT_HOOKS_DIR" ]; then
    mkdir -p "$GIT_HOOKS_DIR"
    echo -e "${GREEN}✅ .git/hooks 디렉토리 생성${NC}"
else
    echo -e "${GREEN}✅ .git/hooks 디렉토리 존재${NC}"
fi

# =============================================================================
# 3. pre-commit hook 복사
# =============================================================================
if [ ! -f "$PRE_COMMIT_SRC" ]; then
    echo -e "${RED}❌ pre-commit.sh를 찾을 수 없습니다.${NC}"
    echo -e "${YELLOW}   경로: $PRE_COMMIT_SRC${NC}"
    exit 1
fi

# 기존 hook 백업
if [ -f "$PRE_COMMIT_DST" ]; then
    BACKUP="$PRE_COMMIT_DST.backup.$(date +%Y%m%d%H%M%S)"
    cp "$PRE_COMMIT_DST" "$BACKUP"
    echo -e "${YELLOW}⚠️  기존 pre-commit hook 백업: $(basename "$BACKUP")${NC}"
fi

# 복사
cp "$PRE_COMMIT_SRC" "$PRE_COMMIT_DST"
echo -e "${GREEN}✅ pre-commit hook 복사 완료${NC}"

# =============================================================================
# 4. 실행 권한 부여
# =============================================================================
chmod +x "$PRE_COMMIT_DST"
echo -e "${GREEN}✅ 실행 권한 부여${NC}"

# =============================================================================
# 결과
# =============================================================================
echo ""
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}✅ Git hooks 설치 완료${NC}"
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo -e "${CYAN}설치된 hooks:${NC}"
echo -e "  - pre-commit: 커밋 전 품질 게이트"
echo ""
echo -e "${CYAN}테스트:${NC}"
echo -e "  git add . && git commit -m 'test'"
echo ""
echo -e "${YELLOW}비활성화하려면:${NC}"
echo -e "  rm $PRE_COMMIT_DST"
