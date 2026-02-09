# TASK-001 결과

생성 시간: 2026-02-02T18:16:40.780890

---

# Instagram Creator Tools 프로젝트 - 요구사항 정의서

## 프로젝트 개요
- **프로젝트명**: Instagram Creator Tools
- **목적**: 인스타그램 크리에이터를 위한 데이터 분석 및 콘텐츠 추천 서비스
- **타겟 사용자**: 인스타그램 비즈니스/크리에이터 계정 운영자
- **시작일**: 2024-12-20
- **현재 단계**: MVP

## MVP 핵심 가치
**"내 인스타그램 계정의 성과를 한눈에 보고, 다음 포스팅 시간을 추천받는다"**

## 주요 기능 요구사항

### 1. 사용자 인증 및 계정 연결
- Instagram Graph API를 통한 OAuth 2.0 인증
- 비즈니스/크리에이터 계정만 지원 (개인 계정 불가)
- 사용자 프로필 정보 저장
- 액세스 토큰 관리 및 자동 갱신

### 2. 데이터 수집 및 저장
- 계정 인사이트 데이터 수집
  - 팔로워 수, 도달 계정, 프로필 조회수
  - 인게이지먼트율 (좋아요, 댓글, 저장, 공유)
- 게시물별 성과 데이터
  - 게시 시간, 도달수, 인터랙션
  - 미디어 타입 (이미지, 동영상, 릴스)
- 데이터 수집 주기: 일 1회 자동

### 3. 대시보드 및 시각화
- 핵심 지표 요약 카드
  - 팔로워 증감률
  - 평균 인게이지먼트율
  - 최고 성과 게시물
- 시간대별 성과 히트맵
- 최근 7일/30일 트렌드 차트

### 4. 포스팅 시간 추천
- 과거 데이터 기반 최적 포스팅 시간 분석
- 요일별/시간대별 추천
- 추천 근거 설명 제공

## Instagram Graph API 제약사항
- **접근 권한**: 비즈니스/크리에이터 계정만 가능
- **Rate Limit**: 시간당 200회 호출
- **데이터 보관**: 최대 2년
- **필수 권한**:
  - instagram_basic
  - instagram_manage_insights
  - pages_show_list
  - pages_read_engagement

## TODO.md

### MVP 핵심 기능 (P0)
- [ ] Instagram OAuth 인증 구현: Graph API 연동 및 토큰 관리 @FullStack-Developer
- [ ] 계정 인사이트 수집: 팔로워, 도달, 인게이지먼트 데이터 @Backend-Developer
- [ ] 대시보드 메인 화면: 핵심 지표 카드 및 7일 트렌드 @Frontend-Developer
- [ ] 포스팅 시간 추천: 시간대별 성과 분석 알고리즘 @AI-Developer

### 필수 기능 (P1)
- [ ] 사용자 계정 관리: 프로필 저장 및 토큰 갱신 @Backend-Developer
- [ ] 게시물 상세 분석: 개별 포스트 성과 조회 @FullStack-Developer
- [ ] 데이터 자동 수집: 일일 배치 작업 스케줄러 @Backend-Developer
- [ ] 반응형 UI: 모바일/데스크톱 대응 @Frontend-Developer

### 추가 기능 (P2)
- [ ] 경쟁사 분석: 유사 계정 비교 @AI-Developer
- [ ] 해시태그 추천: 성과 기반 태그 제안 @AI-Developer
- [ ] 리포트 내보내기: PDF/Excel 다운로드 @Backend-Developer
- [ ] 알림 기능: 주요 지표 변화 알림 @FullStack-Developer

## 기술 검토 요청 사항
1. Instagram Graph API 인증 플로우 구현 방안
2. Supabase에서의 시계열 데이터 최적 저장 구조
3. 실시간 대시보드 업데이트 vs 캐싱 전략
4. 포스팅 시간 추천 알고리즘 접근법

---

**다음 단계**: Architect에게 기술 아키텍처 설계 요청