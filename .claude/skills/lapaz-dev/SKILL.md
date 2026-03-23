---
name: lapaz-dev
description: "La Paz 계열 프로젝트 작업 시 사용. projects/la-paz, lapaz-live, lapaz-crawl 하위 파일 수정, 축구, RAG, 실시간 Q&A 관련 작업 시 자동 트리거."
user-invocable: false
allowed-tools: Read, Write, Edit, Bash, Grep, Glob
---

# La Paz 개발 스킬

## 현재 상태
!`git log --oneline -5 -- projects/la-paz projects/lapaz-live 2>/dev/null || echo "git log 불가"`
!`git branch --show-current 2>/dev/null || echo "브랜치 확인 불가"`

## 상세 codemap
Read `.claude/knowledge/codemap-lapaz.md`

## 프로젝트 관계

```
la-paz (메인) ─────────────────────────────────────────┐
  └─ 5-Domain Agent 파이프라인, Supabase, Next.js       │
                                                        │ 같은 Supabase 인스턴스 공유
lapaz-crawl (데이터 수집) ──── documents 테이블 적재 ────┤
                                                        │
lapaz-live (실시간 Q&A) ──── documents 테이블 검색 ─────┘
  └─ la-paz RAG 코어 추출/경량화, Fly.io+Vercel 배포
```

## 핵심 규칙

### LLM 정책
- **Gemini 전용** (lapaz-live, lapaz-crawl)
- la-paz 메인은 DeepSeek V3.2 사용 중 (별도 관리)
- openai 패키지: la-paz에서 DeepSeek용 OpenAI SDK로 사용 (직접 OpenAI API 아님)

### RAG 파이프라인 (lapaz-live)
```
질문 → Gemini Flash 분류 (7카테고리)
     → pgvector 하이브리드 검색 (키워드 + 시맨틱)
     → 구조화 컨텍스트 조합
     → Gemini 2.5 Flash 답변 생성
```

### 배포
- lapaz-live BE: Fly.io (단일 인스턴스 — SQLite 제약)
- lapaz-live FE: Vercel
- 후속 필요: Supabase 마이그레이션 (다중 인스턴스 지원)

### 크롤러 (lapaz-crawl)
- 나무위키 MUN/AVL 선수 프로필 크롤링
- GitHub Actions daily_crawl.yml로 매일 자동 실행
- 데이터 → Supabase documents 테이블 적재

## Gotchas
- src/ 코드가 lapaz-crawl과 lapaz-live에 중복 존재 (별도 관리)
- SQLite: 다중 인스턴스 스케일 아웃 불가 → Supabase 마이그레이션 필요
- lapaz-live에 README.md/CLAUDE.md 없음 (이번 업그레이드에서 추가 예정)
- few_shot_examples.json: 분류기 성능에 직접 영향 — 신중하게 수정

## References
- [system-architecture.md](references/system-architecture.md)
