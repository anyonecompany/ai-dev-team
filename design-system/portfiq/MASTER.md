# Portfiq Design System - Master File

> **LOGIC:** When building a specific page, first check `design-system/portfiq/pages/[page-name].md`.
> If that file exists, its rules **override** this Master file.
> If not, strictly follow the rules below.

---

**Project:** Portfiq
**Updated:** 2026-03-13
**Category:** Fintech / ETF Investment Portfolio App
**Platform:** Flutter (iOS & Android)
**Theme:** Dark Premium Glassmorphism

---

## Global Rules

### Color Palette

| Role | Hex | Flutter Color | CSS Variable |
|------|-----|---------------|--------------|
| Background Primary | `#0D0E14` | `Color(0xFF0D0E14)` | `--color-bg-primary` |
| Background Secondary | `#16181F` | `Color(0xFF16181F)` | `--color-bg-secondary` |
| Background Tertiary | `#1E2028` | `Color(0xFF1E2028)` | `--color-bg-tertiary` |
| Surface/Card | `#16181F` @ 70% | `Color(0xFF16181F).withOpacity(0.7)` | `--color-surface` |
| Border | `#2D2F3A` | `Color(0xFF2D2F3A)` | `--color-border` |
| Text Primary | `#F8FAFC` | `Color(0xFFF8FAFC)` | `--color-text-primary` |
| Text Secondary | `#9CA3AF` | `Color(0xFF9CA3AF)` | `--color-text-secondary` |
| Text Tertiary | `#6B7280` | `Color(0xFF6B7280)` | `--color-text-tertiary` |
| Accent / Indigo | `#6366F1` | `Color(0xFF6366F1)` | `--color-accent` |
| Accent Light | `#818CF8` | `Color(0xFF818CF8)` | `--color-accent-light` |
| Accent Dark | `#4F46E5` | `Color(0xFF4F46E5)` | `--color-accent-dark` |
| Positive / Green | `#10B981` | `Color(0xFF10B981)` | `--color-positive` |
| Negative / Red | `#EF4444` | `Color(0xFFEF4444)` | `--color-negative` |
| Warning / Amber | `#F59E0B` | `Color(0xFFF59E0B)` | `--color-warning` |
| Warning Light | `#FBBF24` | `Color(0xFFFBBF24)` | `--color-warning-light` |
| High Impact Red | `#DC2626` | `Color(0xFFDC2626)` | `--color-high-impact` |
| Medium Impact Amber | `#D97706` | `Color(0xFFD97706)` | `--color-medium-impact` |

**Color Notes:** Dark OLED-optimized background with Electric Indigo `#6366F1` accent (변경 금지). Green/Red for financial positive/negative. Amber for warnings and briefing highlights.

### Typography

- **Primary Font:** Inter (numbers, UI labels, prices)
- **Korean Font:** Pretendard (Korean body text fallback)
- **Fallback:** Noto Sans KR, system-ui, sans-serif
- **Mood:** Clean, trustworthy, professional, data-readable

### Flutter Font Configuration

```dart
// pubspec.yaml
fonts:
  - family: Inter
    fonts:
      - asset: assets/fonts/Inter-Regular.ttf
        weight: 400
      - asset: assets/fonts/Inter-Medium.ttf
        weight: 500
      - asset: assets/fonts/Inter-SemiBold.ttf
        weight: 600
      - asset: assets/fonts/Inter-Bold.ttf
        weight: 700
      - asset: assets/fonts/Inter-ExtraBold.ttf
        weight: 800
```

### Spacing Variables

| Token | Value | Usage |
|-------|-------|-------|
| `space4` | `4px` | Tight gaps, icon-text micro spacing |
| `space8` | `8px` | Icon-text gap, inline spacing |
| `space12` | `12px` | Between cards |
| `space16` | `16px` | Card internal padding |
| `space20` | `20px` | Subsection gaps |
| `space24` | `24px` | Section gaps |
| `space32` | `32px` | Large section gaps |
| `space40` | `40px` | Page-level padding |
| `space48` | `48px` | Hero sections |
| `space64` | `64px` | Top-level spacing |

---

## Depth / Elevation System

4-level depth system for consistent Z-ordering across all surfaces.

