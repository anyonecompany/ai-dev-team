#!/bin/bash
#
# 패턴 저장 스크립트
# 버전: 1.0.0
#
# 사용법:
#   bash .claude/scripts/save-pattern.sh [패턴이름] [카테고리]
#
# 카테고리:
#   backend  - 백엔드 패턴
#   frontend - 프론트엔드 패턴
#   devops   - DevOps 패턴
#   general  - 일반 패턴
#
# 예시:
#   bash .claude/scripts/save-pattern.sh rate-limiting backend
#   bash .claude/scripts/save-pattern.sh form-validation frontend
#

set -e

# =============================================================================
# 설정
# =============================================================================
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(dirname "$(dirname "$SCRIPT_DIR")")"
KNOWLEDGE_DIR="$PROJECT_ROOT/.claude/knowledge"
PATTERNS_DIR="$KNOWLEDGE_DIR/patterns"

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
    echo -e "${RED}사용법: $0 [패턴이름] [카테고리]${NC}"
    echo ""
    echo -e "${CYAN}카테고리:${NC}"
    echo "  backend  - 백엔드 패턴"
    echo "  frontend - 프론트엔드 패턴"
    echo "  devops   - DevOps 패턴"
    echo "  general  - 일반 패턴"
    echo ""
    echo -e "${CYAN}예시:${NC}"
    echo "  $0 rate-limiting backend"
    echo "  $0 form-validation frontend"
    exit 1
fi

PATTERN_NAME="$1"
CATEGORY="${2:-general}"

# 패턴 이름 형식 검증 (kebab-case)
if [[ ! "$PATTERN_NAME" =~ ^[a-z][a-z0-9-]*$ ]]; then
    echo -e "${RED}잘못된 패턴 이름: $PATTERN_NAME${NC}"
    echo -e "${CYAN}형식: kebab-case (예: rate-limiting, form-validation)${NC}"
    exit 1
fi

# 카테고리 검증
VALID_CATEGORIES="backend frontend devops general"
if [[ ! " $VALID_CATEGORIES " =~ " $CATEGORY " ]]; then
    echo -e "${RED}잘못된 카테고리: $CATEGORY${NC}"
    echo -e "${CYAN}유효한 카테고리: $VALID_CATEGORIES${NC}"
    exit 1
fi

TODAY=$(date '+%Y-%m-%d')
PATTERN_FILE="$PATTERNS_DIR/$PATTERN_NAME.md"

# =============================================================================
# 기존 패턴 확인
# =============================================================================
if [ -f "$PATTERN_FILE" ]; then
    echo -e "${YELLOW}경고: $PATTERN_NAME.md 파일이 이미 존재합니다.${NC}"
    read -p "덮어쓰시겠습니까? (y/N) " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo -e "${YELLOW}작업 취소됨.${NC}"
        exit 0
    fi
fi

# =============================================================================
# 카테고리별 제목 매핑
# =============================================================================
case $CATEGORY in
    backend)
        CATEGORY_TITLE="Backend"
        ;;
    frontend)
        CATEGORY_TITLE="Frontend"
        ;;
    devops)
        CATEGORY_TITLE="DevOps"
        ;;
    *)
        CATEGORY_TITLE="General"
        ;;
esac

# 패턴 이름을 Title Case로 변환
PATTERN_TITLE=$(echo "$PATTERN_NAME" | sed 's/-/ /g' | awk '{for(i=1;i<=NF;i++) $i=toupper(substr($i,1,1)) tolower(substr($i,2))}1')

# =============================================================================
# 템플릿 생성
# =============================================================================
mkdir -p "$PATTERNS_DIR"

cat > "$PATTERN_FILE" << TEMPLATE
# $PATTERN_TITLE Pattern

> 카테고리: $CATEGORY_TITLE
> 출처: [파일 경로 또는 참조]
> 최종 갱신: $TODAY

## 개요

[이 패턴이 해결하는 문제와 핵심 아이디어를 1-2문장으로 설명]

## 문제 상황

[이 패턴이 필요한 상황, 기존 코드의 문제점]

\`\`\`python
# 문제가 있는 코드 예시
\`\`\`

## 구현

### 핵심 코드

\`\`\`python
# 패턴 구현 코드
\`\`\`

### 사용법

\`\`\`python
# 패턴 사용 예시
\`\`\`

## 장점

1. **[장점 1]**: 설명
2. **[장점 2]**: 설명
3. **[장점 3]**: 설명

## 주의사항

- [주의사항 1]
- [주의사항 2]

## 의존성

\`\`\`txt
# 필요한 패키지
\`\`\`

## 관련 패턴

- [관련 패턴 1](#)
- [관련 패턴 2](#)
TEMPLATE

# =============================================================================
# 완료
# =============================================================================
echo ""
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}  ✅ 패턴 템플릿 생성 완료${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo -e "파일: ${CYAN}$PATTERN_FILE${NC}"
echo ""
echo -e "${YELLOW}다음 단계:${NC}"
echo "  1. 생성된 파일을 열어 내용을 작성하세요"
echo "  2. [파일 경로 또는 참조] 부분을 실제 출처로 교체하세요"
echo "  3. 코드 예시를 실제 구현으로 교체하세요"
echo ""

# 에디터로 열기 (선택사항)
if command -v code &> /dev/null; then
    read -p "VS Code에서 파일을 열까요? (y/N) " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        code "$PATTERN_FILE"
    fi
fi
