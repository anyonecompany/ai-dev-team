# Portfiq(포트픽) — 출시 준비 (Release Preparation)

> Phase 1~3 + 디자인 고도화 + 데이터 연동 완료 상태.
> 앱스토어/플레이스토어 출시를 위한 전체 준비 작업.

## 프로젝트 경로
- Flutter 앱: `projects/portfiq/apps/mobile/`
- FastAPI 백엔드: `projects/portfiq/backend/`
- 환경변수: `projects/portfiq/.env`

## 디자인 시스템
- **Accent**: `#6366F1` (Electric Indigo)
- **Primary BG**: `#0D0E14` / **Card**: `#16181F`
- **다크 모드 전용**
- **폰트**: Pretendard (한국어) + Inter (영어/숫자)

---

## 에이전트 팀 구성 (5인)

### 1. AppIcon-Designer
**담당**: 앱 아이콘 + 스플래시 에셋 생성

**작업 내용**:

1. `projects/portfiq/apps/mobile/assets/icon/` 디렉토리 생성
2. 앱 아이콘 생성 (flutter_launcher_icons 패키지 사용)
   - 컨셉: 다크 배경(#0D0E14) + Electric Indigo(#6366F1) 그라데이션 + "P" 또는 차트 심볼
   - 1024x1024 마스터 아이콘 → iOS/Android 각 사이즈 자동 생성
   - `pubspec.yaml`에 `flutter_launcher_icons` 설정 추가
   - `flutter pub run flutter_launcher_icons` 실행
3. 스플래시 스크린 네이티브 설정 (flutter_native_splash 패키지)
   - 다크 배경(#0D0E14) + 앱 아이콘
   - `pubspec.yaml`에 `flutter_native_splash` 설정 추가
   - `flutter pub run flutter_native_splash:create` 실행
4. 스토어 스크린샷 준비용 가이드 문서 작성
   - `projects/portfiq/docs/store_screenshots_guide.md`
   - iOS: 6.7" (1290x2796), 6.5" (1242x2688), 5.5" (1242x2208)
   - Android: 폰(1080x1920 이상), 태블릿(1200x1920)

**파일 소유권**: `assets/icon/`, `pubspec.yaml` (아이콘/스플래시 섹션만)

---

### 2. BE-Deploy
**담당**: 백엔드 서버 배포 설정 (Railway)

**작업 내용**:

1. `projects/portfiq/backend/Dockerfile` 생성
   ```dockerfile
   FROM python:3.11-slim
   WORKDIR /app
   COPY requirements.txt .
   RUN pip install --no-cache-dir -r requirements.txt
   COPY . .
   EXPOSE 8000
   CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
   ```

2. `projects/portfiq/backend/Procfile` 생성 (Railway용)
   ```
   web: uvicorn main:app --host 0.0.0.0 --port $PORT
   ```

3. `projects/portfiq/backend/.dockerignore` 생성
   ```
   __pycache__/
   *.pyc
   .env
   .git/
   venv/
   ```

4. `projects/portfiq/backend/requirements.txt` 검증 — 모든 import 패키지 포함 확인

5. 환경변수 분리 문서
   - `projects/portfiq/docs/deployment_env_vars.md`
   - Railway에 설정해야 할 환경변수 목록:
     - SUPABASE_URL, SUPABASE_KEY, SUPABASE_SERVICE_KEY
     - ANTHROPIC_API_KEY, ANTHROPIC_MODEL
     - ENVIRONMENT=production
   - **주의**: .env 파일은 커밋하지 않음

6. CORS 설정 업데이트
   - `backend/main.py`에 프로덕션 도메인 CORS 추가
   - 환경변수로 CORS 오리진 제어

7. 헬스체크 엔드포인트 추가
   - `GET /health` → `{"status": "ok", "version": "1.0.0"}`

**파일 소유권**: `backend/Dockerfile`, `backend/Procfile`, `backend/.dockerignore`, `docs/deployment_env_vars.md`

---

### 3. Flutter-Release
**담당**: Flutter 앱 릴리즈 빌드 설정

**작업 내용**:

1. **Android 릴리즈 설정**
   - `android/app/build.gradle` — applicationId 확인 (`com.portfiq.app`)
   - 서명 키스토어 생성 가이드 문서 (실제 키는 수동 생성)
   - `android/app/build.gradle`에 릴리즈 빌드 설정 (minifyEnabled, shrinkResources)
   - ProGuard rules 설정 (`android/app/proguard-rules.pro`)
   - `flutter build appbundle --release` 테스트

2. **iOS 릴리즈 설정**
   - `ios/Runner/Info.plist` — Bundle ID, 버전, 권한 설명 한국어화
     - NSCameraUsageDescription (필요시)
     - NSPhotoLibraryUsageDescription (필요시)
     - NSUserTrackingUsageDescription (ATT)
   - `ios/Runner.xcodeproj/project.pbxproj` — Bundle ID 확인
   - `flutter build ios --release --no-codesign` 테스트

3. **앱 메타데이터 파일 생성**
   - `projects/portfiq/docs/store_metadata.md`:
     ```
     앱 이름: 포트픽 — AI ETF 브리핑
     부제: 내 ETF 맞춤 뉴스 분석
     카테고리: 금융 (Finance)
     키워드: ETF, 투자, 주식, AI, 브리핑, 서학개미, 포트폴리오
     앱 설명 (한국어): ...
     앱 설명 (영어): ...
     지원 URL: https://portfiq.com/support
     개인정보처리방침 URL: https://portfiq.com/privacy
     ```

4. **앱 버전 관리**
   - `pubspec.yaml` — version: 1.0.0+1 확인
   - 버전 표시가 설정 화면에 정확히 반영되는지 확인

5. **프로덕션 API URL 설정**
   - `lib/config/app_config.dart` — production URL을 실제 배포 URL로 업데이트
   - `lib/main_production.dart` — production flavor 빌드 가능하도록 확인

**파일 소유권**: `android/`, `ios/`, `pubspec.yaml` (버전), `docs/store_metadata.md`

---

### 4. Legal-Compliance
**담당**: 법적 문서 + 인공지능기본법 준수

**작업 내용**:

1. **개인정보처리방침** 작성
   - `projects/portfiq/docs/privacy_policy.md` (한국어)
   - `projects/portfiq/docs/privacy_policy_en.md` (영어)
   - 수집 항목: 디바이스 ID, 등록 ETF 목록, 푸시 토큰
   - 수집 목적: 맞춤 브리핑 제공, 푸시 알림
   - 보관 기간, 제3자 제공 (Supabase, Anthropic Claude API)
   - 개인정보 삭제 요청 방법

2. **이용약관** 작성
   - `projects/portfiq/docs/terms_of_service.md`
   - AI 기반 분석은 투자 조언이 아닌 참고 정보임을 명시
   - 면책 조항: 투자 손실에 대한 책임 제한
   - 서비스 변경/중단 권리

3. **인공지능기본법 준수 체크리스트**
   - `.claude/docs/AI_BASIC_LAW_COMPLIANCE.md` 참조
   - AI 사용 고지 UI 확인 (설정 화면에 이미 포함)
   - AI 생성 콘텐츠 라벨링 — 브리핑/뉴스 분석에 "AI 분석" 라벨 추가
   - 위험 식별/완화 문서: `projects/portfiq/docs/ai_risk_assessment.md`

4. **앱 내 법적 링크 연결**
   - 설정 화면의 "이용약관", "개인정보처리방침" 버튼에 실제 URL 연결
   - 현재 "준비 중입니다" 스낵바 → WebView 또는 URL 오픈으로 변경
   - `lib/features/settings/settings_screen.dart` 수정

**파일 소유권**: `docs/privacy_policy*.md`, `docs/terms_of_service.md`, `docs/ai_risk_assessment.md`

---

### 5. QA-Release
**담당**: 릴리즈 전 전체 품질 검증

**작업 내용**:

1. **코드 품질**
   - `flutter analyze` → 에러 0
   - `flutter test` → 테스트 통과 (있는 경우)
   - 미사용 import/변수 제거

2. **빌드 검증**
   - `flutter build appbundle --release` → 성공
   - `flutter build ios --release --no-codesign` → 성공
   - `flutter build web --release` → 성공

3. **기능 검증 체크리스트**
   - [ ] 스플래시 → 온보딩 → 홈 플로우 정상
   - [ ] 온보딩 완료 후 재실행 시 홈 직행
   - [ ] 4개 탭 전환 정상 (Home, My ETF, Calendar, Settings)
   - [ ] 뉴스 카드 탭 → 바텀시트 상세
   - [ ] 브리핑 카드 탭 → 상세 화면 + 뒤로가기
   - [ ] ETF 추가/삭제 정상
   - [ ] ETF 상세 화면 + 뒤로가기
   - [ ] 원문 보기 → 외부 브라우저 오픈
   - [ ] Pull-to-refresh 동작
   - [ ] 캘린더 월 이동 + 날짜 선택
   - [ ] 설정 토글 동작
   - [ ] API 실패 시 graceful fallback (서버 끄고 테스트)

4. **성능 검증**
   - 앱 시작 시간 3초 이내
   - 스크롤 프레임 드랍 없음
   - 메모리 누수 없음 (DevTools 확인)

5. **보안 검증**
   - .env 파일이 .gitignore에 포함되어 있는지 확인
   - 하드코딩된 API 키 없는지 grep 검색
   - Supabase RLS 활성화 확인

6. **검증 결과 보고서**
   - `projects/portfiq/docs/release_qa_report.md` 생성

**파일 소유권**: `docs/release_qa_report.md`, `tests/`

---

## 실행 순서

```
Phase 1 (병렬): AppIcon-Designer + BE-Deploy + Flutter-Release + Legal-Compliance
  ↓
Phase 2: QA-Release (전체 통합 검증)
```

## Notion 보고 규칙 (필수 — 반드시 지킬 것)

각 에이전트는 작업 **시작 시점**과 **완료 시점** 모두 Notion에 보고해야 한다.

```python
from integrations.notion.reporter import report_task_done, report_completion, add_task

# 작업 시작 시 — 반드시 진행중으로 변경
report_task_done("태스크명", "🔨 진행중")

# 작업 완료 시
report_task_done("태스크명", "✅ 완료", "결과 요약")
```

**상태 전이 필수**: `⏳ 진행 전` → `🔨 진행중` → `✅ 완료`
- `🔨 진행중` 없이 바로 `✅ 완료`로 가는 것은 금지

## 규칙
- 기존 코드 구조 최대한 유지
- 다크 모드 전용 — 라이트 모드 코드 금지
- 이모지를 UI 아이콘으로 사용 금지 (Lucide Icons만)
- 환경변수 하드코딩 금지
- .env 파일 절대 커밋 금지
- 민감 정보 (API 키, 시크릿) 하드코딩 금지
- 한국어 우선 (모든 사용자 대면 텍스트)
- 인공지능기본법 준수 필수
- 작업 완료 후 Notion 보고 (project_name="Portfiq (포트픽)")
