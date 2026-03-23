---
name: codemap-update
description: "코드베이스 네비게이션 맵 생성/갱신. 새 프로젝트 시작, 대규모 리팩토링 완료 후, 코드맵이 없거나 오래된 경우 사용."
argument-hint: "[project-name]"
allowed-tools: Read, Glob, Grep, Bash, Write
---

# Codemap Update

코드베이스 네비게이션 맵을 생성/갱신한다. 탐색 컨텍스트 소비를 제거한다.

## 출력 파일
- `.claude/knowledge/codemap-{project}.md` (프로젝트별)
- `.claude/knowledge/codemap-index.md` (인덱스 갱신)

## 코드맵 구조

```
# Codemap: {프로젝트명}
# 최종 갱신: {날짜}

## 진입점
- 메인 파일, 라우터, 앱 초기화 위치

## 핵심 모듈 지도
각 디렉토리: 역할 한 줄 설명 + 핵심 파일 목록

## API/엔드포인트 맵
엔드포인트 → 핸들러 함수 → 관련 DB 테이블

## DB 스키마 요약
Supabase 테이블명 + 핵심 컬럼 + 관계

## 자주 수정되는 파일 TOP 10
(에이전트가 빠르게 찾아야 할 파일들)

## 알려진 복잡 영역
컨텍스트가 많이 필요한 모듈, 주의사항
```

## 사용 방법
새 세션 시작 시: `.claude/knowledge/codemap-index.md` 먼저 읽고 필요한 codemap 선택
