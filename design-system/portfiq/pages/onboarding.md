# Onboarding Page Overrides

> **PROJECT:** Portfiq
> **Updated:** 2026-03-13
> **Page Type:** Onboarding Flow / Progressive Disclosure

> **IMPORTANT:** Rules in this file **override** the Master file (`design-system/portfiq/MASTER.md`).
> Only deviations from the Master are documented here. For all other rules, refer to the Master.

---

## Page Structure

```
Scaffold (bg: #0D0E14)
├── Body: PageView (horizontal swipe)
│   ├── Page 1: Welcome
│   │   ├── Portfiq logo (gradient text, scale-in)
│   │   ├── Tagline "내 ETF 맞춤 브리핑"
│   │   └── "시작하기" button
│   ├── Page 2: ETF Selection
│   │   ├── Title "관심 ETF를 선택하세요"
│   │   ├── Search input
│   │   ├── Popular ETF chips
│   │   └── Selected ETF list
│   └── Page 3: Notification Setup
│       ├── Title "브리핑 알림을 받을까요?"
│       ├── Morning/Night toggle cards
│       └── Time picker
├── Bottom: Navigation Row
│   ├── Left: "건너뛰기" text button (skip)
│   ├── Center: Page indicator dots
│   └── Right: "다음" / "완료" button
```

---

## Layout Overrides

- **Layout:** Horizontal `PageView` with 3 steps
- **Page padding:** `24px` horizontal, `48px` top
- **Button area:** Fixed bottom, `16px` horizontal padding, `24px` bottom safe area
- **Content alignment:** Center vertical within page area (above button bar)

---

## Component Overrides

### Page Indicator Dots
- Active: `8px` height, `#6366F1`, `borderRadius: 4`
- Inactive: `8px` x `8px`, `#2D2F3A`, `borderRadius: 4`
- Active animates width: `8px` → `24px` (pill), `200ms`, `easeOutCubic`
- Spacing: `8px`

### Welcome Page (Step 1)
- Logo: Same as splash — gradient text "Portfiq", 48px, w800
- Logo animation: Scale `0.8` → `1.0` + fade, `600ms`, `easeOutCubic`
- Tagline: 16px, `#9CA3AF`, fade in `400ms` delay
- Background: Subtle radial gradient (same as splash)

### ETF Selection Page (Step 2)
- Search input: As per MASTER.md search spec
- Popular chips: Horizontally scrollable
  - Default: `#1E2028` bg, `#9CA3AF` text, pill shape
  - Selected: `#6366F1` @ 20% bg, `#6366F1` text, `#6366F1` border
  - Tap animation: Scale `0.95`, `100ms`, + `HapticFeedback.selectionClick()`
- Selected ETF list:
  - Slide in from right, staggered `50ms`
  - Remove: Slide out left + fade, `200ms`
  - Each item: GlassCard Level 1, ETF name + ticker + remove icon

### Notification Setup Page (Step 3)
- Toggle cards: GlassCard Level 2
  - Morning card: Indigo gradient border when enabled
  - Night card: Amber gradient border when enabled
  - Disabled: Standard border `#2D2F3A`
  - Toggle animation: border gradient fade in, `300ms`
- Time picker: Bottom sheet with wheel picker, GlassCard Level 3

### Skip & Navigation
- "건너뛰기" (Skip): `TextButton`, `#9CA3AF`, 14px
- "다음" (Next): `ElevatedButton`, `#6366F1` bg, full width
- "완료" (Done): Same as Next
- Back gesture: Swipe right or back button

---

## Color Overrides

- **Step progression colors:**
  - Step 1: Indigo accent (`#6366F1`) — brand introduction
  - Step 2: Indigo accent — selection/action
  - Step 3: Indigo accent — confirmation

---

## Animations

- **Page transition:** Horizontal slide with parallax (background moves slower)
- **Logo entry:** Scale + fade, `600ms`, `easeOutCubic`
- **ETF chip selection:** Scale bounce `0.95` → `1.02` → `1.0`, `200ms`, `easeOutBack`
- **Selected ETF add:** Slide in from right + fade, `300ms`, `easeOutBack`
- **Selected ETF remove:** Slide out left + fade, `200ms`, `easeOutCubic`
- **Page indicator dot:** Width morph `8px` → `24px`, `200ms`, `easeOutCubic`
- **Button state:** Disabled → enabled smooth color transition, `200ms`

---

## Recommendations (from Engine)

- Soft press animations (200ms ease-out) for all interactive elements
- Smooth transitions between steps
- Provide Skip and Back buttons at all times
- Progressive disclosure: only show necessary info per step
- Fluid animations (400-600ms curves) for page transitions
- Haptic feedback on ETF selection/deselection
