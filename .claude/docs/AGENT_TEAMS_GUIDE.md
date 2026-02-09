# Agent Teams 실행 가이드

> 버전: 1.0.0
> 최종 갱신: 2026-02-09

Claude Code 내장 Agent Teams 기능을 사용하여 여러 에이전트가 동시에 협업하는 실용 가이드.

---

## 1. 사전 준비

### tmux 설치

```bash
# macOS
brew install tmux

# Ubuntu/Debian
sudo apt install tmux
```

### 설정 확인

`settings.local.json`에 다음이 포함되어 있어야 한다:

```json
{
  "env": {
    "CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS": "1"
  }
}
```

---

## 2. 팀 실행 절차

### Step 1: tmux 세션 시작
```bash
tmux new -s dev
```

### Step 2: Claude Code 실행
```bash
cd ~/ai-dev-team
claude
```

### Step 3: 팀 프로젝트 지시

자연어로 팀 구성과 프로젝트를 지시한다:

```
에이전트 팀을 구성해서 React와 FastAPI로 todo 앱을 만들어줘.

팀 구성:
1. PM-Planner: 요구사항 분석 후 태스크 분해
2. Architect: 시스템 설계, API/DB 스키마
3. BE-Developer: FastAPI 백엔드 구현
4. FE-Developer: React/TypeScript 프론트엔드 구현
5. QA-DevOps: 린트, 타입체크, 테스트, 빌드 검증

규칙:
- projects/ 하위에 프로젝트 폴더 생성
- 각 팀원은 plan approval 후 구현 시작
- BE와 FE는 Architect 설계 완료 후 병렬 진행
- QA는 구현 완료 후 실행
```

### Step 4: 팀원 모니터링

tmux 분할 화면에서 각 팀원의 작업을 실시간으로 확인할 수 있다.

---

## 3. tmux 기본 조작법

| 조작 | 키 | 설명 |
|------|-----|------|
| 새 세션 | `tmux new -s dev` | 이름 지정 세션 생성 |
| 세션 분리 | `Ctrl+b d` | 세션 유지한 채 나가기 |
| 세션 복귀 | `tmux attach -t dev` | 기존 세션으로 돌아가기 |
| 패널 전환 | `Ctrl+b 방향키` | 분할된 패널 간 이동 |
| 세션 종료 | `exit` 또는 `Ctrl+d` | 현재 패널 종료 |
| 세션 목록 | `tmux ls` | 활성 세션 목록 확인 |

---

## 4. 팀 규모별 프롬프트 예시

### 풀스택 프로젝트 (5인)
```
에이전트 팀을 구성해서 {프로젝트 설명}을 만들어줘.

팀:
1. PM-Planner: 요구사항 분석, 태스크 분해
2. Architect: 시스템 설계, API/DB 스키마
3. BE-Developer: FastAPI 백엔드
4. FE-Developer: React/TypeScript 프론트엔드
5. QA-DevOps: 테스트 및 검증

projects/ 하위에 생성. plan approval 필수.
```

### 백엔드 전용 (3인)
```
에이전트 팀으로 {API 설명} 백엔드를 개발해줘.

팀:
1. Architect: API/DB 설계
2. BE-Developer: FastAPI 구현
3. QA-DevOps: 테스트

projects/ 하위에 생성.
```

### 프론트엔드 전용 (3인)
```
에이전트 팀으로 {UI 설명} 프론트엔드를 개발해줘.

팀:
1. Designer: UI/UX 설계, 컴포넌트 구조
2. FE-Developer: React/TypeScript 구현
3. QA-DevOps: 린트, 타입체크, 빌드

projects/ 하위에 생성.
```

### 코드 리뷰 (3인)
```
에이전트 팀으로 {대상 경로} 코드 리뷰를 진행해줘.

팀:
1. Security 리뷰어: 보안 취약점, OWASP Top 10
2. Quality 리뷰어: 코드 품질, 테스트 커버리지
3. Performance 리뷰어: 성능 병목, 비동기 패턴

각자 독립적으로 리뷰 후 결과를 리드에게 보고.
```

