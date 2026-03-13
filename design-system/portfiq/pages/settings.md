# Settings Page Overrides

> **PROJECT:** Portfiq
> **Updated:** 2026-03-13
> **Page Type:** Settings / Preferences

> **IMPORTANT:** Rules in this file **override** the Master file (`design-system/portfiq/MASTER.md`).
> Only deviations from the Master are documented here. For all other rules, refer to the Master.

---

## Page Structure

```
Scaffold (bg: #0D0E14)
├── AppBar
│   └── Center: "설정"
├── Body: ListView
│   ├── Section: 내 ETF
│   │   └── "ETF 관리" row → ETF management page
│   ├── Section: 브리핑 알림
│   │   ├── "아침 브리핑" toggle row
│   │   ├── "저녁 브리핑" toggle row
│   │   └── "알림 시간" row → time picker
│   ├── Section: 앱 정보
│   │   ├── "버전" row (value: version string)
│   │   ├── "개인정보 처리방침" row → WebView
│   │   └── "이용약관" row → WebView
│   └── Section: 기타
│       ├── "문의하기" row → email
│       └── "로그아웃" row (destructive)
└── BottomTabBar (index: 3)
```

---

## Layout Overrides

- **Layout:** Grouped `ListView` with section headers
- **Page padding:** `16px` horizontal
- **Section spacing:** `24px` between sections
- **Section header:** Label (11px, w600), `#6B7280`, letter-spacing `1.2`, uppercase

---

## Component Overrides

### Settings Row
- Height: `52px`
- Background: transparent (no card)
- Left: icon (Lucide, 20px, `#9CA3AF`) + label (15px, w400, `#F8FAFC`)
- Right: value text (14px, `#6B7280`) or chevron (Lucide `chevron-right`, 16px, `#6B7280`) or toggle
- Divider: `#2D2F3A` @ 30%, below each row, `52px` left indent
- Tap: Full row tappable, `HapticFeedback.selectionClick()`
- Press feedback: `opacity(0.7)`, `100ms` (no scale — flat list style)

### Toggle Switch
- Track on: `#6366F1`
- Track off: `#2D2F3A`
- Thumb: `#F8FAFC`
- Size: Standard Material 3 switch
- Animation: `200ms`, `easeOutCubic`
- Haptic: `HapticFeedback.selectionClick()` on toggle

### Destructive Row ("로그아웃")
- Text color: `#EF4444` (negative red)
- Icon color: `#EF4444`
- Confirmation: Show alert dialog before action
  - Dialog: GlassCard Level 3, "정말 로그아웃 하시겠어요?" + "취소" / "로그아웃"
  - "로그아웃" button: `#EF4444` bg

### Section Headers
- Font: Label (11px, w600), letter-spacing `1.2`
- Color: `#6B7280`
- Margin: `24px` top, `8px` bottom
- Transform: uppercase

---

## Animations

- **Toggle:** Track color morphs `200ms`, `easeOutCubic`
- **Row tap:** Opacity `1.0` → `0.7` → `1.0`, `100ms`
- **Dialog enter:** Scale `0.95` → `1.0` + fade, `200ms`, `easeOutCubic`
- **Page enter:** No special animation (tab switch handles it)

---

## Accessibility Overrides

- All toggles: semantic label describing current state
- Minimum touch target: `44px x 44px`
- Respect `MediaQuery.disableAnimations` — skip all transition animations
- Focus indicators: `#6366F1` border on focused row
- Screen reader: Row reads "label, current value, button/switch"

---

## Recommendations (from Engine)

- Minimal glow effects (subtle BoxShadow on focused elements)
- High readability with sufficient contrast
- Visible focus states for accessibility navigation
- Check `MediaQuery.disableAnimations` for all animations
