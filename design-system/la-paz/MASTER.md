# La Paz Design System — Master File

> **LOGIC:** When building a specific page, first check `design-system/la-paz/pages/[page-name].md`.
> If that file exists, its rules **override** this Master file.
> If not, strictly follow the rules below.

---

**Project:** La Paz — Football Intelligence Platform
**Generated:** 2026-03-09
**Category:** Sports / AI Intelligence / Fan Platform
**Theme Default:** Dark

---

## Brand DNA

La Paz 로고는 **기하학적 블록 타이포그래피** (각진 컷, 삼각형 요소, 순수 블랙&화이트).
이 DNA를 UI 전체에 반영한다:

- **각진 요소**: 카드 모서리 `border-radius: 2px` (둥근 것 금지 — 최대 4px)
- **대각선/삼각형 모티프**: 섹션 구분선, 악센트 장식에 `clip-path: polygon()` 활용
- **블랙&화이트 기반**: 악센트 색상은 최소한으로, 로고와 충돌 금지
- **볼드한 타이포그래피**: 헤딩은 크고 무겁게, 임팩트 있는 시각

### Logo Usage

| Context | File | Minimum Margin |
|---------|------|---------------|
| Dark background | `Lapaz_logo_white.png` | 로고 높이의 50% |
| Light background | `lapaz_logo_black.png` | 로고 높이의 50% |

**Logo Don'ts:**
- 색상 변형 금지 (블랙/화이트만 사용)
- 배경에 대비 부족 시 사용 금지
- 로고 위에 텍스트 오버레이 금지
- 로고 비율 변경 금지

---

## Color Palette

### Dark Theme (기본)

| Role | Hex | HSL | Tailwind | CSS Variable |
|------|-----|-----|----------|--------------|
| Background | `#0A0A0A` | 0 0% 4% | `bg-[#0A0A0A]` | `--background` |
| Surface | `#141414` | 0 0% 8% | `bg-[#141414]` | `--surface` |
| Surface Elevated | `#1E1E1E` | 0 0% 12% | `bg-[#1E1E1E]` | `--surface-elevated` |
| Border | `#2A2A2A` | 0 0% 16% | `border-[#2A2A2A]` | `--border` |
| Border Hover | `#3A3A3A` | 0 0% 23% | `border-[#3A3A3A]` | `--border-hover` |
| Text Primary | `#F5F5F5` | 0 0% 96% | `text-[#F5F5F5]` | `--text-primary` |
| Text Secondary | `#A0A0A0` | 0 0% 63% | `text-[#A0A0A0]` | `--text-secondary` |
| Text Muted | `#6B6B6B` | 0 0% 42% | `text-[#6B6B6B]` | `--text-muted` |
| Accent | `#00E5A0` | 160 100% 45% | `text-[#00E5A0]` | `--accent` |
| Accent Hover | `#00CC8E` | 160 100% 40% | — | `--accent-hover` |
| Accent Subtle | `#00E5A010` | — | — | `--accent-subtle` |
| Destructive | `#EF4444` | 0 84% 60% | `text-red-500` | `--destructive` |
| Warning | `#F59E0B` | 38 92% 50% | `text-amber-500` | `--warning` |
| Success | `#10B981` | 160 64% 40% | `text-emerald-500` | `--success` |

### Light Theme

| Role | Hex | CSS Variable |
|------|-----|--------------|
| Background | `#FAFAFA` | `--background` |
| Surface | `#FFFFFF` | `--surface` |
| Surface Elevated | `#F5F5F5` | `--surface-elevated` |
| Border | `#E5E5E5` | `--border` |
| Text Primary | `#0A0A0A` | `--text-primary` |
| Text Secondary | `#525252` | `--text-secondary` |
| Accent | `#00B37E` | `--accent` |

### Accent Color Rationale
- `#00E5A0` (민트 그린): 블랙 배경 위 높은 대비, 에너지 + 프리미엄, 로고 B&W와 충돌 없음
- 축구 피치 그린에서 영감을 받되 네온으로 현대화
- 사용은 **최소한**: CTA, 활성 상태, 중요 수치 강조에만

---

## Typography

### Font Stack

| Role | Font | Weight | Fallback |
|------|------|--------|----------|
| Display (Hero) | **Bebas Neue** | 400 | sans-serif |
| Heading | **Outfit** | 500–700 | sans-serif |
| Body | **Work Sans** | 300–500 | sans-serif |
| Mono (Stats) | **JetBrains Mono** | 400–600 | monospace |

```css
@import url('https://fonts.googleapis.com/css2?family=Bebas+Neue&family=Outfit:wght@300;400;500;600;700&family=Work+Sans:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500;600&display=swap');
```

