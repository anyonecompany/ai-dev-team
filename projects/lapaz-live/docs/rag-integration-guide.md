# RAG Pipeline Integration Guide

> La Paz 대시보드 백엔드에서 기존 RAG 파이프라인을 통합하기 위한 가이드

## 1. RAG 파이프라인 개요

기존 RAG 코드 위치: `projects/lapaz-live/src/rag/`

파이프라인 흐름:
```
질문 → classify(question) → retrieve(question, category, keywords) → generate(question, documents, match_context) → 응답
```

### 모듈 구성

| 모듈 | 파일 | 역할 |
|------|------|------|
| Classifier | `classifier.py` | Claude Sonnet으로 질문을 7개 카테고리 분류 + 키워드 추출 |
| Retriever | `retriever.py` | Voyage AI 벡터 검색 + 키워드 ILIKE 검색 → RRF 병합 |
| Generator | `generator.py` | Claude Sonnet으로 한국어 3~4문장 답변 생성 |
| Pipeline | `pipeline.py` | 위 3개 모듈 통합 오케스트레이션 |

## 2. pipeline.ask() 호출 방법

```python
import sys
import os

# RAG 파이프라인 경로 추가
RAG_PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "lapaz-live", "src")
)
sys.path.insert(0, RAG_PROJECT_ROOT)

from rag.pipeline import ask

# 호출 (async)
result = await ask(
    question="브루노가 왜 자꾸 밑으로 내려와?",
    match_context="Man Utd vs Aston Villa | 2026-03-15 23:00 KST | Premier League"
)
```

### sys.path 설정 주의사항

- RAG 모듈은 상대 경로로 `.env`와 `prompts/` 디렉토리를 참조함
- `classifier.py`, `retriever.py`, `generator.py` 모두 `load_dotenv(os.path.join(os.path.dirname(__file__), "..", "..", ".env"))` 로 `.env`를 로드
- 따라서 `.env` 파일은 반드시 `lapaz-live/.env` 위치에 존재해야 함
- `prompts/` 디렉토리도 `Path(__file__).parent / "prompts"` 로 참조하므로 원본 위치 유지 필요

## 3. 필요한 환경변수

| 변수명 | 용도 | 사용 모듈 | 필수 여부 |
|--------|------|----------|----------|
| `ANTHROPIC_API_KEY` | Claude API (분류 + 답변 생성) | classifier, generator | 필수 |
| `VOYAGE_API_KEY` | Voyage AI 임베딩 (벡터 검색) | retriever | 선택 (없으면 키워드 검색만) |
| `SUPABASE_URL` | Supabase 프로젝트 URL | retriever | 필수 |
| `SUPABASE_SERVICE_KEY` | Supabase service role key | retriever | 필수 |

> 주의: retriever.py에서 환경변수 키는 `SUPABASE_SERVICE_KEY` (SUPABASE_KEY 아님)

## 4. 반환값 필드 매핑

`pipeline.ask()` 반환값:

```python
{
    "question": str,           # 원본 질문
    "category": str,           # 분류 카테고리 (7개 중 하나)
    "keywords": list[str],     # 추출된 키워드
    "confidence": float,       # 분류 확신도 (0.0~1.0)
    "answer": str,             # 생성된 답변 (한국어, 50~500자)
    "source_docs": list[int],  # 참조 문서 ID 목록
    "generation_time_ms": int, # 답변 생성 소요시간 (ms)
    "total_time_ms": int,      # 전체 파이프라인 소요시간 (ms)
}
```

### API 응답 필드 매핑 제안

| Pipeline 필드 | API 응답 필드 | 설명 |
|--------------|--------------|------|
| `answer` | `answer` | 사용자에게 보여줄 답변 |
| `category` | `category` | 질문 분류 결과 |
| `keywords` | `keywords` | 검색 키워드 |
| `confidence` | `confidence` | 분류 확신도 |
| `source_docs` | `sources` | 참조 문서 ID |
| `generation_time_ms` | `metrics.generation_ms` | 생성 소요시간 |
| `total_time_ms` | `metrics.total_ms` | 전체 소요시간 |

## 5. 분류 카테고리 목록

| 카테고리 | 설명 | 검색 컬렉션 |
|---------|------|------------|
| `player_info` | 선수 기본 정보 | `player_profiles` |
| `tactical_intent` | 전술적 의도 | `match_context` |
| `match_flow` | 경기 흐름 | `match_context` |
| `player_form` | 선수 폼/컨디션 | `player_profiles`, `match_context` |
| `fan_simulation` | 팬 시뮬레이션 | `player_profiles`, `match_context` |
| `season_narrative` | 시즌 서사 | `match_context` |
| `rules_judgment` | 규칙/심판 판정 | `match_context` |

## 6. 에러 핸들링 가이드

### ANTHROPIC_API_KEY 누락/만료
- **영향**: classifier + generator 모두 실패 → 전체 파이프라인 중단
- **에러 타입**: `anthropic.AuthenticationError`
- **대응**: 503 응답 + "AI 서비스 일시 불가" 메시지

### VOYAGE_API_KEY 누락
- **영향**: 벡터 검색 비활성화, 키워드 검색만으로 폴백
- **에러 타입**: 에러 없음 (graceful degradation)
- **대응**: 로그 경고, 답변 품질 저하 가능성 안내 불필요

### SUPABASE 연결 실패
- **영향**: retriever 전체 실패
- **에러 타입**: `Exception` (supabase client)
- **대응**: 503 응답 + "데이터 검색 불가" 메시지

### 타임아웃
- **Claude API**: 기본 60초 타임아웃 (분류 + 생성 각각)
- **Voyage API**: 임베딩 생성 (보통 1~3초)
- **권장**: API 엔드포인트에 전체 30초 타임아웃 설정
- **대응**: `asyncio.wait_for(ask(...), timeout=30.0)` 래핑

### JSON 파싱 실패 (Classifier)
- **영향**: 자동으로 기본값 반환 (`category="match_flow"`, `confidence=0.3`)
- **대응**: 별도 처리 불필요 (내부 폴백)

## 7. 성능 메트릭

응답에 포함된 성능 지표 활용:

```python
result = await ask(question, match_context)

# 성능 모니터링
metrics = {
    "generation_ms": result["generation_time_ms"],  # Claude 답변 생성만
    "total_ms": result["total_time_ms"],             # 분류+검색+생성 전체
    "overhead_ms": result["total_time_ms"] - result["generation_time_ms"],  # 분류+검색
}
```

### 예상 소요시간

| 단계 | 예상 시간 |
|------|----------|
| classify | 1~3초 (Claude API) |
| retrieve (vector) | 0.5~2초 (Voyage + Supabase) |
| retrieve (keyword) | 0.1~0.5초 (Supabase) |
| generate | 2~5초 (Claude API) |
| **전체** | **3~10초** |
