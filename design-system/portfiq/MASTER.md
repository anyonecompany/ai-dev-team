# Portfiq Design System — Flutter Dark Mode

> **LOGIC:** When building a specific page, first check `design-system/portfiq/pages/[page-name].md`.
> If that file exists, its rules **override** this Master file.
> If not, strictly follow the rules below.

---

**Project:** Portfiq (포트픽) — 서학 ETF AI 브리핑 앱
**Platform:** Flutter (Dart) — iOS / Android
**Style:** Dark Premium + Glassmorphism + Fintech Minimal
**Target:** 2030 한국인 투자자
**Generated:** 2026-03-17 (Flutter 전용)

---

## 1. Color Palette

### Core
| Role | Hex | Dart | Usage |
|------|-----|------|-------|
| Accent | `#6366F1` | `Color(0xFF6366F1)` | CTA, 선택 상태, 브랜드 |
| Accent Light | `#818CF8` | `Color(0xFF818CF8)` | 호버, 그라데이션 끝 |
| Accent Dark | `#4F46E5` | `Color(0xFF4F46E5)` | 프레스 상태 |

### Backgrounds (어두운 순)
| Role | Hex | Usage |
|------|-----|-------|
| Primary BG | `#0D0E14` | Scaffold, 최하층 |
| Card/Secondary | `#16181F` | 카드, 바텀시트 |
| Surface/Tertiary | `#1E2028` | 인풋, 인터랙티브 영역 |

### Semantic
| Role | Hex | Usage |
|------|-----|-------|
| Positive/호재 | `#10B981` | 수익, 상승 |
| Negative/위험 | `#EF4444` | 손실, 하락 |
| Warning/중립 | `#F59E0B` | 경고, 주의 |

### Text
| Role | Hex | Opacity |
|------|-----|---------|
| Primary | `#F9FAFB` | 100% — 제목, 본문 |
| Secondary | `#9CA3AF` | — 보조 텍스트 |
| Tertiary | `#6B7280` | — 비활성, 캡션 |

### Divider / Border
| Role | Hex |
|------|-----|
| Divider | `#2D2F3A` |
| Glass Border | `rgba(255,255,255,0.08)` |
| Glass Border Highlight | `rgba(255,255,255,0.15)` |

---

## 2. Typography

**Font:** Pretendard (전체 통일)

| Scale | Size | Weight | Letter Spacing | Line Height | Usage |
|-------|------|--------|---------------|-------------|-------|
| Display | 28px | w800 | -0.5 | 1.2 | 히어로 숫자, 큰 제목 |
| Title | 22px | w700 | -0.3 | 1.3 | 섹션 제목 |
| Subtitle | 17px | w600 | 0 | 1.4 | 카드 제목, 리스트 제목 |
| Body | 15px | w400 | 0 | 1.5 | 본문, 설명 |
| Caption | 12px | w400 | 0 | 1.3 | 보조 정보, 타임스탬프 |
| Label | 11px | w600 | 1.2 | 1.2 | 배지, 태그, 섹션 라벨 |

### 규칙
- 최소 폰트 사이즈: 11px (Label)
- 숫자/영어도 Pretendard 사용 (Inter 사용 금지)
- 금액/퍼센트는 `fontFeatures: [FontFeature.tabularFigures()]` 적용 권장

---

## 3. Spacing & Layout

### Spacing Scale (4px 기반)
| Token | Value | Usage |
|-------|-------|-------|
| space4 | 4px | 아이콘-텍스트 간격, 미세 갭 |
| space8 | 8px | 인라인 요소 간격 |
| space12 | 12px | 카드 내 요소 간격 |
| space16 | 16px | 표준 패딩, 섹션 내 간격 |
| space20 | 20px | 카드 패딩 |
| space24 | 24px | 섹션 간격 |
| space32 | 32px | 큰 섹션 구분 |
| space48 | 48px | 히어로, 최상단 여백 |

### Corner Radius
| Element | Radius |
|---------|--------|
| Card | 16px |
| Button | 10px |
| Chip | 8px |
| Pill (배지, 태그) | 24px |
| Input | 10px |
| Bottom Sheet | 20px (상단만) |

---

## 4. Glassmorphism 시스템

### Glass Card (3단계 깊이)

