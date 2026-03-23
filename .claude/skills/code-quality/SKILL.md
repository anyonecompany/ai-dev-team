---
name: code-quality
description: "코드 품질 검증 시 사용. 린트, 테스트, 타입체크 실행, 코드 리뷰, 품질 기준 확인 시 자동 트리거."
user-invocable: false
allowed-tools: Read, Bash, Grep, Glob
---

# 코드 품질 스킬

## 검증 명령어

### Python
```bash
ruff check . 2>&1                    # 린트
ruff format --check . 2>&1           # 포맷 확인
mypy . 2>&1 || pyright . 2>&1       # 타입 체크
pytest --tb=short 2>&1               # 테스트
```

### Node.js / React
```bash
npm run lint 2>&1 || npx eslint . 2>&1    # 린트
npx tsc --noEmit 2>&1                      # 타입 체크
npm test 2>&1                              # 테스트
npm run build 2>&1                         # 빌드
```

### Flutter / Dart
```bash
dart analyze . 2>&1                   # 정적 분석
dart format --set-exit-if-changed . 2>&1  # 포맷 확인
flutter test 2>&1                     # 테스트
```

## 품질 기준

| 항목 | 기준 | 불합격 |
|------|------|--------|
| 린트 에러 | 0건 | 1건 이상 |
| 타입 체크 에러 | 0건 | 1건 이상 |
| 테스트 커버리지 | 80% 이상 | 80% 미만 |
| 함수 길이 | 50줄 이내 | 50줄 초과 |
| 파일 길이 | 800줄 이내 | 800줄 초과 |
| 중첩 깊이 | 4단계 이내 | 4단계 초과 |

## 자동 수정 명령어
```bash
ruff format . && ruff check --fix .   # Python
npx eslint --fix . 2>&1               # JS/TS
dart format . 2>&1                    # Dart
```

## 코드 리뷰 체크리스트
- [ ] 변이(mutation) 패턴 사용하지 않는가
- [ ] 하드코딩된 값이 없는가
- [ ] console.log / print 디버깅 문이 없는가
- [ ] 에러 핸들링이 있는가 (사용자 친화적 메시지)
- [ ] 환경변수는 .env에서 가져오는가
- [ ] 입력 검증이 있는가 (pydantic / zod)
