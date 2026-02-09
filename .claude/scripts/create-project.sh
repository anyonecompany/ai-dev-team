#!/bin/bash
#
# 프로젝트 생성기
# 버전: 1.0.0
#
# 사용법:
#   bash .claude/scripts/create-project.sh [프로젝트명] [유형]
#
# 유형:
#   api-only  - FastAPI 백엔드만
#   fullstack - FastAPI + React 풀스택
#   landing   - 단일 페이지 랜딩 (React + 결제)
#   saas      - fullstack + 인증 + 구독 결제 + 대시보드
#
# 예시:
#   bash .claude/scripts/create-project.sh my-saas-app fullstack
#   bash .claude/scripts/create-project.sh landing-page landing
#

set -e

# =============================================================================
# 설정
# =============================================================================
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(dirname "$(dirname "$SCRIPT_DIR")")"
TEMPLATES_DIR="$PROJECT_ROOT/.claude/templates/project-types"
PROJECTS_DIR="$PROJECT_ROOT/projects"

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
    echo -e "${RED}사용법: $0 [프로젝트명] [유형]${NC}"
    echo ""
    echo -e "${CYAN}유형:${NC}"
    echo "  api-only  - FastAPI 백엔드만"
    echo "  fullstack - FastAPI + React 풀스택"
    echo "  landing   - 단일 페이지 랜딩 (React + 결제)"
    echo "  saas      - fullstack + 인증 + 구독 결제 + 대시보드"
    echo ""
    echo -e "${CYAN}예시:${NC}"
    echo "  $0 my-app fullstack"
    exit 1
fi

PROJECT_NAME="$1"
PROJECT_TYPE="$2"
TIMESTAMP=$(date '+%Y%m%d%H%M%S')

# 프로젝트명 검증 (영문 소문자, 숫자, 하이픈만)
if [[ ! "$PROJECT_NAME" =~ ^[a-z][a-z0-9-]*$ ]]; then
    echo -e "${RED}프로젝트명은 영문 소문자로 시작하고, 소문자/숫자/하이픈만 사용 가능합니다.${NC}"
    echo -e "${CYAN}예시: my-app, saas-product, landing-page${NC}"
    exit 1
fi

# 유형 검증
if [[ ! "$PROJECT_TYPE" =~ ^(api-only|fullstack|landing|saas)$ ]]; then
    echo -e "${RED}지원하지 않는 유형: $PROJECT_TYPE${NC}"
    echo -e "${CYAN}지원 유형: api-only, fullstack, landing, saas${NC}"
    exit 1
fi

# 템플릿 디렉토리 확인
TEMPLATE_DIR="$TEMPLATES_DIR/$PROJECT_TYPE"
if [ ! -d "$TEMPLATE_DIR" ]; then
    echo -e "${RED}템플릿을 찾을 수 없습니다: $TEMPLATE_DIR${NC}"
    exit 1
fi

# 프로젝트 디렉토리
PROJECT_DIR="$PROJECTS_DIR/${PROJECT_NAME}-${TIMESTAMP}"

if [ -d "$PROJECT_DIR" ]; then
    echo -e "${RED}프로젝트 디렉토리가 이미 존재합니다: $PROJECT_DIR${NC}"
    exit 1
fi

echo -e "${CYAN}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  프로젝트 생성기"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -e "${NC}"
echo -e "프로젝트: ${GREEN}$PROJECT_NAME${NC}"
echo -e "유형: ${GREEN}$PROJECT_TYPE${NC}"
echo -e "경로: ${GREEN}$PROJECT_DIR${NC}"
echo ""

# =============================================================================
# 1. 템플릿 복사
# =============================================================================
echo -e "${YELLOW}[1/5] 템플릿 복사 중...${NC}"
mkdir -p "$PROJECTS_DIR"
cp -r "$TEMPLATE_DIR" "$PROJECT_DIR"
echo -e "${GREEN}  템플릿 복사 완료${NC}"

# =============================================================================
# 2. 플레이스홀더 치환
# =============================================================================
echo -e "${YELLOW}[2/5] 프로젝트명 적용 중...${NC}"

# 프로젝트명 변환
PROJECT_NAME_UPPER=$(echo "$PROJECT_NAME" | tr '[:lower:]' '[:upper:]' | tr '-' '_')
PROJECT_NAME_TITLE=$(echo "$PROJECT_NAME" | sed 's/-/ /g' | awk '{for(i=1;i<=NF;i++) $i=toupper(substr($i,1,1)) tolower(substr($i,2))}1')
PROJECT_NAME_SNAKE=$(echo "$PROJECT_NAME" | tr '-' '_')

