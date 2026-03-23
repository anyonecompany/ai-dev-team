# La Paz Live — 에이전트 지시서

## 프로젝트 개요

La Paz Live는 실시간 축구 팬 Q&A 서비스다. 사용자가 축구 관련 질문을 하면 RAG 파이프라인(Intent Classification → Structured Retrieval → LLM Generation)으로 근거 기반 답변을 생성한다. FastAPI(백엔드, RAG 포함) + Next.js(프론트엔드)로 구성. 배포는 Fly.io(백엔드 1대, 512MB) + Vercel(프론트엔드). Phase 1 라이브 테스트 완료 (2026-03-15 맨유 vs 아스톤빌라전).

## 기술 스택

### 백엔드 (Python 3.11+)
- FastAPI, uvicorn, httpx
- google-genai (Gemini — LLM 생성)
- voyageai (벡터 임베딩)
- supabase (PostgreSQL — pgvector 벡터 검색)
- aiosqlite (질문 로그 로컬 저장)
- beautifulsoup4, selenium (크롤링 파이프라인)
- python-dotenv
- Fly.io 배포 (Docker)

### 프론트엔드 (Next.js 16)
- React 19, TypeScript
- Tailwind CSS 4, lucide-react
- Vercel 배포

### RAG 파이프라인 (`src/rag/`)
- Classifier: 질문 의도 분류 (축구/일반/잡담)
- Retriever: Supabase pgvector + 키워드 하이브리드 검색 (RRF 병합)
- Structured Context: 검색 결과를 구조화된 컨텍스트로 변환
- Generator: Gemini 기반 답변 생성 (스트리밍 지원)
- 프롬프트: `src/rag/prompts/` (classifier_prompt.txt, system_prompt.txt, few_shot_examples.json)
- 선수 이름 매핑: `src/rag/data/player_names.json`

### 외부 데이터
- football-data.org (순위, 경기 정보 — 무료 티어)
- API-Football (라이브 이벤트 전용)

## 아키텍처 핵심 원칙

1. **RAG 근거 없이 통계 생성 금지** — LLM 단독 추론 기반 수치는 환각이다. 데이터 없으면 "데이터 없음" 선언
2. **질문은 모두 구조화 저장** — 의도(intent), 카테고리, 신뢰도, 응답 시간 기록. 로그 저장 실패 시 요청 미완료 처리
3. **컨텍스트 품질 평가 3단계** — `none` (문서 0건), `low` (유사도 0.3 미만), `sufficient`. 품질별 다른 프롬프트 전략 적용
4. **Gemini만 사용** — Anthropic/OpenAI 절대 금지 (Claude → Gemini 전환 완료)
5. **Docker 구조** — `backend/`와 `src/`를 모두 컨테이너에 복사. `config.py`에서 `sys.path`에 RAG src 디렉토리 추가
6. **축구가 아닌 질문도 처리** — Classifier가 `force_football=False`일 때 일반/잡담 판별. 축구 외 질문은 짧은 일반 응답

## 작업 시 규칙

1. **프롬프트 수정은 `src/rag/prompts/`에서만** — `classifier_prompt.txt`, `system_prompt.txt`, `few_shot_examples.json`. 코드 내 프롬프트 하드코딩 금지
2. **선수 이름 매핑은 `src/rag/data/player_names.json`** — 선수 이름 변환 로직 수정 시 이 파일만 갱신
3. **에러 로그는 별도 테이블** — `backend/routers/errors.py` + `services/error_log_service.py`. 파이프라인 실패를 DB에 기록
4. **SQLite는 임시 저장소** — Fly.io에서는 `/tmp/questions.db` 사용 (다중 인스턴스 시 유실). Supabase 마이그레이션 예정
5. **캐시 워밍업** — 서버 시작 시 football-data.org 데이터 프리페치 (Fly.io에서는 비활성화: `ENABLE_STARTUP_WARMUP=0`)
6. **JSON 구조화 로깅** — `rag/logging_utils.py`에서 전역 설정. request_id 기반 추적

## 수정 금지 영역

- `src/rag/prompts/` — 프롬프트 변경은 성능에 직접 영향. A/B 테스트 없이 변경 금지
- `src/rag/pipeline.py`의 컨텍스트 품질 평가 임계값 (0.3) — 튜닝된 값이므로 근거 없이 변경 금지
- `fly.toml` — 배포 설정. `auto_stop_machines=false`, `min_machines_running=1` 변경 시 서비스 중단
- `backend/migrations/` — 기존 마이그레이션 수정 금지. 신규만 추가
- `Dockerfile`의 COPY 순서 — `backend`, `src`, `data` 순서가 바뀌면 RAG 파이프라인 경로 오류

## 테스트/검증 명령어

```bash
# 백엔드 린트
cd projects/lapaz-live/backend && python3 -m ruff check .

# RAG 파이프라인 테스트
cd projects/lapaz-live && python3 -m pytest tests/

# 드라이런 테스트 (실제 API 호출)
cd projects/lapaz-live && python3 -m pytest tests/dryrun_test.py -v

# Generator 단위 테스트
cd projects/lapaz-live && python3 -m pytest tests/test_generator.py -v

# 파이프라인 디그레이데이션 테스트
cd projects/lapaz-live && python3 -m pytest tests/test_pipeline_degradation.py -v

# 백엔드 로컬 실행
cd projects/lapaz-live/backend && uvicorn main:app --host 0.0.0.0 --port 8080 --reload

# 프론트엔드 로컬 실행
cd projects/lapaz-live/frontend && npm run dev
```

## 자주 하는 실수 (git log 기반)

1. **RAG src 경로 누락** — `config.py`에서 `sys.path.insert(0, RAG_SRC_DIR)` 빠지면 `from rag.pipeline import ask` 실패. Docker 빌드 시에도 `COPY src /app/src` 필수
2. **SQLite 다중 인스턴스 문제** — Fly.io 스케일아웃 시 각 인스턴스에 별도 SQLite 생성. 질문 데이터 유실 원인. Supabase 전환 필요
3. **football-data.org 팀 ID 하드코딩** — `config.py`에 `MANUTD_FD_ID=66`, `VILLA_FD_ID=58` 등 특정 경기용 하드코딩 존재. 경기 변경 시 반드시 갱신
