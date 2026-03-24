# Notion 현황 페이지 연동 설정

## 1. 페이지 ID 찾기

Notion에서 "AI-dev-team 현황" 페이지를 열고 URL을 확인:
```
https://www.notion.so/your-workspace/AI-dev-team-현황-abc123def456...
```

마지막 32자리 hex가 페이지 ID.

## 2. 환경변수 설정

```bash
# .env 파일에 추가
NOTION_STATUS_PAGE_ID=abc123def456789012345678901234ab

# NOTION_API_KEY는 이미 설정되어 있어야 함
```

## 3. Notion Integration 권한 확인

해당 페이지에 Integration이 연결되어 있어야 함:
- 페이지 우상단 "..." → "Connections" → 해당 Integration 추가

## 4. 테스트

```bash
./scripts/update-notion-status.sh update
```
