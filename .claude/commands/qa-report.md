# QA 결과 리포트 생성 및 공유

가장 최근 QA 결과를 정리하여 Slack과 Monday.com에 공유한다.

## 절차

1. 가장 최근 QA 실행 결과 수집
2. integrations/shared/notification_format.py의 format_qa_report() 사용
3. Slack 채널에 결과 포스팅
4. Monday.com 보드에 상태 업데이트
5. .claude/reports/ 에 리포트 파일 저장
