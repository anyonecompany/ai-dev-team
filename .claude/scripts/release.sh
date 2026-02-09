#!/bin/bash
#
# 릴리즈 자동화 스크립트
# 버전: 1.0.0
#
# 사용법:
#   bash .claude/scripts/release.sh [버전] [릴리즈노트]
#
# 예시:
#   bash .claude/scripts/release.sh 1.0.0 "MVP 출시"
#   bash .claude/scripts/release.sh 1.1.0 "사용자 인증 기능 추가"
#
# 동작:
#   1. QA 체크 (qa-check.sh 실행)
#   2. Git 상태 확인
#   3. CHANGELOG.md 자동 생성/갱신
#   4. Git 태그 생성
#   5. Push + Tags Push
#

set -e

# =============================================================================
# 설정
# =============================================================================
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(dirname "$(dirname "$SCRIPT_DIR")")"

# 색상
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

# =============================================================================
# 입력 검증
# =============================================================================
if [ $# -lt 1 ]; then
    echo -e "${RED}사용법: $0 [버전] [릴리즈노트]${NC}"
    echo ""
    echo -e "${CYAN}예시:${NC}"
    echo "  $0 1.0.0 \"MVP 출시\""
    echo "  $0 1.1.0 \"사용자 인증 기능 추가\""
    echo ""
    echo -e "${CYAN}버전 형식:${NC}"
    echo "  X.Y.Z (예: 1.0.0, 1.2.3)"
    exit 1
fi

VERSION="$1"
RELEASE_NOTE="${2:-Release v$VERSION}"

# 버전 형식 검증
if [[ ! "$VERSION" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
    echo -e "${RED}잘못된 버전 형식: $VERSION${NC}"
    echo -e "${CYAN}형식: X.Y.Z (예: 1.0.0)${NC}"
    exit 1
fi

TAG_NAME="v$VERSION"
TODAY=$(date '+%Y-%m-%d')

echo -e "${CYAN}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  릴리즈 자동화"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -e "${NC}"
echo -e "버전: ${GREEN}$TAG_NAME${NC}"
echo -e "노트: ${GREEN}$RELEASE_NOTE${NC}"
echo ""

# =============================================================================
# 1. QA 체크
# =============================================================================
echo -e "${YELLOW}[1/5] QA 체크 실행 중...${NC}"

QA_SCRIPT="$SCRIPT_DIR/qa-check.sh"

if [ -f "$QA_SCRIPT" ]; then
    # QA 실행 (FAIL 시 중단)
    set +e
    bash "$QA_SCRIPT" > /tmp/qa-result.txt 2>&1
    QA_EXIT=$?
    set -e

    # 결과 확인
    if grep -q "FAIL:" /tmp/qa-result.txt; then
        echo -e "${RED}  ❌ QA 체크 실패 — 릴리즈 중단${NC}"
        echo ""
        echo -e "${YELLOW}QA 결과:${NC}"
        grep -E "(FAIL:|WARN:|판정:)" /tmp/qa-result.txt || true
        echo ""
        echo -e "${CYAN}qa-check.sh를 다시 실행하여 상세 내용을 확인하세요.${NC}"
        exit 1
    fi

    # WARN은 경고만 출력하고 진행
    if grep -q "WARN:" /tmp/qa-result.txt; then
        echo -e "${YELLOW}  ⚠️  QA 경고 발견 (릴리즈는 계속됨)${NC}"
        grep "WARN:" /tmp/qa-result.txt | head -3
    else
        echo -e "${GREEN}  ✓ QA 체크 통과${NC}"
    fi
else
    echo -e "${YELLOW}  ⚠️  qa-check.sh 없음 — QA 스킵${NC}"
fi

# =============================================================================
# 2. Git 상태 확인
# =============================================================================
echo -e "${YELLOW}[2/5] Git 상태 확인 중...${NC}"

# Git 저장소 확인
if [ ! -d ".git" ]; then
    echo -e "${RED}  ❌ Git 저장소가 아닙니다.${NC}"
    exit 1
fi

# 현재 브랜치 확인
CURRENT_BRANCH=$(git branch --show-current)
echo -e "  현재 브랜치: ${CYAN}$CURRENT_BRANCH${NC}"

# Uncommitted changes 확인
if [ -n "$(git status --porcelain)" ]; then
    echo -e "${YELLOW}  ⚠️  커밋되지 않은 변경사항이 있습니다:${NC}"
    git status --short | head -10

    echo ""
    read -p "변경사항을 커밋하지 않고 계속하시겠습니까? (y/N) " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo -e "${YELLOW}릴리즈 중단됨. 먼저 변경사항을 커밋하세요.${NC}"
        exit 1
    fi
else
    echo -e "${GREEN}  ✓ 작업 디렉토리 깨끗함${NC}"
fi

# 기존 태그 확인
if git tag -l | grep -q "^$TAG_NAME$"; then
    echo -e "${RED}  ❌ 태그 $TAG_NAME 이미 존재합니다.${NC}"
    echo -e "${CYAN}다른 버전을 사용하거나, git tag -d $TAG_NAME 으로 삭제하세요.${NC}"
    exit 1
fi

echo -e "${GREEN}  ✓ Git 상태 확인 완료${NC}"

# =============================================================================
# 3. CHANGELOG.md 생성/갱신
# =============================================================================
echo -e "${YELLOW}[3/5] CHANGELOG.md 갱신 중...${NC}"

CHANGELOG_FILE="CHANGELOG.md"

# 이전 태그 찾기 (없으면 초기 커밋부터)
PREVIOUS_TAG=$(git describe --tags --abbrev=0 2>/dev/null || echo "")

if [ -n "$PREVIOUS_TAG" ]; then
    GIT_LOG_RANGE="$PREVIOUS_TAG..HEAD"
    echo -e "  이전 버전: ${CYAN}$PREVIOUS_TAG${NC}"
else
    GIT_LOG_RANGE="HEAD"
    echo -e "  이전 버전: ${CYAN}(없음 - 첫 릴리즈)${NC}"
fi

# 커밋 로그에서 conventional commits 추출
FEAT_COMMITS=$(git log $GIT_LOG_RANGE --pretty=format:"%s" 2>/dev/null | grep -E "^feat(\(.+\))?:" | sed 's/^feat\(.*\): //' || true)
FIX_COMMITS=$(git log $GIT_LOG_RANGE --pretty=format:"%s" 2>/dev/null | grep -E "^fix(\(.+\))?:" | sed 's/^fix\(.*\): //' || true)
REFACTOR_COMMITS=$(git log $GIT_LOG_RANGE --pretty=format:"%s" 2>/dev/null | grep -E "^refactor(\(.+\))?:" | sed 's/^refactor\(.*\): //' || true)
DOCS_COMMITS=$(git log $GIT_LOG_RANGE --pretty=format:"%s" 2>/dev/null | grep -E "^docs(\(.+\))?:" | sed 's/^docs\(.*\): //' || true)
OTHER_COMMITS=$(git log $GIT_LOG_RANGE --pretty=format:"%s" 2>/dev/null | grep -vE "^(feat|fix|refactor|docs|chore|style|test)(\(.+\))?:" | head -10 || true)

# CHANGELOG 엔트리 생성
NEW_ENTRY="## [$VERSION] - $TODAY

> $RELEASE_NOTE
"

if [ -n "$FEAT_COMMITS" ]; then
    NEW_ENTRY+="
### Added
"
    while IFS= read -r commit; do
        [ -n "$commit" ] && NEW_ENTRY+="- $commit
"
    done <<< "$FEAT_COMMITS"
fi

if [ -n "$FIX_COMMITS" ]; then
    NEW_ENTRY+="
### Fixed
"
    while IFS= read -r commit; do
        [ -n "$commit" ] && NEW_ENTRY+="- $commit
"
    done <<< "$FIX_COMMITS"
fi

if [ -n "$REFACTOR_COMMITS" ]; then
    NEW_ENTRY+="
### Changed
"
    while IFS= read -r commit; do
        [ -n "$commit" ] && NEW_ENTRY+="- $commit
"
    done <<< "$REFACTOR_COMMITS"
fi

if [ -n "$DOCS_COMMITS" ]; then
    NEW_ENTRY+="
### Documentation
"
    while IFS= read -r commit; do
        [ -n "$commit" ] && NEW_ENTRY+="- $commit
"
    done <<< "$DOCS_COMMITS"
fi

if [ -n "$OTHER_COMMITS" ] && [ -z "$FEAT_COMMITS" ] && [ -z "$FIX_COMMITS" ] && [ -z "$REFACTOR_COMMITS" ]; then
    NEW_ENTRY+="
### Changes
"
    while IFS= read -r commit; do
        [ -n "$commit" ] && NEW_ENTRY+="- $commit
"
    done <<< "$OTHER_COMMITS"
fi

# CHANGELOG 파일 업데이트
if [ -f "$CHANGELOG_FILE" ]; then
    # 기존 파일에 추가 (헤더 다음에)
    HEADER="# Changelog

"
    EXISTING_CONTENT=$(cat "$CHANGELOG_FILE" | tail -n +3)
    echo -e "${HEADER}${NEW_ENTRY}
${EXISTING_CONTENT}" > "$CHANGELOG_FILE"
else
    # 새 파일 생성
    cat > "$CHANGELOG_FILE" << CHANGELOG
# Changelog

모든 주요 변경사항은 이 파일에 기록됩니다.
형식: [Keep a Changelog](https://keepachangelog.com/ko/1.1.0/)

$NEW_ENTRY
CHANGELOG
fi

echo -e "${GREEN}  ✓ CHANGELOG.md 갱신됨${NC}"

# CHANGELOG 커밋
git add "$CHANGELOG_FILE"
git commit -m "docs: update CHANGELOG for v$VERSION" --no-verify 2>/dev/null || true

# =============================================================================
# 4. Git 태그 생성
# =============================================================================
echo -e "${YELLOW}[4/5] Git 태그 생성 중...${NC}"

git tag -a "$TAG_NAME" -m "Release $TAG_NAME

$RELEASE_NOTE

Generated by release.sh"

echo -e "${GREEN}  ✓ 태그 $TAG_NAME 생성됨${NC}"

# =============================================================================
# 5. Push
# =============================================================================
echo -e "${YELLOW}[5/5] Push 중...${NC}"

# 원격 저장소 확인
REMOTE=$(git remote | head -1)

if [ -z "$REMOTE" ]; then
    echo -e "${YELLOW}  ⚠️  원격 저장소가 설정되지 않았습니다.${NC}"
    echo -e "${CYAN}  수동으로 push하세요:${NC}"
    echo "    git push origin $CURRENT_BRANCH"
    echo "    git push origin $TAG_NAME"
else
    echo -e "  원격: ${CYAN}$REMOTE${NC}"

    # Push commits
    git push "$REMOTE" "$CURRENT_BRANCH" 2>/dev/null || {
        echo -e "${YELLOW}  ⚠️  Push 실패 — 수동으로 push하세요${NC}"
    }

    # Push tags
    git push "$REMOTE" "$TAG_NAME" 2>/dev/null || {
        echo -e "${YELLOW}  ⚠️  태그 Push 실패 — 수동으로 push하세요${NC}"
    }

    echo -e "${GREEN}  ✓ Push 완료${NC}"
fi

# =============================================================================
# 완료
# =============================================================================
echo ""
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}  ✅ v$VERSION 릴리즈 완료${NC}"
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo -e "${YELLOW}다음 단계:${NC}"
echo "  1. CI/CD 파이프라인이 자동으로 배포를 시작합니다"
echo "  2. GitHub Actions 탭에서 배포 상태를 확인하세요"
if [ -n "$REMOTE" ]; then
    REMOTE_URL=$(git remote get-url "$REMOTE" 2>/dev/null | sed 's/\.git$//' | sed 's/git@github.com:/https:\/\/github.com\//')
    if [ -n "$REMOTE_URL" ]; then
        echo ""
        echo -e "${CYAN}GitHub:${NC}"
        echo "  - Actions: ${REMOTE_URL}/actions"
        echo "  - Release: ${REMOTE_URL}/releases/tag/$TAG_NAME"
    fi
fi
echo ""
