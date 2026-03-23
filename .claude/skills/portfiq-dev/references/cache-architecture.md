# Portfiq 캐시 아키텍처

## 3-Layer 캐시 구조

```
요청 → [Layer 1: In-Memory TTL] → [Layer 2: Supabase] → [Layer 3: 외부 API]
         cache.py / cachetools        supabase_client.py      yfinance, Finnhub, RSS
```

### Layer 1: In-Memory TTL Cache
- 구현: `backend/services/cache.py` (cachetools TTLCache 래퍼)
- TTL 상수: `backend/services/cache_ttl.py`
- 스레드 세이프 (threading.Lock)

### Layer 2: Supabase
- ETF 마스터 데이터, 뉴스, 브리핑 결과 저장
- Edge Function으로 뉴스 파이프라인 실행

### Layer 3: 외부 API
- yfinance: ETF 가격/홀딩스 (폴백용)
- Finnhub: 경제 이벤트 캘린더
- RSS: 뉴스 피드 원본

## Adaptive TTL 전략

| 데이터 | 장중 TTL | 장외 TTL | 구현 파일 |
|--------|---------|---------|----------|
| ETF 가격 | 15분 | 6시간 | price_service.py |
| 환율 | 30분 | 30분 | exchange_rate_service.py |
| 뉴스 | 5분 | 30분 | news_service.py |
| 경제 이벤트 | 1시간 | 1시간 | calendar_service.py |
| ETF 홀딩스 | 24시간 | 24시간 | holdings_service.py |

## Stale Cache 패턴
외부 API 실패 시 만료된 캐시라도 반환 (stale-while-revalidate):
```python
# price_service.py 패턴
try:
    fresh = await fetch_from_api()
    cache.set(key, fresh, ttl=adaptive_ttl)
    return fresh
except:
    stale = cache.get_stale(key)  # 만료됐어도 반환
    if stale: return stale
    raise
```
