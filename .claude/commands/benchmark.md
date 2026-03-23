---
description: "에이전트 성능 벤치마크 리포트. 에이전트별 호출 횟수, 도구 사용 패턴, Read/Write 비율 분석."
---

# 에이전트 벤치마크

아래를 실행하라:
```bash
./scripts/agent-benchmark.sh
```

리포트 결과를 분석하여:
1. 비효율적인 에이전트가 있으면 → 스킬/컨텍스트 개선 제안
2. Read 비율이 과도하면 → codemap 갱신 또는 CLAUDE.md 보강 제안
3. 특정 에이전트가 과다 사용되면 → 작업 분배 재조정 제안
4. 에이전트 활동이 전무하면 → /orchestrate 활용 권장

## 외부 보고

벤치마크 리포트 완료 후 Notion에 자동 기록:
```bash
./scripts/report-to-external.sh benchmark '{
  "total_calls": {총 호출 수},
  "read_write_ratio": "{R/W 비율}",
  "top_agents": "{상위 에이전트}",
  "top_tools": "{상위 도구}"
}'
```
