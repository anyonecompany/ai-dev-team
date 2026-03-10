# La Paz -- FE Developer Handoff

> **Designer:** Designer Agent (Sonnet 4.5)
> **Date:** 2026-03-09
> **Design System:** `design-system/la-paz/MASTER.md`

---

## Design System Files

| File | Description |
|------|-------------|
| `design-system/la-paz/MASTER.md` | Global design system (Source of Truth) |
| `design-system/la-paz/pages/transfers.md` | Transfers page overrides |
| `design-system/la-paz/pages/matches.md` | Matches page overrides |
| `design-system/la-paz/pages/chat.md` | Chat page overrides |
| `design-system/la-paz/pages/simulate.md` | Simulation page overrides |
| `design-system/la-paz/pages/standings.md` | Standings page overrides |

**Usage rule:** When building a page, check `pages/[page].md` first. If it exists, its rules override MASTER.md.

---

## Existing Design Documents (Reference)

These were the source documents used to create the design system:

| Document | Path |
|----------|------|
| Design Tokens | `projects/la-paz/docs/DESIGN_TOKENS.md` |
| Component Spec | `projects/la-paz/docs/COMPONENT_SPEC.md` |
| Wireframes | `projects/la-paz/docs/WIREFRAMES.md` |

---

## Current Component Analysis & Improvement Points

### 1. RumorCard (`components/transfers/RumorCard.tsx`)

**Current status:** Well-implemented, follows design tokens.

**Improvements needed:**
- [ ] Replace emoji `📰` for source count with Lucide `Newspaper` icon
- [ ] Add `cursor-pointer` class to the Link wrapper
- [ ] Consider adding team logo images (currently text-only)

### 2. ConfidenceGauge (`components/transfers/ConfidenceGauge.tsx`)

**Current status:** Well-implemented, proper `role="meter"` and aria attributes.

**Improvements needed:**
- [ ] Add width animation on mount (currently instant render)
- [ ] Ensure `.stat-number` class is defined in globals.css

### 3. MatchCard (`components/matches/MatchCard.tsx`)

**Current status:** Good implementation with status variants.

**Improvements needed:**
- [ ] Replace emoji `🔴` in LIVE badge with Lucide `Circle` SVG icon
- [ ] Add `cursor-pointer` to the Link wrapper
- [ ] Add team logo images next to team names
- [ ] Add `aria-live="polite"` for live match score updates

### 4. ChatBubble (`components/chat/ChatBubble.tsx`)

**Current status:** Good AI disclaimer implementation, proper structure.

**Improvements needed:**
- [ ] Replace emoji icons in source cards (`📎`, `⚽`, `📊`, `📰`) with Lucide SVG icons (Paperclip, Activity, BarChart2, Newspaper)
- [ ] Use `animate-typing` keyframe instead of `animate-pulse` for streaming dots
- [ ] Add `role="log"` and `aria-live="polite"` on the parent message container
- [ ] Implement Markdown rendering for AI responses (currently plain text)

### 5. Header (`components/shared/Header.tsx`)

**Current status:** Well-structured with Lucide icons, proper sticky header.

**Improvements needed:**
- [ ] Replace emoji `⚽` in logo with SVG logo or Lucide icon
- [ ] Add `cursor-pointer` to icon buttons
- [ ] Consider adding search functionality to the Search icon button

### 6. StandingsTable (`components/standings/StandingsTable.tsx`)

**Current status:** Excellent implementation, proper semantic table, responsive columns.

**Improvements needed:**
- [ ] Add team logo images before team names
- [ ] Add zone separators for CL/EL/relegation zones
- [ ] Add `aria-sort` on sortable column headers
- [ ] Consider sticky table header for long tables
- [ ] Add relegation zone row tinting (`bg-destructive/5`)

### 7. TransferSimForm (`components/simulate/TransferSimForm.tsx`)

**Current status:** Basic implementation, needs significant upgrade.

**Improvements needed:**
- [ ] Replace plain `<Input>` with shadcn `<Command>` Combobox for player/team search
- [ ] Replace emoji `🔍` in placeholder with Lucide `Search` icon
- [ ] Add loading spinner to button (currently text-only "Analyzing...")
- [ ] Add `htmlFor` attribute to label elements
- [ ] Add Lucide `Play` icon to submit button

### 8. TransferSimResult (`components/simulate/TransferSimResult.tsx`)

**Current status:** Good structure with metric cards.

**Improvements needed:**
- [ ] Add confidence color mapping to overall rating bar (not just `bg-primary`)
- [ ] Add position fit color mapping (0-30: destructive, 31-60: warning, 61-100: success)
- [ ] Add Markdown rendering for analysis text
- [ ] Add `animate-slide-up` entry animation
- [ ] Add width animation for overall rating bar

### 9. EventTimeline (`components/matches/EventTimeline.tsx`)

**Status:** Not analyzed in detail.

**Improvements needed:**
- [ ] Replace emojis with Lucide SVG icons for event types
- [ ] Implement desktop split layout (home left, away right)
- [ ] Add `aria-label` for each event

### 10. MobileNav (`components/shared/MobileNav.tsx`)

**Status:** Not analyzed in detail.

**Improvements needed:**
- [ ] Ensure 5 nav items: Home, Matches, Transfers, Chat, Simulate
- [ ] Active state: `text-primary`
- [ ] Replace any emojis with Lucide icons
- [ ] Minimum touch target 44x44px

---

## Global Improvements (All Components)

### Priority 1: Icon Migration (HIGH)