### Tailwind Config
```js
fontFamily: {
  display: ['"Bebas Neue"', 'sans-serif'],
  heading: ['Outfit', 'sans-serif'],
  body: ['"Work Sans"', 'sans-serif'],
  mono: ['"JetBrains Mono"', 'monospace'],
}
```

### Type Scale

| Token | Size | Line Height | Weight | Usage |
|-------|------|-------------|--------|-------|
| `display-xl` | 72px / 4.5rem | 1.0 | 400 | Hero headline (Bebas Neue) |
| `display-lg` | 48px / 3rem | 1.1 | 400 | Section hero (Bebas Neue) |
| `h1` | 32px / 2rem | 1.2 | 700 | Page titles (Outfit) |
| `h2` | 24px / 1.5rem | 1.3 | 600 | Section headers (Outfit) |
| `h3` | 20px / 1.25rem | 1.4 | 600 | Card titles (Outfit) |
| `body-lg` | 18px / 1.125rem | 1.6 | 400 | Lead paragraphs (Work Sans) |
| `body` | 16px / 1rem | 1.6 | 400 | Body text (Work Sans) |
| `body-sm` | 14px / 0.875rem | 1.5 | 400 | Captions, metadata |
| `caption` | 12px / 0.75rem | 1.4 | 500 | Labels, badges |
| `stat` | 28px / 1.75rem | 1.0 | 600 | Stats numbers (JetBrains Mono) |

---

## Spacing

| Token | Value | Tailwind | Usage |
|-------|-------|----------|-------|
| `--space-1` | 4px | `p-1` | Micro gaps |
| `--space-2` | 8px | `p-2` | Icon gaps, inline |
| `--space-3` | 12px | `p-3` | Tight padding |
| `--space-4` | 16px | `p-4` | Standard padding |
| `--space-6` | 24px | `p-6` | Card padding |
| `--space-8` | 32px | `p-8` | Section padding |
| `--space-12` | 48px | `p-12` | Large section gaps |
| `--space-16` | 64px | `p-16` | Hero padding |
| `--space-24` | 96px | `p-24` | Page section margins |

---

## Shadows (Dark Theme)

| Level | Value | Usage |
|-------|-------|-------|
| `--shadow-sm` | `0 1px 2px rgba(0,0,0,0.3)` | Subtle lift |
| `--shadow-md` | `0 4px 12px rgba(0,0,0,0.4)` | Cards |
| `--shadow-lg` | `0 8px 24px rgba(0,0,0,0.5)` | Modals, dropdowns |
| `--shadow-glow` | `0 0 20px rgba(0,229,160,0.15)` | Accent glow effect |

---

## Border & Radius

| Token | Value | Usage |
|-------|-------|-------|
| `--radius-none` | `0px` | Geometric elements, 기본 |
| `--radius-sm` | `2px` | Cards, buttons |
| `--radius-md` | `4px` | 최대 허용 곡률 |
| `--radius-full` | `9999px` | Badges, pills only |

**원칙: 둥근 모서리를 최소화한다.** 로고의 각진 기하학적 언어를 따른다.

---

## Component Specs

### Buttons

```css
/* Primary CTA */
.btn-primary {
  background: var(--accent);
  color: #0A0A0A;
  padding: 12px 28px;
  border-radius: 2px;
  font-family: 'Outfit', sans-serif;
  font-weight: 600;
  font-size: 14px;
  letter-spacing: 0.02em;
  text-transform: uppercase;
  transition: all 200ms ease;
  cursor: pointer;
}
.btn-primary:hover {
  background: var(--accent-hover);
  box-shadow: 0 0 20px rgba(0,229,160,0.2);
}

/* Secondary/Ghost */
.btn-secondary {
  background: transparent;
  color: var(--text-primary);
  border: 1px solid var(--border);
  padding: 12px 28px;
  border-radius: 2px;
  font-weight: 600;
  font-size: 14px;
  text-transform: uppercase;
  transition: all 200ms ease;
  cursor: pointer;
}
.btn-secondary:hover {
  border-color: var(--accent);
  color: var(--accent);
}
```

### Cards

```css
.card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 2px;
  padding: 24px;
  transition: all 200ms ease;
  cursor: pointer;
}
.card:hover {
  border-color: var(--accent);
  box-shadow: 0 0 0 1px var(--accent);
}

/* Stat Card — 숫자 강조 */
.card-stat {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 2px;
  padding: 20px;
  border-left: 3px solid var(--accent);
}
.card-stat .stat-number {
  font-family: 'JetBrains Mono', monospace;
  font-size: 28px;
  font-weight: 600;
  color: var(--text-primary);
}
```

