---
description: "버전 태깅. 인프라 변경 시 Notion에 버전 기록 추가 + 현황 갱신. git tag도 생성."
---

# Version Tag — 버전 기록

$ARGUMENTS

## 사용법

```
/version-tag v4.1.0 "Notion 자동 연동 추가"
```

## 프로세스

1. 인자에서 버전과 설명 파싱
2. git tag 생성:
   ```bash
   git tag -a "{버전}" -m "{설명}"
   git push origin "{버전}"
   ```
3. Notion에 현황 갱신 + 버전 기록:
   ```bash
   ./scripts/update-notion-status.sh both "{버전}" "{설명}"
   ```
4. Slack에도 알림

## 버전 규칙

- 인프라 변경 (커맨드/훅/스킬 추가) → minor (v4.1.0 → v4.2.0)
- 규율/규칙 변경 → minor
- 버그 수정 → patch (v4.1.0 → v4.1.1)
- 대규모 구조 변경 → major (v4.0.0 → v5.0.0)
