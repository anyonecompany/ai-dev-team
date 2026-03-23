# Portfiq 비용 최적화

## 원칙
비용 최적화는 아키텍처에 내장되어 있다. 후속 최적화가 아니라 설계 단계에서 반영한다.

## 4대 비용 절감 패턴

### 1. 그룹 공유 (Group Sharing)
같은 ETF를 구독하는 사용자들은 동일한 뉴스/브리핑을 공유한다.
- 뉴스 수집: ETF별 1회 → 전체 구독자 공유
- 브리핑: 스케줄러가 1회 생성 → 캐시에서 모든 사용자에게 반환

### 2. 배치 번역 (Batch Translation)
영문 뉴스를 개별이 아닌 배치로 번역한다.
- `news_service.py`: RSS 수집 → 영문 캐시 즉시 저장 → Gemini 배치 번역 (백그라운드)
- 개별 요청마다 Gemini 호출하지 않음

### 3. 3-Layer 캐시
외부 API 호출을 최소화한다. 상세: [cache-architecture.md](cache-architecture.md)

### 4. Adaptive TTL
장중/장외 TTL을 분리하여 불필요한 갱신을 방지한다.
- 장외에는 가격이 변하지 않으므로 6시간 TTL

## Gemini 비용 관리
- 모델: `gemini-2.5-flash-lite` (가장 저렴한 등급)
- 브리핑 생성: 1일 2회 (08:35, 22:00 KST)
- 번역: 배치 처리
- 영향도 분류: Gemini + 키워드 폴백 (API 실패 시 로컬 분류)

## 비용 관련 금지사항
- 사용자 요청마다 Gemini 직접 호출 금지 (캐시 우선)
- 개별 뉴스 아이템마다 번역 API 호출 금지 (배치만)
- yfinance 과도한 호출 금지 (rate limit 위험)
