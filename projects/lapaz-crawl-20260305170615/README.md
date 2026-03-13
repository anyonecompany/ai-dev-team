# La Paz Crawl - 선수 프로필 크롤링

맨체스터 유나이티드 / 아스톤 빌라 선수 프로필을 크롤링하여 Supabase에 저장.

## 크롤링 전략

### 소스 우선순위
1. **나무위키** (1차) — 한국어 프로필 데이터
   - URL: `https://namu.wiki/w/{선수_한글명}`
   - 파싱: BeautifulSoup으로 본문 텍스트 추출
   - 주의: robots.txt 준수, 2.5초 딜레이
2. **위키피디아 REST API** (fallback) — 영문 요약
   - URL: `https://en.wikipedia.org/api/rest_v1/page/summary/{name_en}`
   - JSON 응답에서 `extract` 필드 사용

### Supabase documents 테이블 스키마

```sql
CREATE TABLE documents (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    content     TEXT NOT NULL,
    metadata    JSONB DEFAULT '{}',
    embedding   VECTOR(1536),       -- NULL 허용 (deferred 전략)
    collection  TEXT NOT NULL,
    created_at  TIMESTAMPTZ DEFAULT now()
);
```

metadata JSONB 예시:
```json
{
    "player_name_kr": "브루노 페르난데스",
    "player_name_en": "Bruno Fernandes",
    "team": "MUN",
    "position": "MF",
    "source": "namuwiki",
    "crawled_at": "2026-03-05T17:00:00Z"
}
```

### 임베딩 전략
- **현재**: `EMBEDDING_STRATEGY=deferred` — embedding 컬럼을 NULL로 저장
- **추후**: OPENAI_API_KEY 설정 후 배치 임베딩 생성 스크립트 실행

### 디렉토리 구조
```
src/
  config.py          - 환경변수, 선수 목록, 설정 상수
  crawlers/          - 나무위키/위키피디아 크롤러
  processors/        - 텍스트 정제, 청킹
  embeddings/        - 임베딩 생성 (deferred or openai)
  validators/        - 데이터 검증
data/                - 크롤링 원본 캐시
scripts/             - 실행 스크립트
tests/               - 테스트
```
