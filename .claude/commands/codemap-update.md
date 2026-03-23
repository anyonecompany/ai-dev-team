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

## 자동 갱신 로직

### 프로젝트 감지
인자가 있으면 해당 프로젝트만, 없으면 신선도 체크 후 오래된 것만 갱신:
```bash
./scripts/codemap-freshness.sh
```

### 갱신 범위
- 디렉토리 맵: 실제 파일 구조 재스캔
- 핵심 진입점: 변경된 파일 기준으로 업데이트
- 최근 변경 이력: git log -15 재생성
- Gotchas: 에이전트 메모리 + knowledge/mistakes에서 추가 반영

### 갱신 후
- codemap-index.md의 갱신일 업데이트
- `git commit -m "chore: refresh codemap for {프로젝트} $(date +%Y-%m-%d)"`