| Level | Surface | Blur | Border | Shadow | Usage |
|-------|---------|------|--------|--------|-------|
| **Level 0** | `#0D0E14` (solid) | None | None | None | Page background, scaffold |
| **Level 1** | `#16181F` @ 70% | `sigma: 8` | `#2D2F3A` @ 30% | `shadow-sm` | List items, inline containers |
| **Level 2** | `#16181F` @ 75% | `sigma: 10` | `#2D2F3A` @ 50% | `shadow-md` | Cards, feed items, glass cards |
| **Level 3** | `#16181F` @ 80% | `sigma: 12` | `#2D2F3A` @ 70% | `shadow-lg` | Bottom sheets, modals, overlays |
| **Level 4** | `#1E2028` @ 90% | `sigma: 16` | `accent` @ 20% | `shadow-glow` | Tooltips, popovers, focused elements |

```dart
class PortfiqDepth {
  // Level 1 — list items, subtle containers
  static const double blurLevel1 = 8;
  static const double opacityLevel1 = 0.70;
  static const double borderOpacityLevel1 = 0.30;

  // Level 2 — standard glass cards
  static const double blurLevel2 = 10;
  static const double opacityLevel2 = 0.75;
  static const double borderOpacityLevel2 = 0.50;

  // Level 3 — bottom sheets, modals
  static const double blurLevel3 = 12;
  static const double opacityLevel3 = 0.80;
  static const double borderOpacityLevel3 = 0.70;

  // Level 4 — tooltips, popovers
  static const double blurLevel4 = 16;
  static const double opacityLevel4 = 0.90;
}
```

---

## Shadow Depths

| Level | Value | Usage |
|-------|-------|-------|
| `shadow-sm` | `BoxShadow(black @ 0.3, blur: 2, offset: (0, 1))` | Subtle lift |
| `shadow-md` | `BoxShadow(black @ 0.4, blur: 8, offset: (0, 4))` | Cards, buttons |
| `shadow-lg` | `BoxShadow(black @ 0.5, blur: 16, offset: (0, 8))` | Modals, dropdowns |
| `shadow-glow` | `BoxShadow(#6366F1 @ 0.3, blur: 12)` | Selected/active elements (Indigo glow) |
| `shadow-tab-glow` | `BoxShadow(#6366F1 @ 0.4, blur: 12, spread: 2)` | Active tab icon |
| `shadow-glass` | `BoxShadow(black @ 0.2, blur: 4, offset: (0, 2))` | Glass card inner shadow |

---

## Style Guidelines

**Style:** Dark Glassmorphism + OLED Optimized

**Keywords:** Frosted glass, dark premium, OLED black, translucent layers, backdrop blur, depth, financial trust, high contrast

**Best For:** Fintech apps, investment dashboards, portfolio trackers, premium mobile apps

---

## Glassmorphism Specification (Refined)

Glassmorphism should be **subtle** — never overwhelming. The frosted effect enhances depth without distracting from financial data.

### Glass Properties

| Property | Subtle (Default) | Medium | Strong |
|----------|-----------------|--------|--------|
| Background Opacity | `0.05` - `0.10` | `0.10` - `0.15` | `0.15` - `0.20` |
| Backdrop Blur (sigma) | `8` | `10` | `12` |
| Border Opacity | `0.30` | `0.50` | `0.70` |
| Usage | List items, tags | Cards, panels | Modals, overlays |

### Glass Card Container (Standard — Level 2)

```dart
Container(
  decoration: BoxDecoration(
    color: Color(0xFF16181F).withOpacity(0.75),
    borderRadius: BorderRadius.circular(16),
    border: Border.all(
      color: Color(0xFF2D2F3A).withOpacity(0.5),
      width: 1,
    ),
    boxShadow: [
      BoxShadow(
        color: Colors.black.withOpacity(0.2),
        blurRadius: 4,
        offset: Offset(0, 2),
      ),
    ],
  ),
  child: ClipRRect(
    borderRadius: BorderRadius.circular(16),
    child: BackdropFilter(
      filter: ImageFilter.blur(sigmaX: 10, sigmaY: 10),
      child: Padding(
        padding: EdgeInsets.all(16),
        child: content,
      ),
    ),
  ),
)
```

| Property | Value |
|----------|-------|
| Background | `Color(0xFF16181F).withOpacity(0.75)` |
| Backdrop Blur | `ImageFilter.blur(sigmaX: 10, sigmaY: 10)` |
| Border | `1px solid Color(0xFF2D2F3A).withOpacity(0.5)` |
| Border Radius | `16px` |
| Inner Shadow | `BoxShadow(black @ 0.2, blur: 4, offset: (0, 2))` |
| Padding | `16px` |

---

## Gradient Border Specification

Gradient borders are used for highlighted/featured cards (briefing, promotions). The gradient acts as the card border, with the inner card slightly inset.

### Structure

