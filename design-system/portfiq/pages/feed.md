# Feed Page Overrides

> **PROJECT:** Portfiq
> **Updated:** 2026-03-13
> **Page Type:** News Feed / Scrollable Card List

> **IMPORTANT:** Rules in this file **override** the Master file (`design-system/portfiq/MASTER.md`).
> Only deviations from the Master are documented here. For all other rules, refer to the Master.

---

## Page Structure

```
SafeArea
├── AppBar (transparent, no elevation)
│   ├── Left: "Portfiq" logo text (gradient)
│   └── Right: Search icon (Lucide)
├── Body: RefreshIndicator
│   └── CustomScrollView
│       ├── SliverToBoxAdapter: BriefingCard (gradient border)
│       ├── SliverToBoxAdapter: SectionHeader "뉴스 피드"
│       ├── SliverToBoxAdapter: Filter chips (sentiment/ETF)
│       └── SliverList: NewsCard items (staggered entry)
└── BottomTabBar (index: 0)
```

---

## Layout Overrides

- **Layout:** Single column, full-width scroll (`CustomScrollView`)
- **Page padding:** `16px` horizontal, `0px` top (AppBar handles)
- **Card spacing:** `12px` between news cards
- **Briefing to news gap:** `20px`
- **Filter chip bar:** Horizontal scroll, `8px` chip spacing, `16px` left padding

## Spacing Overrides

- **Content density:** Medium — balanced information and whitespace
- **Briefing card margin:** `16px` horizontal
- **News cards margin:** `16px` horizontal

---

## Component Overrides

### AppBar
- Background: transparent (blends with page bg `#0D0E14`)
- Left: "Portfiq" text, 20px, w700, gradient `#6366F1` → `#818CF8`
- Right: Lucide search icon, 22px, `#9CA3AF`
- Height: standard (56px)

### Filter Chips
- Horizontal `ListView` with scroll
- Selected: `#6366F1` @ 20% bg + `#6366F1` text + `#6366F1` border
- Unselected: `#1E2028` bg + `#9CA3AF` text + no border
- Chip radius: `24px` (pill)
- Chip padding: `12px` horizontal, `8px` vertical
- Font: 14px, w500

### News Cards
- Use `PressableCard` wrapping `GlassCard` (Level 2 depth)
- Left accent bar: **gradient** per sentiment (not solid)
- Staggered entry animation: `300ms` + `80ms * index`, `easeOutBack`
- On tap: navigate to article detail with `HapticFeedback.lightImpact()`

### Empty State
- When no news: centered Lucide `newspaper` icon + "새로운 뉴스가 없습니다" message
- If no ETF registered: "ETF를 등록하면 맞춤 뉴스를 받을 수 있어요" + "ETF 등록하기" action button

---

## Animations

- **Pull-to-refresh:** Custom Indigo indicator (see MASTER.md)
- **Feed load:** Shimmer → staggered card entry
- **Briefing card entry:** Scale `0.95` → `1.0` + fade, `300ms`, `easeOutBack`
- **Filter chip tap:** Scale `0.95` → `1.0`, `100ms`, `easeOutCubic`
- **Number animations:** Count-up for briefing ETF change percentages

---

## Recommendations (from Engine)

- Number animations (count-up) for ETF change values
- Trend direction indicators: arrows animate in
- Profit/loss color transitions: smooth `200ms` color change on data update
- High readability: Body text min `14px`, line height `1.5`
