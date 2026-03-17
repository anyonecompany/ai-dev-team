# /session-restore [timestamp or filepath]

저장된 세션 상태를 로드하여 작업을 이어갑니다.

## 사용법
- `/session-restore` — 가장 최근 세션 파일 자동 로드
- `/session-restore 2025-01-20-1430` — 특정 타임스탬프 세션 로드
- `/session-restore path/to/file.md` — 직접 경로 지정

## 실행 순서
1. `.claude/handoff/` 에서 해당 세션 파일 로드
2. `.claude/knowledge/codemap.md` 로드 (있을 경우)
3. "완료됨", "다음 단계", "미결 이슈" 섹션 요약 보고
4. "어디서부터 이어갈까요?" 확인 후 즉시 작업 재개