```dart
// Outer container = gradient border
Container(
  decoration: BoxDecoration(
    borderRadius: BorderRadius.circular(16),
    gradient: gradientColors, // e.g. Indigo or Amber
  ),
  child: Padding(
    padding: EdgeInsets.all(1.5), // Border thickness
    child: Container(
      decoration: BoxDecoration(
        color: Color(0xFF16181F).withOpacity(0.85),
        borderRadius: BorderRadius.circular(14.5),
      ),
      child: ClipRRect(
        borderRadius: BorderRadius.circular(14.5),
        child: BackdropFilter(
          filter: ImageFilter.blur(sigmaX: 8, sigmaY: 8),
          child: content,
        ),
      ),
    ),
  ),
)
```

| Property | Value |
|----------|-------|
| Border Width | `1.5px` (padding around inner card) |
| Inner Radius | `borderRadius - 1.5` (14.5px for 16px outer) |
| Inner Background Opacity | `0.85` |
| Inner Blur | `sigma: 8` |

### Gradient Border Presets

| Name | Colors | Usage |
|------|--------|-------|
| Morning Briefing | `#6366F1` → `#818CF8` | 06:00-18:00 briefing card |
| Night Briefing | `#F59E0B` → `#FBBF24` | 18:00-06:00 briefing card |
| Accent Fade | `#6366F1` → `transparent` | Subtle highlighted card border |
| Positive Highlight | `#10B981` → `transparent` | Strong positive performance |

---

## Component Specs

### 1. News Card

Extends Glass Card with impact-level accent bar and sentiment badge.

**Left Accent Bar — Gradient (not solid!):**

| Sentiment | Gradient | Direction | Colors |
|-----------|----------|-----------|--------|
| Positive (호재) | `LinearGradient` | top → bottom | `#10B981` → `#059669` |
| Negative (위험) | `LinearGradient` | top → bottom | `#EF4444` → `#DC2626` |
| Neutral (중립) | No accent bar | — | — |

```dart
// Left accent bar — MUST be gradient, not solid color
Positioned(
  left: 0, top: 12, bottom: 12,
  child: Container(
    width: 3,
    decoration: BoxDecoration(
      borderRadius: BorderRadius.circular(1.5),
      gradient: LinearGradient(
        begin: Alignment.topCenter,
        end: Alignment.bottomCenter,
        colors: isPositive
          ? [Color(0xFF10B981), Color(0xFF059669)]
          : [Color(0xFFEF4444), Color(0xFFDC2626)],
      ),
    ),
  ),
)
```

**Press Feedback:**
- Scale: `0.98`
- Opacity: `0.85`
- Duration: `100ms` press / `150ms` release
- Curve: `Curves.easeOutCubic`

---

### 2. Briefing Card

Extends Glass Card with time-of-day gradient border.

| Time | Gradient Colors | Label |
|------|----------------|-------|
| Morning (06:00-18:00) | `#6366F1` → `#818CF8` | Indigo gradient |
| Night (18:00-06:00) | `#F59E0B` → `#FBBF24` | Amber gradient |

---

### 3. ETF Price Display Specification

#### Price Chip (Compact)

```dart
Container(
  padding: EdgeInsets.symmetric(horizontal: 8, vertical: 4),
  decoration: BoxDecoration(
    color: isPositive
      ? Color(0xFF10B981).withOpacity(0.15)
      : Color(0xFFEF4444).withOpacity(0.15),
    borderRadius: BorderRadius.circular(8),
  ),
  child: Text(
    priceChangeText, // e.g. "+2.4%"
    style: TextStyle(
      fontFamily: 'Inter',
      fontSize: 13,
      fontWeight: FontWeight.w600,
      color: isPositive ? Color(0xFF10B981) : Color(0xFFEF4444),
    ),
  ),
)
```

| Direction | Background | Text Color |
|-----------|-----------|------------|
| Positive (+) | `#10B981` @ 15% | `#10B981` |
| Negative (-) | `#EF4444` @ 15% | `#EF4444` |
| Neutral (0) | `#6B7280` @ 15% | `#6B7280` |

#### Large Price Display (ETF Detail Hero)

| Property | Value |
|----------|-------|
| Current Price | Inter, 32px, w800, `#F8FAFC` |
| Change Amount | Inter, 16px, w600, positive/negative color |
| Change Percent | Inside chip (above spec) |
| Ticker Symbol | Inter, 14px, w600, `#9CA3AF`, letter-spacing: 1.2 |

#### Price Count-Up Animation

