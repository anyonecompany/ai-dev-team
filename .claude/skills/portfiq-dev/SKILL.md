---
name: portfiq-dev
description: "Portfiq 프로젝트 작업 시 사용. projects/portfiq/ 하위 파일 수정, ETF, 브리핑, 포트폴리오, Gemini, 캐시 관련 작업 시 자동 트리거."
user-invocable: false
allowed-tools: Read, Write, Edit, Bash, Grep, Glob
---

# Portfiq 개발 스킬

## 현재 상태
!`git -C projects/portfiq log --oneline -5 2>/dev/null || echo "git log 불가"`
!`git -C projects/portfiq branch --show-current 2>/dev/null || echo "브랜치 확인 불가"`

## 상세 codemap
Read `.claude/knowledge/codemap-portfiq.md`

## 핵심 규칙

### 캐시 전략 (필수)
- 3-layer 캐시: in-memory TTL → Supabase → 외부 API
- 장중 15분 / 장외 6시간 Adaptive TTL (price_service.py)
- 브리핑은 스케줄러가 사전 생성 → API는 캐시에서만 반환
- 새 API 추가 시 반드시 cache_ttl.py에 TTL 상수 정의

### LLM 정책
- **Gemini 전용** — `google-genai` 패키지만 사용
- openai, anthropic 패키지 추가/import 절대 금지
- 기본 모델: `gemini-2.5-flash-lite` (config.py GEMINI_MODEL)

### Flutter 규칙
- 상태 관리: **Riverpod만** (Provider, Bloc 금지)
- 라우팅: GoRouter (선언형)
- 데이터 모델: Freezed + json_annotation
- 폰트: **Pretendard 전체 통일** (Inter 사용 금지, 숫자/영어 포함)
- 환경: Flavor 3단계 (local/qa/production) — main_*.dart

### 백엔드 규칙
- 새 라우터 추가 시 main.py에 `app.include_router()` 등록 필수
- 스케줄러 Job은 `_run_in_thread()`로 별도 스레드에서 실행
- Supabase 키: anon(클라이언트) / service(서버) 분리 — RLS 주의
- ETF 유니버스는 동적 — 절대 하드코딩 금지

### 비용 최적화 체크리스트
- [ ] 같은 ETF 뉴스를 여러 사용자가 공유하는가? (그룹 공유)
- [ ] 번역은 배치로 처리하는가? (개별 호출 금지)
- [ ] 캐시 TTL이 적절한가? (장중/장외 분리)
- [ ] 불필요한 외부 API 호출이 없는가?

## Gotchas
- yfinance: 과도한 호출 시 rate limit. 배치 조회 활용
- Supabase Edge Function: Deno 런타임 — Node.js API 사용 불가
- Flutter 빌드: `flutter pub run build_runner build` 후 테스트
- 어드민 Next.js: Pretendard 폰트 미전환 상태 (미해결)

## References
- [cache-architecture.md](references/cache-architecture.md)
- [api-conventions.md](references/api-conventions.md)
- [cost-optimization.md](references/cost-optimization.md)