| Level | Blur | BG Opacity | Border | Usage |
|-------|------|-----------|--------|-------|
| 1 (Subtle) | 8px | 70% | 0.08 white | 리스트 아이템 |
| 2 (Standard) | 10px | 75% | 0.12 white | 뉴스 카드, ETF 카드 |
| 3 (Prominent) | 16px | 80% | 0.15 white | 모달, 하이라이트 카드 |

### Flutter 구현 패턴
```dart
// Glass Card (Level 2 기본)
Container(
  decoration: BoxDecoration(
    color: Color(0xFF16181F).withOpacity(0.75),
    borderRadius: BorderRadius.circular(16),
    border: Border.all(
      color: Colors.white.withOpacity(0.12),
      width: 1,
    ),
    boxShadow: [
      BoxShadow(
        color: Colors.black.withOpacity(0.15),
        blurRadius: 6,
        blurStyle: BlurStyle.inner,
      ),
    ],
  ),
  child: ClipRRect(
    borderRadius: BorderRadius.circular(16),
    child: BackdropFilter(
      filter: ImageFilter.blur(sigmaX: 10, sigmaY: 10),
      child: content,
    ),
  ),
)
```

### Gradient Border (하이라이트 카드용)
```dart
// 그라데이션 보더 래퍼
Container(
  decoration: BoxDecoration(
    borderRadius: BorderRadius.circular(17), // radius + 1
    gradient: LinearGradient(
      begin: Alignment.topLeft,
      end: Alignment.bottomRight,
      colors: [
        Colors.white.withOpacity(0.15),
        Colors.white.withOpacity(0.02),
      ],
    ),
  ),
  child: Container(
    margin: const EdgeInsets.all(1), // 보더 두께
    decoration: BoxDecoration(
      color: Color(0xFF16181F),
      borderRadius: BorderRadius.circular(16),
    ),
    child: content,
  ),
)
```

---

## 5. Component Specs

### 5.1 뉴스 카드 (NewsCard)
- Glass Level 2 배경
- **좌측 Accent Bar**: 3px width, 카드 높이 전체
  - 호재: `LinearGradient(#10B981 → #059669)`
  - 위험: `LinearGradient(#EF4444 → #DC2626)`
  - 중립: `LinearGradient(#9CA3AF → #6B7280)`
- 탭 시: `AnimatedScale(scale: 0.98 → 1.0, 100ms)`
- 헤드라인: Subtitle (17px, w600)
- 소스 + 시간: Caption (12px, textSecondary)
- 영향도 배지: 우측 상단

### 5.2 브리핑 카드 (BriefingCard)
- Glass Level 3 배경
- **아침**: Indigo gradient border (`#6366F1 → #818CF8`)
- **밤**: Amber gradient border (`#F59E0B → #FBBF24`)
- 제목: Title (22px, w700)
- 요약: Body (15px, textSecondary)
- 아이콘: Lucide `sunrise` / `moon`

### 5.3 영향도 배지 (ImpactBadge)
- Pill shape (radiusPill: 24)
- **높음**: `LinearGradient(#EF4444 → #DC2626)`, white text
- **보통**: `LinearGradient(#F59E0B → #D97706)`, white text
- **낮음**: divider bg, textSecondary text
- Font: Label (11px, w600)

### 5.4 ETF 칩 (EtfChip)
- Surface bg + radiusChip (8px)
- 티커: 14px, w600, accent color
- 등락률: positive/negative color + 부호

### 5.5 하단 탭 바 (BottomTabBar)
- Primary BG + 상단 1px divider
- 선택 탭: accent color + scale 1.1 + **glow shadow** (accent 50%, blur 16, spread 3)
- 비선택 탭: textTertiary, scale 1.0, 라벨 숨김
- 라벨: 10px, w600, 선택 시만 `AnimatedOpacity + AnimatedSlide`로 등장

### 5.6 버튼
- **Primary**: accent bg, white text, 52px height, radiusButton
- **Secondary (Ghost)**: transparent bg, textSecondary, no border
- **Destructive**: negative bg, white text
- 모든 버튼: `splashColor: accent.withAlpha(31)`

### 5.7 인풋/검색바
- tertiaryBg fill + divider border
- 포커스 시: accent border (1px)
- Hint: textSecondary, 14px
- Content padding: horizontal 16, vertical 14