When price data loads, animate from 0 to actual value:
- Duration: `800ms`
- Curve: `Curves.easeOutExpo`
- Number format: Korean Won (₩) with comma separator
- Decimal: 소수점 없음 for KRW, 2자리 for %

---

### 4. News Card Impact Visual — Accent Bar Gradients

| Impact Level | Left Bar Gradient | Bar Width | Colors |
|-------------|-------------------|-----------|--------|
| **High** | `LinearGradient` top → bottom | `3px` | `#EF4444` → `#DC2626` |
| **Medium** | `LinearGradient` top → bottom | `3px` | `#F59E0B` → `#D97706` |
| **Low** | No accent bar | `0px` | — |

---

### 5. Tab Bar

Bottom navigation bar with glow effect on selection.

```dart
Container(
  color: Color(0xFF0D0E14),
  decoration: BoxDecoration(
    border: Border(
      top: BorderSide(color: Color(0xFF2D2F3A), width: 1),
    ),
  ),
)
```

| State | Icon Color | Label | Glow |
|-------|-----------|-------|------|
| Selected | `#6366F1` (Indigo) | Visible, 10px, w600 | `BoxShadow(#6366F1 @ 0.4, blur: 12, spread: 2)` |
| Unselected | `#6B7280` (Gray) | Hidden (opacity 0) | None |

**Tab Bar Glow Effect:**
- Glow wraps around the icon, not the entire tab area
- Glow color: `Color(0xFF6366F1).withOpacity(0.4)`
- Glow blur: `12px`
- Glow spread: `2px`
- Icon scale selected: `1.1`
- Label slides up from `Offset(0, 0.3)` on selection

**Animation:**
- Icon scale: `1.0` → `1.1`, `200ms`, `easeOutCubic`
- Label opacity: `0.0` → `1.0`, `200ms`, `easeOutCubic`
- Label slide: `Offset(0, 0.3)` → `Offset.zero`, `200ms`, `easeOutCubic`

---

### 6. Search Input

| State | Border | Glow |
|-------|--------|------|
| Default | `1px solid #2D2F3A` | None |
| Focused | `1px solid #6366F1` | `BoxShadow(#6366F1 @ 0.2, blur: 8)` |

| Property | Value |
|----------|-------|
| Background | `#1E2028` |
| Border Radius | `10px` |
| Prefix Icon | Lucide Search, `#9CA3AF` |

---

### 7. Shimmer Loading (Enhanced)

Multi-variant shimmer system matching actual card shapes.

#### Base Shimmer Effect

```dart
ShaderMask(
  shaderCallback: (bounds) {
    return LinearGradient(
      colors: [
        Color(0xFF16181F),   // base
        Color(0xFF252730),   // highlight (brighter than before)
        Color(0xFF16181F),   // base
      ],
      stops: [0.0, 0.5, 1.0],
    ).createShader(bounds);
  },
  child: skeletonShape,
)
```

| Property | Value |
|----------|-------|
| Base Color | `#16181F` |
| Highlight Color | `#252730` (was `#1E2028`, now slightly brighter for better visibility) |
| Animation | Linear gradient sweep, `1500ms` duration, infinite repeat |
| Shape | Card-shaped skeleton matching actual card layout |

#### Shimmer Variants

| Variant | Structure | Usage |
|---------|-----------|-------|
| `ShimmerNewsCard` | Rectangle 100% x 16px + gap + rectangle 80% x 14px + gap + 3 lines | Feed news items |
| `ShimmerBriefingCard` | Gradient border + rectangle 60% x 18px + 2 pill shapes + 2 lines | Briefing banner |
| `ShimmerETFRow` | Circle 40px + column(2 lines) + right-aligned pill | ETF list items |
| `ShimmerChart` | Rectangle 100% x 200px with subtle wave | Chart loading area |

---

### 8. Splash Screen

```dart
Container(
  decoration: BoxDecoration(
    gradient: RadialGradient(
      center: Alignment.center,
      radius: 1.2,
      colors: [
        Color(0xFF1A1B2E), // Center: slight indigo tint
        Color(0xFF0D0E14), // Edge: deep dark
      ],
    ),
  ),
  child: Column(
    mainAxisAlignment: MainAxisAlignment.center,
    children: [
      // Logo text with gradient
      ShaderMask(
        shaderCallback: (bounds) => LinearGradient(
          colors: [Color(0xFF6366F1), Color(0xFF818CF8)],
        ).createShader(bounds),
        child: Text('Portfiq', style: TextStyle(
          fontSize: 48, fontWeight: FontWeight.w800, color: Colors.white,
        )),
      ),
      SizedBox(height: 12),
      Text('내 ETF 맞춤 브리핑', style: TextStyle(
        fontSize: 14, color: Color(0xFF9CA3AF),
      )),
    ],
  ),
)
```

