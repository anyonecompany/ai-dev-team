---
name: context-compact
description: "컨텍스트 한계 도달 전 세션 상태 저장 및 요약. /session-save 실행 시, 컨텍스트 50% 이하 감지 시 사용."
user-invocable: false
---

# Context Compact

컨텍스트 한계 도달 전 세션 상태를 저장하고 요약한다.

## 트리거
- 컨텍스트 잔여량 50% 이하 감지 시
- 사용자가 `/session-save` 실행 시
- 긴 태스크의 체크포인트 도달 시

## 실행 절차

### 1. 세션 요약 파일 생성
파일명: `.claude/handoff/session-{YYYY-MM-DD-HHMM}.md`

포함 내용:
- **현재 작업 중인 태스크** (프로젝트명, 태스크 ID)
- **완료된 항목** (검증 증거 포함 — 테스트 통과, 빌드 성공 등)
- **시도했으나 실패한 접근법** (이유와 함께)
- **다음 단계** (구체적 파일명, 함수명 포함)
- **열려있는 이슈/미결정 사항**
- **관련 파일 경로** (새 세션에서 빠르게 로드할 수 있도록)

### 2. 코드맵 갱신
변경된 파일이 있으면 해당 프로젝트의 codemap 업데이트

### 3. 사용자에게 보고
"세션 저장 완료: .claude/handoff/session-{timestamp}.md
새 세션에서: /session-restore {timestamp} 실행"

## 새 세션 복원 방법
새 대화 시작 시 파일 경로만 제공하면 됨:
"이어서 진행해줘: .claude/handoff/session-{timestamp}.md"
