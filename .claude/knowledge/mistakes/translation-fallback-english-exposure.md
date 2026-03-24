# 번역 fallback에 영문 원제를 그대로 사용

> 발견일: 2026-03-24
> 프로젝트: Portfiq
> 커밋: 549d6cd

## 문제

번역 API(Gemini) 응답 전 빈 상태를 영문 원제(`f"• {headline}"`)로 채우면,
번역이 느리거나 실패할 때 영문이 사용자에게 그대로 노출된다.

news_service.py에 4곳, Flutter UI에 2곳(news_card.dart, feed_screen.dart)에서
동일한 패턴이 반복되고 있었다.

### 백엔드 (news_service.py)
- `_translate_batch()` fallback: `summary_3line = f"• {h}"` (영문 headline)
- Gemini 파싱 실패 시 fallback: 동일
- `_classify_impacts()`: `article["summary_3line"] = f"• {headline}"`
- Supabase 로드 시: `summary_3line = f"• {headline}"`

### Flutter UI
- `news_card.dart`: `summary3line` 비어있으면 `item.impactReason`을 fallback으로 표시
- `feed_screen.dart`: 동일 — else 블록에서 `impactReason` 표시

## 수정

- fallback은 항상 빈값(`""`) 또는 명시적 로딩 상태여야 함
- UI 레이어도 동일 — impactReason을 summary fallback으로 쓰면 동일 문제 재발
- 번역 완료 후 Supabase `raw_data`에 `summary_3line`도 함께 저장하도록 추가

## 교훈

번역/가공이 필요한 필드의 fallback에 원문(다른 언어)을 사용하면 안 된다.
"빈 상태"가 "잘못된 언어 노출"보다 UX상 항상 낫다.
