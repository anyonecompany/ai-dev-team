# Briefing Page Overrides

> **PROJECT:** Portfiq
> **Updated:** 2026-03-13
> **Page Type:** Briefing Detail / Dashboard View

> **IMPORTANT:** Rules in this file **override** the Master file (`design-system/portfiq/MASTER.md`).
> Only deviations from the Master are documented here. For all other rules, refer to the Master.

---

## Page Structure

```
Scaffold (bg: #0D0E14)
├── AppBar
│   ├── Left: Back arrow
│   ├── Center: "오늘의 브리핑" / "오늘의 마감"
│   └── Right: Share icon (Lucide share-2)
├── Body: SingleChildScrollView
│   ├── Section: Hero Summary
│   │   ├── Time-of-day greeting text
│   │   ├── Date label (yyyy.MM.dd)
│   │   └── "AI 분석" badge
│   ├── Section: ETF Performance Overview
│   │   ├── ETF chips with price count-up
│   │   └── Summary paragraph
│   ├── Section: Key Insights
│   │   ├── Numbered insight cards (GlassCard Level 2)
│   │   └── Each card: icon + title + description
│   ├── Section: Market Context
│   │   └── Brief market conditions paragraph
│   └── Section: Action Items
│       └── Checkbox-style items (tap to mark)
└── BottomTabBar (hidden on this page — pushed from feed)
```

---

## Layout Overrides

- **Layout:** Single column, narrow focus
- **Max content width:** `428px` (largest iPhone width constraint)
- **Page padding:** `20px` horizontal (wider than feed for reading comfort)
- **Section spacing:** `24px` between sections
- **Content density:** Low — focus on clarity and readability

## Spacing Overrides

- **Hero section padding:** `24px` top
- **Insight card spacing:** `12px` between cards
- **Paragraph line height:** `1.6` (higher than default for reading)

---

## Component Overrides

### Hero Summary
- Greeting: "좋은 아침이에요" / "오늘 하루도 수고했어요"
- Font: Title (22px, w700), `#F8FAFC`
- Date: Caption (12px), `#9CA3AF`
- "AI 분석" badge: `#6366F1` @ 15% bg, `#6366F1` text, pill shape

### ETF Performance Overview
- ETF chips laid out in `Wrap` (same as feed briefing card)
- Price values: `PriceCountUp` animation, `800ms`, `easeOutExpo`
- Summary text: Body (15px), `#9CA3AF`, line height `1.6`

### Insight Cards
- Use `GlassCard` Level 2 depth
- Numbered circle: `28px` diameter, `#6366F1` bg, white number
- Title: Subtitle (17px, w600), `#F8FAFC`
- Description: Body (14px), `#9CA3AF`, max 3 lines
- Card entry: Staggered `300ms` + `100ms * index`, `easeOutBack`

### Mock Data Banner
- When briefing is sample data:
- Amber warning banner inside card
- `#F59E0B` @ 10% bg + `#F59E0B` @ 30% border
- Icon: `auto_awesome` (sparkle), `#F59E0B`
- Text: "AI 분석 준비 중 — 샘플 데이터입니다"

---

## Animations

- **Page enter:** Slide up from bottom `Offset(0, 0.05)` + fade, `300ms`, `easeOutCubic`
- **KPI values:** `PriceCountUp` animation on data load
- **Insight card stagger:** Each card slides in + fades, staggered `100ms`
- **Alert pulse:** Warning banner has subtle opacity pulse `0.8` → `1.0`, `2000ms`, loop (only for urgent items)
- **Share button:** Scale `0.9` → `1.0` on tap, `100ms`

---

## Recommendations (from Engine)

- KPI value animations (count-up) for all numeric data
- Trend arrow direction animations
- Metric card subtle lift on entry
- High readability with generous line spacing
- Low content density — user should absorb, not scan