### Inputs

```css
.input {
  background: var(--surface);
  color: var(--text-primary);
  padding: 12px 16px;
  border: 1px solid var(--border);
  border-radius: 2px;
  font-size: 16px;
  font-family: 'Work Sans', sans-serif;
  transition: border-color 200ms ease;
}
.input:focus {
  border-color: var(--accent);
  outline: none;
  box-shadow: 0 0 0 2px rgba(0,229,160,0.1);
}
.input::placeholder {
  color: var(--text-muted);
}
```

### Navigation

```css
.nav {
  background: rgba(10,10,10,0.8);
  backdrop-filter: blur(12px);
  border-bottom: 1px solid var(--border);
  position: sticky;
  top: 0;
  z-index: 50;
  padding: 0 24px;
  height: 64px;
}
.nav-link {
  color: var(--text-secondary);
  font-family: 'Outfit', sans-serif;
  font-weight: 500;
  font-size: 14px;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  transition: color 200ms ease;
  cursor: pointer;
}
.nav-link:hover,
.nav-link.active {
  color: var(--accent);
}
```

### Badges / Tags

```css
.badge {
  display: inline-flex;
  align-items: center;
  padding: 4px 10px;
  border-radius: 2px;
  font-size: 12px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}
.badge-live {
  background: #EF444420;
  color: #EF4444;
  animation: pulse-live 2s ease-in-out infinite;
}
.badge-confidence {
  background: var(--accent-subtle);
  color: var(--accent);
}
```

### Tables (Standings)

```css
.table {
  width: 100%;
  border-collapse: separate;
  border-spacing: 0;
  font-family: 'Work Sans', sans-serif;
}
.table th {
  color: var(--text-muted);
  font-size: 12px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  padding: 12px 16px;
  border-bottom: 1px solid var(--border);
  text-align: left;
}
.table td {
  padding: 12px 16px;
  border-bottom: 1px solid var(--border);
  font-size: 14px;
}
.table tr:hover {
  background: var(--surface-elevated);
}
.table .stat-cell {
  font-family: 'JetBrains Mono', monospace;
  text-align: center;
}
```

---

## Effects & Animations

### Geometric Decorations
```css
/* 대각선 섹션 구분자 */
.section-divider {
  clip-path: polygon(0 0, 100% 0, 100% 80%, 0 100%);
  height: 80px;
  background: var(--surface);
}

/* 삼각형 악센트 (로고 DNA) */
.accent-triangle {
  width: 0;
  height: 0;
  border-left: 12px solid transparent;
  border-right: 12px solid transparent;
  border-bottom: 20px solid var(--accent);
}
```

### Transitions
```css
/* Standard transition (모든 인터랙티브 요소) */
transition: all 200ms ease;

/* Glow on hover */
.glow-hover:hover {
  box-shadow: 0 0 20px rgba(0,229,160,0.15);
}

/* LIVE pulse */
@keyframes pulse-live {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}
```

### Micro-interactions
- 카드 호버: `border-color` 변경 + glow (scale 금지)
- 버튼 호버: 배경색 변경 + glow
- 네비게이션 링크: `color` 변경만
- `prefers-reduced-motion`: 모든 애니메이션 비활성화

---

## Responsive Breakpoints

| Name | Width | Tailwind | Layout |
|------|-------|----------|--------|
| Mobile | < 640px | `sm:` | 1 column, stack |
| Tablet | 640–1023px | `md:` | 2 columns |
| Desktop | 1024–1439px | `lg:` | 3 columns, sidebar |
| Wide | 1440px+ | `xl:` | Max width 1280px, centered |

### Container
```css
.container {
  max-width: 1280px;
  margin: 0 auto;
  padding: 0 24px;
}
```

---

## Tailwind CSS Config (globals.css)

