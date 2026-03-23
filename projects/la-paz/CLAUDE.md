# CLAUDE.md

## 프로젝트 정체성

**La-Paz는 글로벌 축구 팬 인텔리전스 플랫폼이다.**

- 축구 특화 LLM 서비스
- 구조화 데이터 기반 RAG 시스템
- 팬 행동 데이터 집계 플랫폼

La-Paz의 장기 자산은 모델이 아니라  
**구조화된 팬 수요 데이터**이다.

---

# 1. 사업 방향

## Phase 1 — 무료 팬 서비스
목표: 사용자 확보 + 질의 데이터 축적

## Phase 2 — 구독 확장
고급 분석 및 신뢰도 강화

## Phase 3 — B2B 집계 상품화
익명화된 팬 수요 지표 제공

❗ 원칙:
- 개인 단위 데이터 판매 금지
- 익명화된 집계 데이터만 상업화

---

# 2. 시스템 정체성

La-Paz는 다음이 아니다:

- 커스텀 ML 연구 플랫폼
- 전술 GNN 실험 프로젝트
- 대규모 모델 학습 인프라

La-Paz는 다음이다:

- 축구 특화 LLM 서비스
- 사실 기반 RAG 시스템
- 팬 수요 인텔리전스 플랫폼

---

# 3. 핵심 아키텍처 원칙

User Query  
→ Intent Classification  
→ Structured Retrieval  
→ LLM Reasoning  
→ Source-aware Response  
→ Fan Analytics Logging  

### 금지 사항
- Retrieval 없이 통계 생성 금지
- LLM 단독 추론 기반 수치 생성 금지
- 환각 허용 불가

---

# 4. 팬 데이터 로깅 원칙

모든 질의는 구조화되어 저장되어야 한다.

저장 원칙:

- 사용자 식별 정보는 반드시 익명화
- 원문 질의 보존
- 언어 정보 보존
- 의도(Intent) 분류 기록
- 리그/엔티티 태그 기록
- 응답 품질 메타데이터 기록

로그 저장 실패 시 요청은 완료로 간주하지 않는다.

---

# 5. 다국어 원칙

- 사실 데이터는 canonical 형식으로 저장
- 응답은 사용자 언어에 맞춰 렌더링
- 언어 확장은 구조 변경 없이 가능해야 한다
- 엔티티 별칭은 구조화된 방식으로 관리

---

# 6. 글로벌 확장 원칙

- 리그 확장은 단계적으로 진행한다
- 확장은 데이터 밀도와 팬 수요 기반으로 결정한다
- 리그 종속 코드 작성 금지
- 리그 정보는 단일 레지스트리에서 관리한다
- Tier 1 데이터 완성 전 상위 확장 금지

상세 티어 구성 및 구현 전략은  
`docs/fan_intelligence_architecture.md`에서 관리한다.

---

# 7. RAG 품질 기준

다음은 시스템 불안정 신호이다:

- fallback 비율 급증
- 구조화 통계 데이터 누락
- 벡터 검색 실패율 증가

모든 배포 전 RAG 안정성 검증 필수.

---

# 8. 도메인 신뢰성 원칙

모든 통계는 구조화된 데이터 기반이어야 한다.

데이터가 없을 경우:
명확히 “데이터 없음”을 선언한다.

환각 허용 불가.

---

# 9. 팬 인텔리전스 철학

La-Paz의 핵심 가치는:

팬 → 질의 → 구조화 → 집계 → 인사이트

이다.

B2B는 판매가 목적이 아니라  
**팬 수요를 구조화한 결과물**이다.

---

# 10. 코드 및 품질 원칙

- 타입 안정성 유지
- 테스트 필수
- 시크릿 하드코딩 금지
- 환경 변수 관리 준수
- 파일 단위 책임 분리

---

# 11. Definition of Done

기능은 다음을 만족해야 완료:

- 글로벌 확장 구조 유지
- 팬 로그 정상 저장
- RAG 근거 유지
- 개인정보 보호 준수
- 테스트 포함

---

# 12. 장기 목표

La-Paz는 궁극적으로:

Global Football Intelligence Infrastructure

가 되는 것을 목표로 한다.

모든 개발은 이 방향을 벗어나지 않는다.

---

# 13. 기술 스택 (실제 코드 기반)

### 백엔드 (Python)
- FastAPI, uvicorn, pydantic
- openai SDK (DeepSeek V3.2 / Gemini 게이트웨이)
- supabase (PostgreSQL — 벡터 저장소 포함)
- sentence-transformers (임베딩)
- soccerdata, statsbombpy, understatapi (축구 데이터)
- feedparser, ddgs (뉴스/웹 검색)
- pandas, scikit-learn

### 프론트엔드 (Next.js)
- TypeScript, Tailwind CSS
- 국제화 (messages/ 디렉토리)
- Playwright E2E 테스트

### 데이터
- `data/raw/` — 원시 수집 데이터
- `data/processed/` — 가공 데이터
- `ai/vectorstore/` — 벡터 인덱스
- `evaluation/` — RAG 평가 결과

### 스크립트
- `scripts/daily_crawl.py` — 일일 데이터 수집
- `scripts/generate_transfer_rumors.py` — 이적 루머 생성

---

# 14. 수정 금지 영역

- `ai/vectorstore/` — 벡터 인덱스 파일. 재빌드 스크립트로만 갱신
- `data/processed/` — 가공 완료 데이터. 수동 편집 금지
- `evaluation/` — 평가 결과 아카이브. 덮어쓰기 금지 (히스토리 보존)
- `supabase/` — DB 설정/마이그레이션. 기존 파일 수정 금지
- `docs/fan_intelligence_architecture.md` — 티어/확장 전략 문서. 비즈니스 승인 없이 변경 금지

---

# 15. 자주 하는 실수

1. **리그 종속 코드 작성** — 특정 리그(EPL 등)에 하드코딩된 로직 작성. 글로벌 확장 원칙 위반. 리그 정보는 레지스트리에서 관리
2. **LLM 단독 통계 생성** — Retrieval 없이 "~골, ~어시스트" 등 수치를 LLM이 생성. 환각 원인. 반드시 구조화 데이터 기반
3. **팬 로그 저장 누락** — 질의 처리 성공 후 로그 저장을 빼먹으면 팬 인텔리전스 데이터 유실. 로그 저장 실패 = 요청 미완료
4. **openai SDK 의존** — requirements.txt에 openai SDK가 존재하지만, 이는 DeepSeek/Gemini 호환 게이트웨이용. 실제 OpenAI API 호출은 금지 (전 프로젝트 Gemini 정책)
5. **벡터 인덱스 무검증 배포** — 벡터스토어 갱신 후 RAG 안정성 검증 없이 배포하면 fallback 비율 급증