### 버그 조사 (3인)
```
에이전트 팀으로 {버그 설명}을 조사해줘.

팀:
1. 조사원 A: {가설 1} 방향 조사
2. 조사원 B: {가설 2} 방향 조사
3. 조사원 C: {가설 3} 방향 조사

서로 메시지를 주고받으며 가설을 검증하고 반박해.
```

---

## 5. 파이프라인 흐름

```
[PM-Planner] 요구사항 분석 + 태스크 분해
       ↓
[Architect] 시스템 설계 + API/DB 스키마
       ↓
[BE-Developer] ──병렬──→ [FE-Developer]
  백엔드 구현              프론트엔드 구현
       ↓                       ↓
       └───────────┬───────────┘
                   ↓
[QA-DevOps] ──병렬──→ [Security-Developer]
  린트/테스트/빌드       보안 감사
                   ↓
[리드] 통합 + Monday/Slack 보고 + Git push
```

---

## 6. 파일 소유권 규칙

팀원 간 파일 충돌을 방지하기 위해 각 에이전트는 지정된 디렉토리만 수정한다:

| 에이전트 | 소유 디렉토리 | 비고 |
|---------|-------------|------|
| BE-Developer | `backend/`, `api/`, `models/`, `services/`, `migrations/` | 서버 코드 |
| FE-Developer | `frontend/`, `src/`, `components/`, `pages/`, `hooks/` | 클라이언트 코드 |
| AI-Engineer | `ai/`, `ml/`, `prompts/`, `pipelines/` | AI/ML 코드 |
| QA-DevOps | `tests/`, `__tests__/`, `cypress/`, `.github/` | 테스트/CI |
| Architect | `docs/`, 루트 설정 파일 (`package.json`, `pyproject.toml` 등) | 설계 문서 |
| Designer | `design/`, `assets/`, `styles/` | 디자인 리소스 |

**공유 파일** (README.md, .gitignore 등)은 리드가 관리한다.

---

## 7. Monday.com / Slack 연동

Agent Teams에서 Monday.com/Slack 연동은 **리드(Orchestrator)**가 처리한다:

```python
# 리드가 프로젝트 시작 시 실행
import asyncio, sys, os
sys.path.insert(0, os.path.expanduser("~/ai-dev-team"))
from dotenv import load_dotenv; load_dotenv(os.path.expanduser("~/ai-dev-team/.env"))

from integrations.monday.monday_sync import create_project, log_agent_activity
from integrations.slack.slack_notifier import notify_project_created

asyncio.run(create_project("프로젝트명", description="설명"))
asyncio.run(notify_project_created("프로젝트명"))
```

---

## 8. 트러블슈팅

### 팀원이 멈춘 경우
- 리드에서 해당 팀원에게 메시지: "현재 상태를 보고해줘"
- 응답 없으면 팀원 종료 후 새로 생성

### 파일 충돌 발생
- 같은 파일을 두 팀원이 수정한 경우 → 리드가 충돌 해결
- 예방: 프롬프트에서 파일 소유권을 명확히 지정

### 작업이 태스크 목록에서 완료 안 됨
- 리드가 수동으로 팀원에게 "태스크를 완료로 표시해줘" 지시

### 팀원이 다른 영역 파일 수정
- 에이전트 프로필의 "금지 사항"에 따라 해당 변경 롤백 지시

### 비용이 너무 높음
- 팀 규모 축소 (5인 → 3인)
- 단순 작업은 팀 없이 단독 실행
- plan approval 모드로 불필요한 작업 사전 차단

---

## 9. 베스트 프랙티스

1. **태스크를 5~6개로 제한**: 팀원당 적절한 작업량 유지
2. **파일 충돌 방지**: 프롬프트에서 각 팀원의 담당 디렉토리 명시
3. **plan approval 활용**: 구현 전 설계를 리드가 승인
4. **delegate 모드**: 리드는 코드 작성 대신 조율에 집중
5. **의존성 명시**: "BE 완료 후 FE 시작" 등 순서 지정
6. **점진적 확장**: 처음엔 2~3인 팀부터 시작
