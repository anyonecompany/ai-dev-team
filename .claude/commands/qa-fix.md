# /qa-fix - QA 실행 + 자동 수정

QA를 실행하고 실패 항목을 자동 수정한 뒤 재검증한다.

## 사용법
```
/qa-fix                    # 가장 최근 프로젝트
/qa-fix {project-name}     # 특정 프로젝트
```

## 절차

1. `/qa`와 동일하게 전체 QA 실행 (정적 검증 + 서버 스모크 테스트 포함)
2. 실패 항목별 자동 수정:
   - **린트 실패** → `ruff format .` / `npx eslint --fix .`
   - **타입 에러** → 에러 분석 후 코드 수정
   - **테스트 실패** → 테스트 또는 소스 코드 수정
   - **빌드 실패** → 에러 분석 후 수정
   - **스모크 테스트 실패** → 서버 로그 분석 후 원인 수정 (DB 초기화, import 순서, CORS, 환경 설정 등)
3. 수정 후 QA 재실행 (스모크 테스트 포함)
4. **최대 3회 반복** (무한 루프 방지)
5. 결과를 Slack/Monday에 공유
6. 성공 시 커밋: `fix: auto-fix QA failures in {project-name}`
7. 실패 시 Monday 상태 "차단됨", 에이전트 활동 로그에 실패 기록

## 스모크 테스트 실패 시 자동 수정 가이드

### 일반적인 원인과 수정 방법:

| 원인 | 증상 | 수정 방법 |
|------|------|----------|
| DB 테이블 미생성 | `no such table` 에러 | `init_db()`를 앱 startup/lifespan에 추가 |
| Import 순서 | `ImportError`, `circular import` | 모델 import를 lifespan 내부 또는 별도로 분리 |
| CORS 미설정 | 프론트엔드에서 `CORS error` | `CORSMiddleware` 설정 확인 |
| 포트 충돌 | `Address already in use` | 스모크 테스트 전용 포트(9111) 사용, 기존 프로세스 정리 |
| 환경 변수 누락 | `KeyError`, 빈 설정 | `.env` 파일 또는 기본값 설정 확인 |
| 의존성 미설치 | `ModuleNotFoundError` | `pip install -r requirements.txt` / `npm install` |
