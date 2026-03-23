# /qa-report - QA 결과 리포트 공유

가장 최근 QA 결과를 정리하여 Slack과 Monday.com에 공유한다.

## 사용법
```
/qa-report                    # 가장 최근 QA 결과
/qa-report {project-name}     # 특정 프로젝트 QA 결과
```

## 절차

1. `.claude/reports/` 에서 가장 최근 QA 리포트 파일 읽기
2. `integrations/shared/notification_format.py`의 `format_qa_report()` 로 포맷
3. Slack 채널에 리포트 전송
4. Monday.com QA 그룹에 결과 기록 (아직 없으면)
5. 터미널에도 결과 출력

## 외부 보고

QA 리포트 완료 후 Notion/Slack에 자동 보고:
```bash
./scripts/report-to-external.sh qa_report '{
  "project": "{프로젝트}",
  "verdict": "{GO/CONDITIONAL GO/NO GO}",
  "p0": {P0 건수},
  "p1": {P1 건수},
  "p2": {P2 건수},
  "fixed": {자동수정 건수},
  "manual": {수동필요 건수},
  "summary": "{요약}"
}'
```