### 5.8 바텀시트
- secondaryBg 배경
- 상단 radiusCard (20px)
- **시스템 드래그 핸들만 사용** (showDragHandle: true)
- 수동 핸들 위젯 추가 금지 (중복 방지)
- 배경 딤: `Colors.black.withOpacity(0.5)`

### 5.9 토글/스위치
- Active: accent thumb + accent track
- Inactive: textPrimary thumb + divider track
- 탭 시: `HapticFeedback.selectionClick()`

### 5.10 SnackBar
- secondaryBg 배경
- textPrimary 글씨 (밝은 색 필수)
- floating behavior
- 아이콘 포함 시: Row(icon, SizedBox(8), text)

### 5.11 Shimmer 로딩
- 카드 골격 형태
- shimmerHighlight(`#252730`) 그라데이션 애니메이션
- 3개 플레이스홀더 카드

### 5.12 빈 상태 (Empty State)
- 중앙 정렬
- 아이콘: 48px, textSecondary.withAlpha(100)
- 안내 텍스트: 14px, textSecondary
- CTA 버튼: TextButton (선택)

---

## 6. Gradients

| Name | Colors | Usage |
|------|--------|-------|
| Indigo | `#6366F1 → #818CF8` | 아침 브리핑, 강조 |
| Night/Amber | `#F59E0B → #FBBF24` | 밤 브리핑 |
| High Impact | `#EF4444 → #DC2626` | 높음 배지, 위험 |
| Medium Impact | `#F59E0B → #D97706` | 보통 배지 |
| Positive | `#10B981 → #059669` | 수익, 호재 |
| Glass Highlight | `white 15% → white 2%` | 카드 보더 하이라이트 |

---

## 7. Animation

| Type | Duration | Curve | Usage |
|------|----------|-------|-------|
| Screen transition | 250ms | easeOutCubic | 페이지 전환 |
| Micro interaction | 150ms | easeOutCubic | 탭, 토글, 호버 |
| Card press | 100ms | easeOut | 카드 스케일 0.98→1.0 |
| Stagger | 60ms delay per item | easeOut | 리스트 아이템 등장 |
| Tab label | 200ms | easeOutCubic | 탭 라벨 fade + slide |

### Flutter Animation 규칙
- `AnimatedContainer`, `AnimatedOpacity` 등 implicit animation 우선
- complex sequence → `AnimationController` + `SingleTickerProviderStateMixin`
- 모든 controller는 `dispose()`에서 해제
- 최대 300ms (그 이상은 느리게 느껴짐)

---

## 8. Shadows

| Level | Config | Usage |
|-------|--------|-------|
| Tab Glow | accent 50%, blur 16, spread 3 | 선택된 탭 아이콘 |
| Card Inner | black 15%, blur 6, inner | Glass 카드 내부 깊이 |
| Card Outer | black 10%, blur 8, offset(0,2) | 떠있는 카드 |
| Elevated | black 20%, blur 16, offset(0,4) | 모달, FAB |

---

## 9. Anti-Patterns (금지)

- **수동 드래그 핸들** — 테마 `showDragHandle: true`가 이미 처리함. 수동 추가 시 중복
- **하드코딩 색상** — 반드시 `PortfiqTheme.xxx` 상수 사용
- **Inter 폰트** — 전체 Pretendard 통일
- **라이트 모드 코드** — 다크 모드 전용
- **이모지 아이콘** — Lucide Icons만 사용
- **과도한 blur** — sigmaX/Y 20 이상 금지 (성능 저하)
- **300ms 초과 애니메이션** — 느리게 느껴짐
- **Container로 간격** — `SizedBox` 사용
- **StatefulWidget 남용** — 정적 UI는 StatelessWidget
- **fontSize 11px 미만** — 최소 11px

---

## 10. Pre-Delivery Checklist

- [ ] 모든 색상이 `PortfiqTheme.xxx` 상수 사용
- [ ] 폰트 전체 Pretendard (Inter 없음)
- [ ] 수동 드래그 핸들 없음 (테마 showDragHandle만)
- [ ] 모든 애니메이션 300ms 이하
- [ ] AnimationController 전부 dispose()
- [ ] const 생성자 가능한 곳에 적용
- [ ] SnackBar 텍스트 textPrimary (밝은 색)
- [ ] 빈 상태 / 에러 상태 / 로딩 상태 모두 처리
- [ ] Lucide Icons만 사용 (이모지 금지)
- [ ] 최소 폰트 사이즈 11px