Replace ALL emoji usage in UI chrome with Lucide SVG icons:

| Current Emoji | Replace With | Lucide Icon |
|---------------|-------------|-------------|
| `⚽` | Football icon | `Circle` or custom SVG |
| `📰` | News icon | `Newspaper` |
| `📊` | Chart icon | `BarChart2` |
| `📎` | Attachment icon | `Paperclip` |
| `🔍` | Search icon | `Search` |
| `🔴` | Live dot | `Circle` (filled, destructive color) |
| `🏠` | Home nav | `Home` |
| `💬` | Chat nav | `MessageCircle` |
| `🔮` | Simulate nav | `Sparkles` or `Wand2` |

### Priority 2: Accessibility Fixes (HIGH)

- [ ] Add `cursor-pointer` to ALL clickable elements (Link, Button)
- [ ] Ensure all `<label>` elements have `htmlFor`
- [ ] Add `aria-label` to icon-only buttons
- [ ] Add `prefers-reduced-motion` media query in globals.css
- [ ] Verify all color contrast ratios meet WCAG AA (4.5:1)

### Priority 3: Animation Enhancements (MEDIUM)

- [ ] Add `.stat-number` class in globals.css:
  ```css
  .stat-number {
    font-family: var(--font-mono);
    font-weight: 700;
    font-variant-numeric: tabular-nums;
    letter-spacing: -0.02em;
  }
  ```
- [ ] Add `animate-typing` keyframe for chat streaming
- [ ] Add width transition for gauge/progress bars
- [ ] Add `animate-slide-up` for card entry animations

### Priority 4: Markdown Rendering (MEDIUM)

- [ ] Install and configure `react-markdown` or `@next/mdx` for AI response rendering
- [ ] Style Markdown output to match design tokens (headings, lists, code blocks, links)

---

## tailwind.config.ts Modifications

The current `tailwind.config.ts` is well-configured. Recommended additions:

```typescript
// Add to keyframes:
"typing": {
  "0%": { opacity: "0" },
  "50%": { opacity: "1" },
  "100%": { opacity: "0" },
},

// Add to animation:
"typing": "typing 1.5s steps(3) infinite",

// Add to content paths (verify these are included):
"./app/**/*.{ts,tsx}",  // already present
"./components/**/*.{ts,tsx}",  // already present
"./lib/**/*.{ts,tsx}",  // already present
```

No other tailwind.config.ts changes are needed -- the existing config already matches DESIGN_TOKENS.md.

---

## globals.css Additions

```css
/* Add to globals.css */

/* Stat number utility class */
.stat-number {
  font-family: var(--font-mono);
  font-weight: 700;
  font-variant-numeric: tabular-nums;
  letter-spacing: -0.02em;
}

/* Reduced motion accessibility */
@media (prefers-reduced-motion: reduce) {
  *,
  *::before,
  *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
    scroll-behavior: auto !important;
  }
}
```

---

## Implementation Priority

| Priority | Task | Impact |
|----------|------|--------|
| P0 | Emoji-to-SVG icon migration | Visual professionalism |
| P0 | AI disclaimer on all AI content | Legal compliance |
| P1 | Accessibility fixes (cursor, aria, labels) | Usability |
| P1 | Combobox upgrade for simulation forms | UX quality |
| P2 | Animation enhancements (gauge, slide-up) | Polish |
| P2 | Markdown rendering for AI responses | Content quality |
| P2 | Team/player logo images | Visual richness |
| P3 | Zone separators in standings | Detail polish |
| P3 | Sticky table headers | Scrolling UX |

---

## Tech Stack Confirmation

| Layer | Technology | Status |
|-------|-----------|--------|
| Framework | Next.js 15 (App Router) | Confirmed |
| Styling | Tailwind CSS + CSS Variables | Confirmed |
| UI Library | shadcn/ui (Radix UI) | Confirmed |
| Icons | Lucide React (stroke-width: 1.5) | Needs full migration |
| Fonts | **Bebas Neue** (display) + **Outfit** (heading) + **Work Sans** (body) + **JetBrains Mono** (stats) | **UPDATE NEEDED** |
| Dark Mode | `class` strategy (next-themes), **dark default** | **UPDATE NEEDED** |
| Charts | Recharts (recommended) | To be added |
| Animation | tailwindcss-animate plugin | Configured |
| Border Radius | **2px default, max 4px** (geometric DNA) | **UPDATE NEEDED** |
| Accent Color | **#00E5A0** (mint green) | **UPDATE NEEDED** |

---

## Pre-Delivery Checklist (for FE-Developer)

Before marking any page as complete:

- [ ] No emojis used as functional UI icons
- [ ] All icons from Lucide at consistent sizes
- [ ] `cursor-pointer` on all clickable elements
- [ ] Hover states with 150-300ms transitions
- [ ] Dark theme renders correctly (primary mode)
- [ ] Focus states visible (`ring-2 ring-ring`)
- [ ] `prefers-reduced-motion` respected
- [ ] Responsive: 375px, 768px, 1024px, 1440px
- [ ] No content hidden behind sticky header
- [ ] No horizontal scroll on mobile
- [ ] AI disclaimer labels on all AI-generated content
- [ ] Statistical numbers use `stat-number` class
- [ ] All images have `alt` text
- [ ] Form inputs have labeled `<label>` elements
- [ ] Touch targets minimum 44x44px

---

*This handoff document is the FE-Developer's implementation guide.*
*All design decisions reference MASTER.md as the source of truth.*
*Questions about design intent should reference the original docs in `projects/la-paz/docs/`.*
