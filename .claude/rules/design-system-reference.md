# 디자인 시스템 참조 규칙

## 적용 대상
- .dart 파일 (Flutter UI)
- .tsx/.jsx 파일 (React UI)
- .css/.scss 파일 (스타일)
- .vue 파일 (Vue UI)

## 규칙

### UI 파일 수정 시 필수
1. 해당 프로젝트의 design-system/{프로젝트}/MASTER.md를 먼저 읽는다
2. 페이지별 오버라이드가 있으면 pages/{페이지}.md도 읽는다
3. MASTER.md에 정의된 값만 사용한다:
   - 컬러: MASTER.md의 팔레트만
   - 타이포그래피: MASTER.md의 폰트/사이즈만
   - 스페이싱: MASTER.md의 간격 체계만
   - 컴포넌트: MASTER.md의 패턴을 따름

### 하지 말 것
- 하드코딩 컬러 (#FF5733 같은 임의 값)
- MASTER.md에 없는 폰트 사이즈
- 컴포넌트별 개별 스타일 (시스템에 없으면 시스템에 추가 먼저)

### 새 컴포넌트/스타일 필요 시
1. MASTER.md에서 가장 가까운 기존 패턴을 찾는다
2. 없으면 Designer 에이전트에게 위임하여 MASTER.md에 추가
3. 추가된 후 사용

### 디자인 시스템 없는 프로젝트
design-system/ 디렉토리가 없으면 이 규칙은 적용하지 않는다.
새 프로젝트에서 디자인이 필요하면 /portfiq-design으로 생성.
