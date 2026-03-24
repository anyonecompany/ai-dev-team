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
3. Notion 현황 페이지 갱신:
   ```bash
   ./scripts/update-notion-status.sh update
   ```
4. Notion 버전 관리 DB에 기록 (문제→가설→해결→결과 본문 포함):
   ```bash
   python3 integrations/notion/version_recorder.py \
       --title "{버전} — {설명}" \
       --type "{유형}" \
       --summary "{한줄 요약}" \
       --scope "{영향 범위}" \
       --problem "{이전 문제점}" \
       --hypothesis "{가설}" \
       --solution "{해결 방식}" \
       --result "{결과}"
   ```
   사용자가 --problem 등을 안 주면 빈 템플릿이 들어감. Notion에서 직접 채울 수 있음.
5. Slack에도 알림

## 버전 규칙

- 인프라 변경 (커맨드/훅/스킬 추가) → minor (v4.1.0 → v4.2.0)
- 규율/규칙 변경 → minor
- 버그 수정 → patch (v4.1.0 → v4.1.1)
- 대규모 구조 변경 → major (v4.0.0 → v5.0.0)
