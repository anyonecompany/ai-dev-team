# Portfiq(포트픽) — 디자이너 에이전트: UI/UX 고도화

> 기존 디자인 시스템 스펙 기반으로 트렌디하고 세련된 핀테크 앱 UI/UX를 고도화한다.
> Designer 에이전트가 디자인 시스템을 생성하고, Flutter 개발자 에이전트가 실제 코드에 적용한다.

## 프로젝트 정보
- **제품**: 서학 ETF AI 브리핑 앱 (모바일 퍼스트, 다크 모드 전용)
- **산업**: Fintech / Investment / Personal Finance
- **스타일 키워드**: dark premium, glassmorphism, minimal luxury, data-driven, trendy
- **타겟**: 2030 한국인 투자자 ("서학 ETF 개미")
- **기술 스택**: Flutter (Dart)
- **경로**: `projects/portfiq/apps/mobile/`

## 기존 디자인 시스템 (유지하되 고도화)
- **Key Accent**: Electric Indigo `#6366F1`
- **Primary BG**: `#0D0E14` / **Card**: `#16181F` / **Surface**: `#1E2028`
- **Impact**: High `#EF4444` / Medium `#F59E0B` / Low `#6B7280`
- **Positive**: `#10B981` / **Negative**: `#EF4444`
- **Text**: Primary `#F9FAFB` / Secondary `#9CA3AF`
- **폰트**: Pretendard (한국어) + Inter (영어/숫자)
- **아이콘**: Lucide Icons
- **다크 모드 전용**

---

## 에이전트 팀 구성 (2인)

### 1. Designer (디자인 시스템 생성 + UI 스펙)
**담당**: 디자인 인텔리전스 엔진으로 고도화된 디자인 시스템 생성 + 컴포넌트별 상세 스펙

**작업 순서**:

#### Step 1: 디자인 시스템 생성
```bash
python3 skills/ui-ux-pro-max/scripts/search.py "fintech investment portfolio dark premium glassmorphism" --design-system --persist -p "portfiq"
```

#### Step 2: Flutter 스택 가이드라인
```bash
python3 skills/ui-ux-pro-max/scripts/search.py "fintech dark premium mobile" --stack flutter
```

#### Step 3: 상세 도메인 검색
```bash
# 트렌디한 다크 스타일
python3 skills/ui-ux-pro-max/scripts/search.py "dark premium glassmorphism fintech" --domain style

# 핀테크 컬러 팔레트 (기존 대비 보완/개선)
python3 skills/ui-ux-pro-max/scripts/search.py "fintech investment dark premium" --domain color

# 차트/데이터 시각화 (ETF 등락, 포트폴리오)
python3 skills/ui-ux-pro-max/scripts/search.py "financial chart portfolio realtime" --domain chart

# UX 베스트 프랙티스 (모바일 핀테크)
python3 skills/ui-ux-pro-max/scripts/search.py "mobile fintech onboarding feed animation" --domain ux

# 타이포그래피 (Pretendard + Inter 조합 검증/보완)
python3 skills/ui-ux-pro-max/scripts/search.py "korean fintech premium clean" --domain typography
```

#### Step 4: 페이지별 오버라이드 생성
```bash
# 온보딩
python3 skills/ui-ux-pro-max/scripts/search.py "onboarding flow fintech investment" --design-system --persist -p "portfiq" --page "onboarding"

# 피드 (메인 홈)
python3 skills/ui-ux-pro-max/scripts/search.py "news feed cards dark financial" --design-system --persist -p "portfiq" --page "feed"

# 브리핑 상세
python3 skills/ui-ux-pro-max/scripts/search.py "briefing summary report financial dark" --design-system --persist -p "portfiq" --page "briefing"

# ETF 상세
python3 skills/ui-ux-pro-max/scripts/search.py "stock detail portfolio holdings chart dark" --design-system --persist -p "portfiq" --page "etf-detail"

# 설정
python3 skills/ui-ux-pro-max/scripts/search.py "settings preferences notification toggle dark" --design-system --persist -p "portfiq" --page "settings"
```

#### Step 5: 컴포넌트별 상세 스펙 작성

MASTER.md에 아래 컴포넌트들의 상세 스펙을 포함:

1. **뉴스 카드** — glassmorphism 적용, 영향도별 그라데이션 액센트 바, 호버/프레스 피드백
2. **브리핑 카드** — 아침(Indigo 그라데이션)/밤(Amber 그라데이션) 테두리, 내부 blur 효과
3. **ETF 칩** — 등락률 컬러 + 마이크로 스파크라인(선택)
4. **영향도 배지** — High/Medium/Low 각각 고유 비주얼 (아이콘 + 그라데이션 배경)
5. **탭 바** — 선택 탭 Indigo 글로우 효과, 비선택 탭 subtle 아이콘
6. **카드 컨테이너** — subtle border + inner shadow + glassmorphism (선택적)
7. **버튼** — Primary(Indigo 그라데이션)/Secondary(ghost)/Destructive(Red)
8. **인풋/검색바** — surface 배경 + 포커스 시 Indigo 보더 glow
9. **토글/스위치** — Indigo on 상태, smooth 전환
10. **스낵바/토스트** — 하단 등장, blur 배경
11. **바텀시트** — 둥근 상단, 핸들 바, 배경 딤
12. **스플래시** — 로고 + Indigo 그라데이션 배경 + 페이드인
13. **빈 상태** — 아이콘 + 안내 텍스트 + CTA 버튼
14. **Shimmer 로딩** — 카드 형태 골격 + 그라데이션 애니메이션

