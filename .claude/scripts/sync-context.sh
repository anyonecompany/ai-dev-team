#!/bin/bash
#
# sync-context.sh — COMPACT_CONTEXT.md 자동 갱신 스크립트
# 실행: bash .claude/scripts/sync-context.sh
#

set -e

# 경로 설정
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
CLAUDE_DIR="$(dirname "$SCRIPT_DIR")"
PROJECT_ROOT="$(dirname "$CLAUDE_DIR")"

CLAUDE_MD="$CLAUDE_DIR/CLAUDE.md"
PRINCIPLES_MD="$CLAUDE_DIR/docs/OPERATING_PRINCIPLES.md"
TODO_MD="$CLAUDE_DIR/tasks/TODO.md"
DECISIONS_MD="$CLAUDE_DIR/context/decisions-log.md"
HANDOFF_MD="$CLAUDE_DIR/handoff/current.md"
OUTPUT_MD="$CLAUDE_DIR/context/COMPACT_CONTEXT.md"

# 현재 시간
TIMESTAMP=$(date "+%Y-%m-%d %H:%M")

# 버전 추출
CLAUDE_VERSION="unknown"
PRINCIPLES_VERSION="unknown"
if [ -f "$CLAUDE_MD" ]; then
    CLAUDE_VERSION=$(grep -m1 "버전:" "$CLAUDE_MD" | sed 's/.*버전: *//' | tr -d ' ')
fi
if [ -f "$PRINCIPLES_MD" ]; then
    PRINCIPLES_VERSION=$(grep -m1 "버전:" "$PRINCIPLES_MD" | sed 's/.*버전: *//' | tr -d ' ')
fi

# 프로젝트 정보 추출
PROJECT_NAME="AI Development Team Platform"
PROJECT_STAGE="MVP 완료 / 고도화 진행 중"
PROJECT_VER="v0.2.0"
if [ -f "$CLAUDE_MD" ]; then
    PROJECT_NAME=$(grep -A1 "| 이름" "$CLAUDE_MD" 2>/dev/null | tail -1 | awk -F'|' '{print $3}' | xargs || echo "$PROJECT_NAME")
    PROJECT_STAGE=$(grep -A1 "| 현재 단계" "$CLAUDE_MD" 2>/dev/null | tail -1 | awk -F'|' '{print $3}' | xargs || echo "$PROJECT_STAGE")
    PROJECT_VER=$(grep -A1 "| 버전" "$CLAUDE_MD" 2>/dev/null | tail -1 | awk -F'|' '{print $3}' | xargs || echo "$PROJECT_VER")
fi

# TODO 상태 집계
TODO_COUNT=0
IN_PROGRESS_COUNT=0
BLOCKED_COUNT=0
NEXT_TASKS=""
if [ -f "$TODO_MD" ]; then
    TODO_COUNT=$(grep -c "^### TASK-" "$TODO_MD" 2>/dev/null || echo "0")
    NEXT_TASKS=$(grep "^### TASK-" "$TODO_MD" 2>/dev/null | head -2 | sed 's/^### /  - /' || echo "  - 없음")
fi
if [ -d "$CLAUDE_DIR/tasks/IN_PROGRESS" ]; then
    IN_PROGRESS_COUNT=$(find "$CLAUDE_DIR/tasks/IN_PROGRESS" -name "*.md" 2>/dev/null | wc -l | xargs)
fi
if [ -d "$CLAUDE_DIR/tasks/BLOCKED" ]; then
    BLOCKED_COUNT=$(find "$CLAUDE_DIR/tasks/BLOCKED" -name "*.md" 2>/dev/null | wc -l | xargs)
fi

# 최근 결정 3건 추출
RECENT_DECISIONS=""
if [ -f "$DECISIONS_MD" ]; then
    RECENT_DECISIONS=$(grep -E "^## (DEC-|###)" "$DECISIONS_MD" 2>/dev/null | head -6 | sed 's/^## /1. **/' | sed 's/^### /2. **/' | sed 's/$/**/' | head -3 || echo "- 없음")
fi

# 핸드오프 요약 추출
HANDOFF_SUMMARY="없음"
if [ -f "$HANDOFF_MD" ]; then
    HANDOFF_SUMMARY=$(head -20 "$HANDOFF_MD" 2>/dev/null | grep -A1 "작업:" | tail -1 | xargs || echo "없음")
fi

