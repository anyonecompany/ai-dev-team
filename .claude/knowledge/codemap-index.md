# Codemap 인덱스

> 새 세션 시작 시 이 파일을 먼저 로드하여 필요한 codemap을 선택하라.

| 프로젝트 | 파일 | 갱신일 | 상태 |
|---|---|---|---|
| Portfiq (포트픽) | [codemap-portfiq.md](codemap-portfiq.md) | 2026-03-23 | 활성 |
| La Paz 계열 (la-paz, lapaz-live, lapaz-crawl) | [codemap-lapaz.md](codemap-lapaz.md) | 2026-03-23 | 활성 |
| 기타 (adaptfitai, foundloop, 서로연, tactical-gnn, integrations 등) | [codemap-others.md](codemap-others.md) | 2026-03-23 | 참고용 |

## 사용법

```
# 특정 프로젝트 작업 시
Read .claude/knowledge/codemap-portfiq.md

# 전체 파악 시
Read .claude/knowledge/codemap-index.md → 필요한 codemap 선택
```

## 갱신 규칙

- 대규모 리팩토링/기능 추가 후 `/codemap-update` 실행
- 갱신일이 7일 이상 지나면 재확인 필요
