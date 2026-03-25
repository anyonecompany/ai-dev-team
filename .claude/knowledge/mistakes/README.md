# 반복 실수 패턴

> 최종 갱신: 2026-03-23
> 출처: git log 200건 중 fix/bug 커밋 31건 분석

기존 코딩 레벨 pitfall(None 체크, 비동기 I/O 등)은 `common-pitfalls.md` 참조.
이 문서는 프로젝트 운영 중 반복 발생한 시스템/아키텍처 레벨 실수 패턴을 기록한다.

---

## M-001: OAuth 콜백 무한 로딩 연쇄 버그
- **프로젝트**: Portfiq
- **증상**: Google OAuth 로그인 후 콜백 페이지에서 무한 로딩. 4건의 연쇄 fix 커밋 발생 (`731432c` → `697d52b` → `3a2cba5` → `490daac`)
- **원인**: (1) redirectTo 경로 오류, (2) race condition, (3) PKCE code exchange 미처리, (4) 콜백에서 불필요한 백엔드 호출
- **예방**: OAuth 흐름은 전용 콜백 페이지를 분리하고, PKCE 코드 교환을 명시적으로 처리. 콜백 페이지는 최소 로직만 유지 (백엔드 호출 제거)

## M-002: Event Loop 블로킹으로 서버 행(hang)
- **프로젝트**: Portfiq
- **증상**: 뉴스 수집 백그라운드 작업이 FastAPI의 event loop를 블로킹하여 전체 API 응답 불가. 3건 fix (`fe6dee1` → `19df3db` → `f96fa3c`)
- **원인**: 동기 I/O 작업(뉴스 크롤링)을 async 함수 안에서 직접 호출. `asyncio.to_thread`로 래핑했으나 여전히 event loop 간섭
- **예방**: 무거운 백그라운드 작업은 별도 스레드 + 별도 event loop에서 실행 (`threading.Thread` + `asyncio.new_event_loop`). 수집 간격도 3분에서 10분으로 완화

## M-003: 캐시 무효화 누락
- **프로젝트**: Portfiq
- **증상**: 뉴스 번역 후 피드에 번역 결과가 반영되지 않음 (`40c41cc`). 야간 브리핑도 구 데이터 기반으로 생성 (`3453170`)
- **원인**: 데이터 갱신 후 인메모리 캐시를 무효화하지 않아 구 데이터가 계속 서빙
- **예방**: 데이터 변경(INSERT/UPDATE) 후 반드시 관련 캐시 클리어 API 호출. 캐시 클리어 전용 엔드포인트 제공

## M-004: CORS + API 타임아웃 복합 장애
- **프로젝트**: Portfiq
- **증상**: Admin 대시보드 무한 로딩, Flutter 앱 타임아웃. 5건 이상 fix (`46f4cc9`, `aed4fc5`, `c3f89d2`, `04e35a3`, `908bc2a`)
- **원인**: (1) CORS에 Vercel preview URL 미등록, (2) API 기본 타임아웃 10초로 부족, (3) credentials:include와 CORS 와일드카드 충돌, (4) DNS resolve 불안정
- **예방**: CORS 허용 도메인은 regex로 preview URL 포함. API 타임아웃은 20~30초로 설정. `credentials:include` 사용 시 와일드카드 CORS 금지. Vercel에 API proxy rewrite 추가로 DNS 안정성 확보

## M-005: DB 컬럼명/키 불일치
- **프로젝트**: Portfiq
- **증상**: daily_metrics API에서 컬럼명 `metric_date`로 조회하나 실제 DB는 `date` (`9a59533`). Supabase anon key 서명 불일치 (`2f6d5f1`)
- **원인**: DB 스키마 변경 후 코드 동기화 누락. 환경별 키 관리 미흡
- **예방**: DB 스키마 변경 시 코드 전체 grep으로 참조 컬럼명 확인. 키/시크릿 변경 시 모든 환경(로컬/스테이징/프로덕션) 동시 갱신

## M-006: 하드코딩 데이터가 프로덕션까지 배포
- **프로젝트**: Portfiq
- **증상**: 출시 QA에서 하드코딩된 mock 데이터, localhost URL이 발견 (`1099686`)
- **원인**: 개발 편의를 위한 하드코딩을 제거하지 않고 배포. QA가 정적 검증(린트)에만 의존
- **예방**: QA 시 실사용자 플로우 검증 필수 (신규 설치 → 온보딩 → 홈에서 실데이터 확인). production 빌드에서 localhost 차단

## M-007: GitHub Actions submodules 체크아웃 실패
- **프로젝트**: 전체
- **증상**: CI에서 checkout 실패 (`e9ce083`)
- **원인**: 서브모듈이 있는 레포에서 기본 checkout이 서브모듈을 재귀적으로 fetch 시도
- **예방**: `actions/checkout`에 `submodules: false` 명시

## M-008: html2canvas가 display:none→block 전환된 요소의 CSS 배경을 무시
- **프로젝트**: AdaptFit (report-builder)
- **증상**: PDF 커버 페이지의 네이비 그라데이션 배경이 렌더링되지 않음. `onclone`에서 인라인 `background-color`를 설정해도 무시됨
- **원인**: html2canvas는 CSS 클래스에서 `display: none`이었던 요소를 JS로 `display: block`으로 전환해도, 해당 요소의 배경 스타일을 제대로 렌더하지 못함 (html2canvas 내부 렌더 트리 구성 시점의 한계)
- **해결**: 네이비 배경 포기 → 흰색 배경 + 네이비 텍스트의 기업 보고서 스타일로 디자인 변경
- **예방**: html2pdf/html2canvas로 PDF 생성 시 동적 표시/숨김 요소의 배경은 인라인 스타일이 아닌 **항상 표시되는 요소**에 적용하거나, CSS 배경 대신 인라인 `<div>` 배경 레이어 사용

## M-009: Tailwind arbitrary values와 CSS 변수 오버라이드의 불일치
- **프로젝트**: AdaptFit (report-builder)
- **증상**: PDF 다크→라이트 전환 시 CSS 변수(`--bg`, `--surface`)만 오버라이드했으나, 다크 테마 적용 후 Tailwind arbitrary values(`bg-[#0f1829]`)가 CSS 변수를 참조하지 않아 여전히 다크 배경
- **원인**: FE 에이전트가 CSS 변수 기반 설계(`bg-surface`)를 Tailwind arbitrary values(`bg-[#0f1829]`)로 하드코딩
- **해결**: `onclone`에서 `getComputedStyle` 기반 DOM 순회로 luminance 판별 후 색상 교체
- **예방**: 다크/라이트 전환이 필요한 프로젝트에서는 **CSS 변수 기반 색상만 사용**하고, Tailwind arbitrary hex values 사용 금지. 또는 Tailwind `dark:` 접두사 활용

---

## 변경 이력

| 날짜 | 변경 내용 |
|------|----------|
| 2026-03-26 | 회고: M-008, M-009 추가 (html2canvas 배경 한계, Tailwind arbitrary values 불일치) |
| 2026-03-23 | git log 분석 기반 시스템 레벨 실수 패턴 7건 신규 작성 |
