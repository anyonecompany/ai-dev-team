# ETF Detail Page Overrides

> **PROJECT:** Portfiq
> **Updated:** 2026-03-13
> **Page Type:** Product Detail / Data Dashboard

> **IMPORTANT:** Rules in this file **override** the Master file (`design-system/portfiq/MASTER.md`).
> Only deviations from the Master are documented here. For all other rules, refer to the Master.

---

## Page Structure

```
Scaffold (bg: #0D0E14)
├── SliverAppBar (collapsing)
│   ├── Left: Back arrow
│   ├── Center: ETF ticker (appears on collapse)
│   └── Right: Star (favorite toggle)
├── Body: CustomScrollView
│   ├── SliverToBoxAdapter: Price Hero Section
│   │   ├── ETF name (Korean)
│   │   ├── Ticker symbol (e.g. "KODEX 200")
│   │   ├── Current price (large, count-up)
│   │   ├── Change amount + change percent chip
│   │   └── Last updated timestamp
│   ├── SliverToBoxAdapter: Chart Section
│   │   ├── Period selector chips (1D/1W/1M/3M/1Y/ALL)
│   │   └── Line chart (fl_chart)
│   ├── SliverToBoxAdapter: Holdings Section
│   │   ├── SectionHeader "구성 종목"
│   │   └── Top 5 holdings list (GlassCard Level 1)
│   ├── SliverToBoxAdapter: Related News Section
│   │   ├── SectionHeader "관련 뉴스"
│   │   └── Compact news cards (max 3)
│   └── SliverToBoxAdapter: Info Section
│       ├── SectionHeader "ETF 정보"
│       └── Key-value info rows
└── BottomSafeArea: Action Bar (optional)
```

---

## Layout Overrides

- **Layout:** Single column with collapsing header
- **Page padding:** `16px` horizontal
- **Section spacing:** `24px` between sections
- **Chart height:** `240px` (responsive: `min(240, screenHeight * 0.3)`)

---

## Component Overrides

### Price Hero Section
- ETF name: Title (22px, w700), `#F8FAFC`
- Ticker: Label (11px, w600), `#9CA3AF`, letter-spacing `1.2`
- Current price: Display (28px, w800), `#F8FAFC`, Inter font
  - **Count-up animation:** `0` → actual, `800ms`, `easeOutExpo`
  - **Format:** Won prefix, comma separator, no decimal
- Change amount: 16px, w600, positive/negative color
  - **+** prefix for positive, **-** for negative
- Change percent: ETF price chip (see MASTER.md)
- Updated: Caption (12px), `#6B7280`

### Chart Section
- **Period selector chips:**
  - Selected: `#6366F1` @ 20% bg + `#6366F1` text
  - Unselected: `#1E2028` bg + `#9CA3AF` text
  - Chip radius: `8px`
  - Spacing: `8px`
  - Animation: Scale `0.95` on tap, `100ms`

- **Line chart (fl_chart):**
  - Positive: `#10B981` line (2px) + `#10B981` @ 5% fill area
  - Negative: `#EF4444` line (2px) + `#EF4444` @ 5% fill area
  - Grid: `#2D2F3A` @ 30%, horizontal only, dashed
  - Y-axis labels: Caption (12px), `#6B7280`
  - X-axis labels: Caption (12px), `#6B7280`
  - Touch tooltip: GlassCard Level 4 depth, price + date
  - Crosshair: `#6366F1` @ 50%, 1px dashed vertical
  - Selected dot: 6px circle, `#6366F1`, glow shadow
  - **Chart animation:** Line draws left-to-right, `600ms`, `easeOutCubic`
  - **Period switch:** Crossfade old → new chart, `300ms`

### Holdings Section
- Each row: GlassCard Level 1 depth
- Layout: `Row` — stock name + weight % + mini sparkline
- Stock name: Body (15px), `#F8FAFC`
- Weight: Caption (12px, w600), `#9CA3AF`
- Sparkline: `48px` wide, `24px` tall, 1px line, positive/negative color

### Related News (Compact)
- Smaller news cards: No accent bar, no impact reason
- Show: headline + source + time
- Max 3 items, "더 보기" link at bottom
- Font: Subtitle (15px, w600) for headline

### Info Section
- Key-value rows on transparent background
- Key: Caption (12px), `#6B7280`
- Value: Body (15px, w500), `#F8FAFC`
- Row height: `44px`
- Divider: `#2D2F3A` @ 30%, 1px

---

## Animations

- **Price hero:** Count-up on load, `800ms`, `easeOutExpo`
- **Chart draw:** Line draws from left, `600ms`, `easeOutCubic`
- **Period switch:** Crossfade, `300ms`
- **Holdings stagger:** Each row fades in, staggered `60ms`
- **Parallax:** Price hero has subtle parallax on scroll (moves slower than content)
- **SliverAppBar collapse:** Ticker text fades in as hero scrolls out

---

## Recommendations (from Engine)

- Realistic shadow layers for depth perception
- Parallax effect (2-3 layers) on hero section
- Smooth chart transitions (300-400ms)
- Touch scrub with haptic: `selectionClick` on each data point
- Holdings sparklines for quick visual scanning