**디자인 고도화 방향**:
- **Glassmorphism**: 카드에 subtle한 glass 효과 (과하지 않게)
- **Gradient accents**: 단색 보더 → 미세한 그라데이션 보더
- **Micro-interactions**: 탭/스와이프 시 부드러운 스케일/opacity 변화
- **Depth**: 레이어 간 미세한 그림자/블러로 깊이감
- **Typography hierarchy**: Display(28) > Title(22) > Subtitle(17) > Body(15) > Caption(12) 명확한 위계
- **Spacing rhythm**: 4px 단위 (4, 8, 12, 16, 20, 24, 32, 48)
- **Corner radius**: 카드 16px, 버튼 12px, 칩 24px, 인풋 10px (기존보다 살짝 키움)
- **Animation curves**: `easeOutCubic` 기본, `spring` 바운스 효과 (선택)

**납품 전 체크리스트 실행 (필수)**

**파일 소유권**: `design-system/portfiq/`

---

### 2. Flutter-Designer (디자인 적용 개발자)
**담당**: Designer가 생성한 MASTER.md + 페이지별 오버라이드를 실제 Flutter 코드에 적용

**작업 내용**:

1. `lib/config/theme.dart` 업그레이드
   - MASTER.md의 디자인 토큰 반영
   - 그라데이션, 그림자, 블러 값 상수화
   - TextTheme 위계 재정의
   - 컴포넌트 테마 (CardTheme, AppBarTheme, BottomSheetTheme 등)

2. `lib/shared/widgets/` 전체 업그레이드
   - MASTER.md 컴포넌트 스펙에 따라 기존 위젯 리팩토링
   - glassmorphism 효과 적용 (BackdropFilter + 투명 배경)
   - 그라데이션 보더, 글로우 효과
   - 마이크로 인터랙션 애니메이션 추가
   - shimmer_loading.dart 신규 생성

3. `lib/shared/widgets/glass_card.dart` — 재사용 가능한 Glass 카드 컴포넌트 (신규)

4. 각 화면에 디자인 적용
   - 온보딩 (`lib/features/onboarding/`)
   - 피드 (`lib/features/feed/`)
   - 브리핑 상세 (`lib/features/briefing/`)
   - 스플래시 (`lib/features/splash/`) — 신규 또는 기존 업그레이드

5. 탭 바 업그레이드 (`lib/shared/widgets/bottom_tab_bar.dart`)
   - 선택 탭 글로우 + 레이블 애니메이션

6. 모든 변경에 EventTracker 이벤트 유지

**중요**: Designer의 MASTER.md가 생성된 후에 작업 시작. MASTER.md를 반드시 읽고 그대로 적용할 것.

**파일 소유권**: `lib/config/theme.dart`, `lib/shared/widgets/`, 각 feature 화면의 UI 코드

---

## 실행 순서

```
Phase 1: Designer (디자인 시스템 생성 — 검색 엔진 기반)
  ↓
Phase 2: Flutter-Designer (MASTER.md 기반 코드 적용)
```

## Notion 보고 규칙 (필수 — 반드시 지킬 것)

각 에이전트는 작업 **시작 시점**과 **완료 시점** 모두 Notion에 보고해야 한다.

```python
from integrations.notion.reporter import report_task_done

# 작업 시작 시 — 반드시 진행중으로 변경
report_task_done("태스크명", "🔨 진행중")

# 작업 완료 시
report_task_done("태스크명", "✅ 완료", "결과 요약")
```

**상태 전이 필수**: `⏳ 진행 전` → `🔨 진행중` → `✅ 완료`
- `🔨 진행중` 없이 바로 `✅ 완료`로 가는 것은 금지

## 규칙
- Designer는 코드를 직접 작성하지 않음 — 스펙만 생성
- Flutter-Designer는 MASTER.md를 읽은 후에만 코드 작성
- 기존 Electric Indigo `#6366F1` 액센트 컬러 유지 (변경 금지)
- 다크 모드 전용 (라이트 모드 코드 금지)
- 이모지를 UI 아이콘으로 사용 금지 (Lucide Icons만)
- glassmorphism은 subtle하게 — 과도한 blur/투명도 금지
- 모든 애니메이션 300ms 이하
- 작업 완료 후 Notion 보고 (project_name="Portfiq (포트픽)")