# Git 상태
GIT_CHANGED=0
if command -v git &> /dev/null && [ -d "$PROJECT_ROOT/.git" ]; then
    GIT_CHANGED=$(cd "$PROJECT_ROOT" && git status --porcelain 2>/dev/null | wc -l | xargs)
fi

# COMPACT_CONTEXT.md 생성
cat > "$OUTPUT_MD" << ENDOFFILE
# ⚡ 컴팩트 컨텍스트 (자동 생성)
> 최종 갱신: $TIMESTAMP
> 원본: CLAUDE.md $CLAUDE_VERSION + OPERATING_PRINCIPLES $PRINCIPLES_VERSION

## 프로젝트 정체성
**$PROJECT_NAME** — 가상 AI 에이전트 팀이 협업하여 소프트웨어를 개발하는 플랫폼.
현재 단계: $PROJECT_STAGE ($PROJECT_VER)

## 기술 스택
- **Backend**: Python 3.11+ / FastAPI / aiofiles / structlog / tenacity
- **Frontend**: React 18+ / TypeScript / Vite / Zustand / Tailwind CSS
- **DB**: Supabase (PostgreSQL)
- **AI**: Claude (Opus 4.5, Sonnet 4.5, Haiku 4.5) + Gemini 2.0

## 에이전트 테이블
| 에이전트 | 역할 | 모델 | 핵심 권한 |
|---------|------|------|----------|
| PM-Planner | 요구사항 분석, 태스크 생성 | Opus 4.5 | 요구사항 정의, 태스크 생성 |
| Architect | 시스템 설계, API/DB 스키마 | Opus 4.5 | 아키텍처 결정, 스키마 승인 |
| Designer | UI/UX 설계 | Gemini 2.0 + Sonnet | 디자인 시안, 컴포넌트 설계 |
| BE-Developer | 백엔드 구현 | Sonnet 4.5 | API/서비스 코드 작성 |
| FE-Developer | 프론트엔드 구현 | Sonnet 4.5 | UI 컴포넌트 코드 작성 |
| AI-Engineer | ML/AI 기능 구현 | Sonnet 4.5 | AI 모델 연동, 프롬프트 설계 |
| QA-DevOps | 테스트, 배포, CI/CD | Haiku 4.5 | 테스트 실행, 배포 승인 |
| Orchestrator | 작업 분배, 상태 관리 | Sonnet 4.5 | 태스크 할당, 충돌 해결 |
| Security-Developer | 보안 감사, 취약점 분석 | Sonnet 4.5 | 보안 태스크 생성, 코드 리뷰 |

## 핵심 규칙 (Top 10)
1. **COMPACT_CONTEXT.md 먼저 읽기** — 상세 필요 시만 원본 참조
2. **다른 에이전트 담당 영역 임의 수정 금지**
3. **테스트 없이 "완료" 선언 금지**
4. **TODO.md 외 작업 임의 진행 금지**
5. **Security-Developer 승인 없이 인증/인가 로직 변경 금지**
6. **보안 스캔 미실행 상태로 릴리즈 금지**
7. **.env 파일 커밋 금지, 민감 정보 하드코딩 금지**
8. **코드 변경 후 보안 검증 요청 필수**
9. **복잡도 M 이상은 팀 설계 회의 필수**
10. **Self-QA 5단계 (정적분석→테스트→보안→성능→종합) 통과 후 납품**

## 현재 스프린트 상태
- **TODO**: ${TODO_COUNT}건
- **진행중**: ${IN_PROGRESS_COUNT}건
- **블로커**: ${BLOCKED_COUNT}건
- **Git 변경**: ${GIT_CHANGED}개 파일
- **다음 우선**:
$NEXT_TASKS

## 최근 핸드오프
$HANDOFF_SUMMARY

## 상세 참조
- 전체 헌장: \`.claude/CLAUDE.md\`
- 운영 원칙: \`.claude/docs/OPERATING_PRINCIPLES.md\`
- 에이전트 프로필: \`.claude/agents/[에이전트명].md\`
- 태스크: \`.claude/tasks/TODO.md\`
- 결정 로그: \`.claude/context/decisions-log.md\`
ENDOFFILE

# 토큰 수 추정 (문자 수 / 4)
CHAR_COUNT=$(wc -c < "$OUTPUT_MD" | xargs)
TOKEN_EST=$((CHAR_COUNT / 4))
LINE_COUNT=$(wc -l < "$OUTPUT_MD" | xargs)

echo "✅ 컴팩트 컨텍스트 갱신 완료 — ${LINE_COUNT}줄, 약 ${TOKEN_EST} 토큰"