# 모든 파일에서 플레이스홀더 치환
find "$PROJECT_DIR" -type f \( -name "*.py" -o -name "*.tsx" -o -name "*.ts" -o -name "*.jsx" -o -name "*.js" -o -name "*.json" -o -name "*.md" -o -name "*.html" -o -name "*.yml" -o -name "*.yaml" -o -name "*.toml" -o -name "*.env*" -o -name "Dockerfile" -o -name ".gitignore" \) | while read -r file; do
    if [ -f "$file" ]; then
        sed -i '' "s/__PROJECT_NAME__/$PROJECT_NAME/g" "$file" 2>/dev/null || true
        sed -i '' "s/__PROJECT_NAME_UPPER__/$PROJECT_NAME_UPPER/g" "$file" 2>/dev/null || true
        sed -i '' "s/__PROJECT_NAME_TITLE__/$PROJECT_NAME_TITLE/g" "$file" 2>/dev/null || true
        sed -i '' "s/__PROJECT_NAME_SNAKE__/$PROJECT_NAME_SNAKE/g" "$file" 2>/dev/null || true
        sed -i '' "s/__TIMESTAMP__/$TIMESTAMP/g" "$file" 2>/dev/null || true
        sed -i '' "s/__DATE__/$(date '+%Y-%m-%d')/g" "$file" 2>/dev/null || true
    fi
done

echo -e "${GREEN}  플레이스홀더 치환 완료${NC}"

# =============================================================================
# 3. Git 초기화
# =============================================================================
echo -e "${YELLOW}[3/5] Git 저장소 초기화 중...${NC}"
cd "$PROJECT_DIR"
git init -q
git add .
git commit -q -m "Initial commit: $PROJECT_NAME ($PROJECT_TYPE)

자동 생성됨 - $(date '+%Y-%m-%d %H:%M:%S')
템플릿: $PROJECT_TYPE"
echo -e "${GREEN}  Git 초기화 완료${NC}"

# =============================================================================
# 4. 의존성 설치 (선택적)
# =============================================================================
echo -e "${YELLOW}[4/5] 의존성 확인 중...${NC}"

INSTALL_DEPS=false
if [ -f "$PROJECT_DIR/backend/requirements.txt" ]; then
    echo -e "${CYAN}  Backend 의존성 발견 (requirements.txt)${NC}"
    if command -v pip &> /dev/null; then
        echo -e "  pip install은 수동으로 실행해주세요:"
        echo -e "    ${CYAN}cd $PROJECT_DIR/backend && pip install -r requirements.txt${NC}"
    fi
fi

if [ -f "$PROJECT_DIR/frontend/package.json" ]; then
    echo -e "${CYAN}  Frontend 의존성 발견 (package.json)${NC}"
    if command -v npm &> /dev/null; then
        echo -e "  npm install은 수동으로 실행해주세요:"
        echo -e "    ${CYAN}cd $PROJECT_DIR/frontend && npm install${NC}"
    fi
fi

echo -e "${GREEN}  의존성 확인 완료${NC}"

# =============================================================================
# 5. 완료
# =============================================================================
echo -e "${YELLOW}[5/5] 설정 파일 생성 중...${NC}"

# .env.example을 .env로 복사 (존재할 경우)
if [ -f "$PROJECT_DIR/backend/.env.example" ]; then
    cp "$PROJECT_DIR/backend/.env.example" "$PROJECT_DIR/backend/.env"
fi
if [ -f "$PROJECT_DIR/frontend/.env.example" ]; then
    cp "$PROJECT_DIR/frontend/.env.example" "$PROJECT_DIR/frontend/.env"
fi

echo -e "${GREEN}  설정 파일 생성 완료${NC}"

# =============================================================================
# 결과 출력
# =============================================================================
echo ""
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}  프로젝트 [$PROJECT_NAME] 생성 완료 ($PROJECT_TYPE)${NC}"
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo -e "경로: ${GREEN}$PROJECT_DIR${NC}"
echo ""

# 파일 수 계산
FILE_COUNT=$(find "$PROJECT_DIR" -type f | wc -l | tr -d ' ')
echo -e "생성된 파일: ${GREEN}${FILE_COUNT}개${NC}"
echo ""

echo -e "${YELLOW}실행 방법:${NC}"
echo ""

case "$PROJECT_TYPE" in
    api-only)
        echo -e "  ${CYAN}# Backend 실행${NC}"
        echo -e "  cd $PROJECT_DIR/backend"
        echo -e "  pip install -r requirements.txt"
        echo -e "  python main.py"
        echo ""
        echo -e "  ${CYAN}# API 문서${NC}"
        echo -e "  http://localhost:8000/docs"
        ;;
    fullstack|landing|saas)
        echo -e "  ${CYAN}# Backend 실행${NC}"
        echo -e "  cd $PROJECT_DIR/backend"
        echo -e "  pip install -r requirements.txt"
        echo -e "  python main.py"
        echo ""
        echo -e "  ${CYAN}# Frontend 실행 (새 터미널)${NC}"
        echo -e "  cd $PROJECT_DIR/frontend"
        echo -e "  npm install"
        echo -e "  npm run dev"
        echo ""
        echo -e "  ${CYAN}# 접속${NC}"
        echo -e "  Frontend: http://localhost:5173"
        echo -e "  Backend:  http://localhost:8000"
        echo -e "  API Docs: http://localhost:8000/docs"
        ;;
esac

echo ""
echo -e "${CYAN}다음 단계:${NC}"
echo "  1. backend/.env 파일에 환경변수 설정 (SUPABASE_URL, SUPABASE_KEY 등)"
echo "  2. Supabase에 스키마 적용 (supabase/schema.sql)"
echo "  3. 개발 시작!"
echo ""