```css
@tailwind base;
@tailwind components;
@tailwind utilities;

@layer base {
  :root {
    --background: 0 0% 98%;
    --foreground: 0 0% 4%;
    --card: 0 0% 100%;
    --card-foreground: 0 0% 4%;
    --popover: 0 0% 100%;
    --popover-foreground: 0 0% 4%;
    --primary: 160 100% 45%;
    --primary-foreground: 0 0% 4%;
    --secondary: 0 0% 96%;
    --secondary-foreground: 0 0% 10%;
    --muted: 0 0% 96%;
    --muted-foreground: 0 0% 42%;
    --accent: 160 100% 45%;
    --accent-foreground: 0 0% 4%;
    --destructive: 0 84% 60%;
    --destructive-foreground: 0 0% 98%;
    --border: 0 0% 90%;
    --input: 0 0% 90%;
    --ring: 160 100% 45%;
    --radius: 2px;
  }

  .dark {
    --background: 0 0% 4%;
    --foreground: 0 0% 96%;
    --card: 0 0% 8%;
    --card-foreground: 0 0% 96%;
    --popover: 0 0% 8%;
    --popover-foreground: 0 0% 96%;
    --primary: 160 100% 45%;
    --primary-foreground: 0 0% 4%;
    --secondary: 0 0% 12%;
    --secondary-foreground: 0 0% 96%;
    --muted: 0 0% 12%;
    --muted-foreground: 0 0% 42%;
    --accent: 160 100% 45%;
    --accent-foreground: 0 0% 4%;
    --destructive: 0 84% 60%;
    --destructive-foreground: 0 0% 98%;
    --border: 0 0% 16%;
    --input: 0 0% 16%;
    --ring: 160 100% 45%;
  }
}
```

### tailwind.config.ts Additions
```typescript
theme: {
  extend: {
    fontFamily: {
      display: ['"Bebas Neue"', 'sans-serif'],
      heading: ['Outfit', 'sans-serif'],
      body: ['"Work Sans"', 'sans-serif'],
      mono: ['"JetBrains Mono"', 'monospace'],
    },
    borderRadius: {
      DEFAULT: '2px',
      sm: '2px',
      md: '4px',
      lg: '4px',
      full: '9999px',
    },
    colors: {
      accent: {
        DEFAULT: '#00E5A0',
        hover: '#00CC8E',
        subtle: 'rgba(0,229,160,0.06)',
      },
    },
    keyframes: {
      'pulse-live': {
        '0%, 100%': { opacity: '1' },
        '50%': { opacity: '0.5' },
      },
    },
    animation: {
      'pulse-live': 'pulse-live 2s ease-in-out infinite',
    },
  },
},
```

---

## Anti-Patterns (Do NOT Use)

- **둥근 카드** (border-radius > 4px) — 로고의 각진 기하학과 상충
- **이모지 아이콘** — SVG only (Lucide React)
- **화려한 그래디언트** — B&W 기반, 악센트 그래디언트만 허용 (`#00E5A0` → `#00B37E`)
- **Layout-shifting hovers** — scale 대신 glow/border 변경
- **과도한 색상** — 악센트 1색(민트) + 시맨틱 3색(red/amber/green)만
- **라이트 테마 다크 텍스트 부족** — 최소 4.5:1 대비
- **Static content** — 모든 데이터는 실시간 또는 ISR
- **cursor:pointer 누락** — 클릭 가능 요소 필수

---

## Icon System

- **Library:** Lucide React (일관된 stroke-width: 1.5)
- **Size:** 기본 20px (`w-5 h-5`), 네비게이션 24px (`w-6 h-6`)
- **Color:** `currentColor` — 부모의 text color 상속
- **aria-hidden:** 장식 아이콘에 `aria-hidden="true"`

---

## Chart & Data Visualization

- **Library:** Recharts (React 네이티브)
- **Real-time:** Streaming Area Chart (D3.js or CanvasJS)
- **Colors:** 악센트(`#00E5A0`), secondary(`#3B82F6`), muted(`#6B6B6B`)
- **Dark theme:** 그리드 `#2A2A2A`, 축 텍스트 `#6B6B6B`
- **Tooltip:** `background: #1E1E1E`, `border: 1px solid #2A2A2A`

---

## Pre-Delivery Checklist

- [ ] 이모지 아이콘 없음 (SVG Lucide React 사용)
- [ ] 모든 아이콘 일관된 세트 (Lucide, stroke-width: 1.5)
- [ ] `cursor-pointer` 모든 클릭 가능 요소
- [ ] 호버 상태 smooth transition (200ms)
- [ ] Dark mode: 기본 테마, 모든 컴포넌트 검증
- [ ] Light mode: 텍스트 대비 4.5:1 이상
- [ ] Focus states 가시적 (keyboard nav)
- [ ] `prefers-reduced-motion` 적용
- [ ] Responsive: 375px, 768px, 1024px, 1440px
- [ ] 고정 nav 뒤 콘텐츠 숨김 없음
- [ ] 모바일 가로 스크롤 없음
- [ ] 로고 올바른 버전 사용 (다크=화이트, 라이트=블랙)
- [ ] `border-radius` 최대 4px (로고 기하학 DNA)
- [ ] 숫자/통계에 JetBrains Mono 사용
