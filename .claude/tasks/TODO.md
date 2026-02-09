# 프로젝트 TODO

## 현재 스프린트
- 마지막 업데이트: 2026-02-03 13:00

---

## MVP 핵심 기능 (P0)
> 이것만 되면 출시 가능

- (없음)


## 필수 기능 (P1)
> MVP에 포함되어야 함

### TASK-SEC-001: 현재 코드베이스 보안 감사 [P1/L]
- **담당**: Security-Developer
- **의존성**: 없음
- **설명**: OWASP Top 10 전 항목 점검 + 의존성 스캔
- **산출물**: 보안 감사 리포트 (`docs/security/audit-initial.md`)

### TASK-SEC-002: 시큐어 코딩 가이드라인 작성 [P1/M]
- **담당**: Security-Developer + Architect
- **의존성**: 없음 (SEC-001과 병렬 가능)
- **설명**: 프로젝트 전용 시큐어 코딩 표준 문서화
- **산출물**: `.claude/docs/SECURE_CODING_GUIDE.md`


## 추가 기능 (P2)
> 시간 여유 시 또는 고도화 단계

### TASK-SEC-003: 의존성 스캔 자동화 [P2/M]
- **담당**: Security-Developer + QA-DevOps
- **의존성**: SEC-001 이후
- **설명**: CI/CD 파이프라인에 보안 스캔 통합
- **산출물**: `.github/workflows/security-scan.yml`


---

## 완료된 작업
> DONE 상태 태스크

- [x] TASK-001: MVP 요구사항 정의 및 기능 명세서 작성 - PM-Planner
- [x] TASK-002: 시스템 아키텍처 및 DB 스키마 설계 - Architect
- [x] TASK-003: 대시보드 UI/UX 시안 및 컴포넌트 설계 - Designer
- [x] TASK-004: IG OAuth 및 Graph API 연동 백엔드 구현 - BE-Developer
- [x] TASK-005: 추천 알고리즘 v0 구현 - AI-Engineer
- [x] TASK-006: 대시보드 프론트엔드 구현 - FE-Developer
- [x] TASK-007: Vercel/Railway 배포 및 데모 계정 연동 테스트 - QA-DevOps