| Property | Value |
|----------|-------|
| Background | `RadialGradient` center `#1A1B2E` to edge `#0D0E14` |
| Logo Text | "Portfiq", 48px, weight 800, gradient `#6366F1` → `#818CF8` |
| Subtitle | "내 ETF 맞춤 브리핑", 14px, `#9CA3AF` |
| Logo Fade-in | `600ms`, `easeOutCubic` |
| Logo Scale-in | `0.8` → `1.0`, `600ms`, `easeOutCubic` |
| Subtitle Fade-in | `400ms` delay + `400ms` duration |

---

## Typography Scale

| Token | Size | Weight | Letter Spacing | Line Height | Usage |
|-------|------|--------|-----------------|-------------|-------|
| Display | 28px | w800 | -0.5 | 1.2 | Large numbers, prices |
| Title | 22px | w700 | -0.3 | 1.3 | Section headers |
| Subtitle | 17px | w600 | 0 | 1.4 | Card headlines |
| Body | 15px | w400 | 0 | 1.5 | Body text |
| Caption | 12px | w400 | 0 | 1.3 | Secondary info, timestamps |
| Label | 11px | w600 | 1.2 | 1.2 | Badges, chips, tags |

```dart
class PortfiqTypography {
  static const display = TextStyle(
    fontFamily: 'Inter', fontSize: 28, fontWeight: FontWeight.w800,
    letterSpacing: -0.5, height: 1.2, color: Color(0xFFF8FAFC),
  );
  static const title = TextStyle(
    fontFamily: 'Inter', fontSize: 22, fontWeight: FontWeight.w700,
    letterSpacing: -0.3, height: 1.3, color: Color(0xFFF8FAFC),
  );
  static const subtitle = TextStyle(
    fontFamily: 'Inter', fontSize: 17, fontWeight: FontWeight.w600,
    height: 1.4, color: Color(0xFFF8FAFC),
  );
  static const body = TextStyle(
    fontFamily: 'Inter', fontSize: 15, fontWeight: FontWeight.w400,
    height: 1.5, color: Color(0xFFF8FAFC),
  );
  static const caption = TextStyle(
    fontFamily: 'Inter', fontSize: 12, fontWeight: FontWeight.w400,
    height: 1.3, color: Color(0xFF9CA3AF),
  );
  static const label = TextStyle(
    fontFamily: 'Inter', fontSize: 11, fontWeight: FontWeight.w600,
    letterSpacing: 1.2, height: 1.2, color: Color(0xFF9CA3AF),
  );
}
```

---

## Animation Tokens

| Token | Duration | Usage |
|-------|----------|-------|
| Fast | `100ms` | Press feedback, toggle, chip tap |
| Normal | `200ms` | Tab switch, chip appear, state change |
| Slow | `300ms` | Screen transition, modal open/close |
| Splash | `600ms` | Splash fade-in/scale-in |
| Shimmer | `1500ms` | Shimmer loading cycle |
| Price Count-Up | `800ms` | Price number animation |
| Default Curve | `Curves.easeOutCubic` | Standard easing for most interactions |
| Bounce Curve | `Curves.elasticOut` | Subtle bounce for added items |
| Spring Curve | `Curves.easeOutBack` | Overshoot spring for card entry |
| Decelerate Curve | `Curves.easeOutExpo` | Number count-up, value animations |

```dart
class PortfiqAnimation {
  static const fast = Duration(milliseconds: 100);
  static const normal = Duration(milliseconds: 200);
  static const slow = Duration(milliseconds: 300);
  static const splash = Duration(milliseconds: 600);
  static const shimmer = Duration(milliseconds: 1500);
  static const priceCountUp = Duration(milliseconds: 800);
  static const cardRelease = Duration(milliseconds: 150);

  static const defaultCurve = Curves.easeOutCubic;
  static const bounceCurve = Curves.elasticOut;
  static const springCurve = Curves.easeOutBack;
  static const decelerateCurve = Curves.easeOutExpo;
}
```

---

## Micro-interactions (Enhanced)

