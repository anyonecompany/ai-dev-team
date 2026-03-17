# /codemap-update [project-name]

코드베이스 네비게이션 맵을 생성하거나 갱신합니다.
새 세션에서 탐색 컨텍스트 소비를 줄이기 위해 사용합니다.

## 사용법
- `/codemap-update` — 현재 프로젝트 자동 감지 후 갱신
- `/codemap-update la-paz` — 특정 프로젝트 코드맵 생성

## 실행
`codemap-update` 스킬 실행:
1. `projects/{name}/` 구조 스캔
2. 진입점, 핵심 모듈, API 맵, DB 스키마 추출
3. `.claude/knowledge/codemap-{project}.md` 저장
4. 기존 파일 있으면 diff 후 갱신된 항목만 보고
