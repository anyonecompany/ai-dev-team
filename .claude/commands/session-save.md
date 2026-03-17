# /session-save

현재 작업 세션의 상태를 저장합니다.
컨텍스트 한계 도달 전, 또는 긴 작업의 중간 체크포인트로 사용합니다.

## 실행
`context-compact` 스킬을 실행하여:
1. `.claude/handoff/session-{timestamp}.md` 생성
2. 완료/미완료/실패 항목 기록
3. 다음 단계 명시
4. 코드맵 갱신 (변경사항 있을 경우)
5. 복원 명령어 안내