| Interaction | Transform | Duration | Curve |
|------------|-----------|----------|-------|
| Card press | `scale(0.98)` + `opacity(0.85)` | `100ms` | `easeOutCubic` |
| Card release | `scale(1.0)` + `opacity(1.0)` | `150ms` | `easeOutCubic` |
| List item appear | `SlideTransition` from right 20px + `FadeTransition` | staggered `50ms` per item | `easeOutCubic` |
| Tab switch | Icon scale `1.0` → `1.1` → `1.0` | `200ms` | `easeOutCubic` |
| Card entry (page load) | `scale(0.95)` → `scale(1.0)` + fade | `300ms`, staggered `80ms` | `easeOutBack` (spring) |
| Price value change | Old value fades out ↑, new value fades in ↓ | `200ms` | `easeOutCubic` |
| Swipe dismiss | `SlideTransition` + `FadeTransition` on horizontal drag | velocity-based | `easeOutCubic` |

### Haptic Feedback Guide

| Action | Haptic Type | Flutter API |
|--------|------------|-------------|
| Card tap | Light impact | `HapticFeedback.lightImpact()` |
| Button confirm (CTA) | Medium impact | `HapticFeedback.mediumImpact()` |
| Destructive action | Heavy impact | `HapticFeedback.heavyImpact()` |
| Toggle switch | Selection click | `HapticFeedback.selectionClick()` |
| Pull-to-refresh trigger | Medium impact | `HapticFeedback.mediumImpact()` |
| Error / validation fail | Notification error | `HapticFeedback.vibrate()` |

**Rule:** Only use haptic for meaningful state changes. Never for scroll, hover, or passive interactions.

---

## Pull-to-Refresh (Custom)

Custom branded refresh indicator replacing the default Material indicator.

| Property | Value |
|----------|-------|
| Indicator Color | `#6366F1` (Indigo) |
| Background | Transparent |
| Style | Three pulsing dots or custom Indigo spinner |
| Pull Distance | `80px` trigger threshold |
| Displacement | `40px` (how far indicator sits from top) |
| Haptic | `HapticFeedback.mediumImpact()` at trigger point |
| Animation | Dots scale `0.6` → `1.0` sequentially, `200ms` stagger |

```dart
// Custom refresh indicator
RefreshIndicator(
  color: Color(0xFF6366F1),
  backgroundColor: Colors.transparent,
  strokeWidth: 2.5,
  displacement: 40,
  onRefresh: _onRefresh,
  child: listView,
)
```

---

## Chart Guidelines (ETF Detail Page)

| Chart Type | Use Case | Library |
|-----------|----------|---------|
| Line Chart | Price history, performance trend | `fl_chart` |
| Sparkline | Inline mini price chart in ETF rows | `fl_chart` (minimal) |
| Gauge / Bullet | Performance vs target | `fl_chart` custom |
| Waterfall | Cumulative changes, P&L breakdown | `fl_chart` custom |

**Chart Colors:**
- Positive trend line: `#10B981`, line width `2px`, filled area `#10B981` @ 5%
- Negative trend line: `#EF4444`, line width `2px`, filled area `#EF4444` @ 5%
- Grid lines: `#2D2F3A` @ 30%, dashed
- Chart background: transparent (sits on glass card)
- Tooltip: Glass card style (Level 4 depth) with backdrop blur
- Crosshair: `#6366F1` @ 50%, 1px dashed vertical line
- Selected dot: `#6366F1` with glow shadow

**Chart Interaction:**
- Touch to show tooltip with crosshair
- Horizontal drag to scrub through timeline
- Haptic: `selectionClick` on each data point during scrub

---

## Icon System

- **Package:** `lucide_icons` (Flutter package)
- **Icon Size Standard:** 20px (tab bar), 24px (general), 16px (inline)
- **Icon Color:** follows text color hierarchy (primary/secondary/tertiary)

---

## Anti-Patterns (Do NOT Use)

- Light backgrounds on any surface (OLED dark only)
- Emojis as icons — use SVG icons (Lucide icons via `lucide_icons` package)
- Missing touch feedback — all tappable elements need press state
- Low contrast text — maintain 4.5:1 minimum contrast ratio on dark backgrounds
- Instant state changes — always use transitions (100-300ms)
- Invisible focus states — focus states must be visible for accessibility
- Pure white text (`#FFFFFF`) — use `#F8FAFC` for softer contrast
- Continuous decorative animations — only use for loading indicators
- Force linear unskippable onboarding flows
- Light mode default — dark mode is the only mode
- Solid color accent bars on news cards — use gradient
- Haptic on every interaction — only on meaningful state changes
- `BackdropFilter` everywhere — only use where depth matters (cards, modals, tooltips)

---

## Pre-Delivery Checklist

Before delivering any UI code, verify:

