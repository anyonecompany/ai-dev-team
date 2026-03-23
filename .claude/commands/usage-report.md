---
description: "도구 사용량 리포트 조회. 세션별/도구별 토큰 소비 패턴 확인."
---

# 사용량 리포트

아래 스크립트를 실행하여 사용량 리포트를 출력하라:

```bash
./scripts/token-report.sh today
```

사용자가 특정 기간을 요청하면:
- "오늘" → `./scripts/token-report.sh today`
- "이번 주" → `./scripts/token-report.sh week`
- "전체" → `./scripts/token-report.sh all`

리포트를 보고 아래를 분석하여 제안하라:
1. 가장 많이 사용되는 도구 → 해당 도구의 효율화 방안
2. 세션 수가 비정상적으로 많으면 → /compact 또는 세션 분리 권장
3. 특정 시간대에 집중되면 → 해당 시간 작업 패턴 분석