- [ ] All surfaces use dark palette (no light backgrounds)
- [ ] Glass cards use `BackdropFilter` with correct blur per depth level
- [ ] All icons from Lucide icon set (no emojis)
- [ ] All tappable elements have press feedback (scale 0.98 + opacity 0.85)
- [ ] Text contrast 4.5:1 minimum on dark backgrounds
- [ ] Focus states visible for keyboard/accessibility navigation
- [ ] `MediaQuery.disableAnimations` respected
- [ ] Responsive: 375px (iPhone SE), 390px (iPhone 14), 428px (iPhone 14 Pro Max)
- [ ] No horizontal scroll unintended
- [ ] Shimmer loading states for all async content (correct variant)
- [ ] ETF price chips use correct positive/negative/neutral colors
- [ ] News card accent bars use **gradient** (not solid color)
- [ ] Tab bar glow effect on selected tab
- [ ] Staggered list item animations on page load
- [ ] Typography scale matches spec (Display/Title/Subtitle/Body/Caption/Label)
- [ ] 4px spacing rhythm followed consistently
- [ ] Haptic feedback on meaningful interactions only
- [ ] Price count-up animations on data load
- [ ] Pull-to-refresh uses branded Indigo indicator
- [ ] Depth system applied correctly (Level 0-4)

---

## Flutter Theme Configuration

```dart
class PortfiqTheme {
  static ThemeData get darkTheme => ThemeData(
    brightness: Brightness.dark,
    scaffoldBackgroundColor: Color(0xFF0D0E14),
    colorScheme: ColorScheme.dark(
      primary: Color(0xFF6366F1),
      secondary: Color(0xFF818CF8),
      surface: Color(0xFF16181F),
      error: Color(0xFFEF4444),
      onPrimary: Color(0xFFF8FAFC),
      onSecondary: Color(0xFFF8FAFC),
      onSurface: Color(0xFFF8FAFC),
      onError: Color(0xFFF8FAFC),
    ),
    textTheme: TextTheme(
      displayLarge: PortfiqTypography.display,
      titleLarge: PortfiqTypography.title,
      titleMedium: PortfiqTypography.subtitle,
      bodyMedium: PortfiqTypography.body,
      bodySmall: PortfiqTypography.caption,
      labelSmall: PortfiqTypography.label,
    ),
    fontFamily: 'Inter',
    cardTheme: CardTheme(
      color: Color(0xFF16181F),
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(16),
      ),
      elevation: 0,
    ),
    bottomNavigationBarTheme: BottomNavigationBarThemeData(
      backgroundColor: Color(0xFF0D0E14),
      selectedItemColor: Color(0xFF6366F1),
      unselectedItemColor: Color(0xFF6B7280),
    ),
    inputDecorationTheme: InputDecorationTheme(
      filled: true,
      fillColor: Color(0xFF1E2028),
      border: OutlineInputBorder(
        borderRadius: BorderRadius.circular(10),
        borderSide: BorderSide(color: Color(0xFF2D2F3A)),
      ),
      focusedBorder: OutlineInputBorder(
        borderRadius: BorderRadius.circular(10),
        borderSide: BorderSide(color: Color(0xFF6366F1)),
      ),
    ),
  );
}
```

---

## Flutter Implementation Guide

> This section provides the exact spec for Flutter developers to implement. **No ambiguity — follow these values exactly.**

### theme.dart — New Constants to Add

```dart
// Add to PortfiqTheme class:
static const Color positiveGradientEnd = Color(0xFF059669); // for gradient accent bars
static const Color accentFade = Color(0x006366F1);          // transparent accent for gradient borders

// Add to PortfiqAnimation class:
static const Duration priceCountUp = Duration(milliseconds: 800);
static const Duration splash = Duration(milliseconds: 600);
static const Curve springCurve = Curves.easeOutBack;
static const Curve decelerateCurve = Curves.easeOutExpo;

// Add new class:
class PortfiqDepth {
  PortfiqDepth._();
  static const double blurLevel1 = 8;
  static const double opacityLevel1 = 0.70;
  static const double borderOpacityLevel1 = 0.30;
  static const double blurLevel2 = 10;
  static const double opacityLevel2 = 0.75;
  static const double borderOpacityLevel2 = 0.50;
  static const double blurLevel3 = 12;
  static const double opacityLevel3 = 0.80;
  static const double borderOpacityLevel3 = 0.70;
  static const double blurLevel4 = 16;
  static const double opacityLevel4 = 0.90;
}

// Add to PortfiqGradients class:
static const positiveAccent = LinearGradient(
  begin: Alignment.topCenter,
  end: Alignment.bottomCenter,
  colors: [Color(0xFF10B981), Color(0xFF059669)],
);
static const accentFade = LinearGradient(
  colors: [Color(0xFF6366F1), Color(0x006366F1)],
);
```

### Widget-by-Widget Changes

#### `glass_card.dart` — Depth-Aware

| Change | Detail |
|--------|--------|
| Add `depth` parameter | `int depth = 2` (default Level 2) |
| Apply depth-based blur, opacity, border | Use `PortfiqDepth` constants |
| Keep backward compatibility | Existing `enableBlur` stays, `depth` overrides when set |

#### `news_card.dart` — Gradient Accent Bar

| Change | Detail |
|--------|--------|
| Replace solid `color: accentColor` | Use `gradient: PortfiqGradients.positiveAccent` or `highImpact` |
| Add haptic on tap | `HapticFeedback.lightImpact()` in `PressableCard.onTap` |

#### `loading_shimmer.dart` — Brighter Highlight + Variants

| Change | Detail |
|--------|--------|
| Change highlight color | `#1E2028` → `#252730` for better visibility |
| Add `ShimmerNewsCard` widget | Skeleton matching news card layout |
| Add `ShimmerBriefingCard` widget | Skeleton with gradient border placeholder |
| Add `ShimmerETFRow` widget | Circle + 2 lines + right pill |
| Add `ShimmerChart` widget | Full-width rectangle with subtle wave |

#### `bottom_tab_bar.dart` — No Changes

Current implementation already matches spec (glow, scale, label animation).

#### `etf_chip.dart` — Add Neutral State

| Change | Detail |
|--------|--------|
| Handle `changePercent == 0` | Use `#6B7280` @ 15% background, `#6B7280` text |

#### `briefing_card.dart` — No Changes

Current implementation already uses gradient borders correctly.

#### `pressable_card.dart` — Add Haptic

| Change | Detail |
|--------|--------|
| Add `hapticOnTap` parameter | `bool hapticOnTap = true` |
| Call `HapticFeedback.lightImpact()` | In `_onTapDown` when `hapticOnTap` is true |
| Respect reduced motion | Check `MediaQuery.disableAnimations` to skip animation |

### New Widgets to Create

| Widget | File | Description |
|--------|------|-------------|
| `PriceCountUp` | `lib/shared/widgets/price_count_up.dart` | Animated number that counts from 0 to value on load. Inter font, `800ms`, `easeOutExpo` curve. Accepts `value`, `prefix` (₩), `suffix` (%), `style`. |
| `ShimmerNewsCard` | `lib/shared/widgets/shimmer_variants.dart` | News card skeleton — title line (100% w, 16h), gap, subtitle (80% w, 14h), gap, 3 body lines |
| `ShimmerBriefingCard` | same file | Briefing skeleton with gradient border placeholder |
| `ShimmerETFRow` | same file | ETF list row skeleton |
| `ShimmerChart` | same file | Chart area placeholder |
| `AnimatedListItem` | `lib/shared/widgets/animated_list_item.dart` | Wrapper that applies staggered slide+fade on first build. Params: `index`, `child`. Uses `easeOutBack` spring, `300ms` + `80ms * index` delay. |

### Animation Curves & Durations Reference Table

| Animation | Duration | Curve | Trigger |
|-----------|----------|-------|---------|
| Card press down | `100ms` | `easeOutCubic` | `onTapDown` |
| Card release | `150ms` | `easeOutCubic` | `onTapUp` / `onTapCancel` |
| Tab icon scale | `200ms` | `easeOutCubic` | Tab selection change |
| List item stagger | `300ms` + `80ms * index` | `easeOutBack` | Page load / data refresh |
| Price count-up | `800ms` | `easeOutExpo` | Data loaded |
| Price value change | `200ms` | `easeOutCubic` | Realtime price update |
| Shimmer sweep | `1500ms` (loop) | `linear` | While loading |
| Splash logo | `600ms` | `easeOutCubic` | App launch |
| Screen transition | `300ms` | `easeOutCubic` | Navigation push/pop |
| Pull-to-refresh dots | `200ms` stagger | `easeOutCubic` | Pull gesture |
| Modal/sheet enter | `300ms` | `easeOutCubic` | Open trigger |
| Swipe dismiss | velocity-based | `easeOutCubic` | Horizontal drag |

---

*This document is the single source of truth for all Portfiq UI implementation. Page-specific overrides are in `design-system/portfiq/pages/[page].md`.*
