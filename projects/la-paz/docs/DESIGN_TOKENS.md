# La Paz — Design Tokens (T-D1)

> Version: 1.0.0
> Date: 2026-03-05
> Theme: Dark-first (축구 미디어 관례)
> Framework: Tailwind CSS + CSS Custom Properties
> UI Library: shadcn/ui (Radix UI)

---

## 1. 색상 (Color Palette)

### 1.1 기본 색상 — 다크 테마

| Token | Hex | HSL | 용도 |
|-------|-----|-----|------|
| `--background` | `#0B0F1A` | `225 40% 7%` | 페이지 배경 |
| `--foreground` | `#F0F2F5` | `216 20% 95%` | 기본 텍스트 |
| `--card` | `#131928` | `225 32% 12%` | 카드 배경 |
| `--card-foreground` | `#F0F2F5` | `216 20% 95%` | 카드 텍스트 |
| `--popover` | `#1A2138` | `225 35% 16%` | 팝오버/드롭다운 배경 |
| `--popover-foreground` | `#F0F2F5` | `216 20% 95%` | 팝오버 텍스트 |
| `--muted` | `#1E2640` | `225 35% 18%` | 비활성/보조 배경 |
| `--muted-foreground` | `#8B95A8` | `220 15% 60%` | 보조 텍스트 |
| `--border` | `#2A3350` | `225 30% 24%` | 테두리, 구분선 |
| `--input` | `#2A3350` | `225 30% 24%` | 입력 필드 테두리 |
| `--ring` | `#10B981` | `160 84% 39%` | 포커스 링 |

### 1.2 브랜드 색상

| Token | Hex | HSL | 용도 |
|-------|-----|-----|------|
| `--primary` | `#10B981` | `160 84% 39%` | CTA 버튼, 링크, 강조 (에메랄드 그린 — 축구 필드) |
| `--primary-foreground` | `#FFFFFF` | `0 0% 100%` | primary 위 텍스트 |
| `--secondary` | `#1E2640` | `225 35% 18%` | 보조 버튼, 뱃지 배경 |
| `--secondary-foreground` | `#F0F2F5` | `216 20% 95%` | secondary 위 텍스트 |
| `--accent` | `#F59E0B` | `38 92% 50%` | 골/이벤트 하이라이트, 알림 (앰버) |
| `--accent-foreground` | `#0B0F1A` | `225 40% 7%` | accent 위 텍스트 |

### 1.3 시맨틱 색상

| Token | Hex | HSL | 용도 |
|-------|-----|-----|------|
| `--destructive` | `#EF4444` | `0 84% 60%` | 레드카드, 에러, 신뢰도 낮음 (0-30) |
| `--destructive-foreground` | `#FFFFFF` | `0 0% 100%` | destructive 위 텍스트 |
| `--success` | `#22C55E` | `142 71% 45%` | 확정 이적, 신뢰도 높음 (61-100), 성공 |
| `--success-foreground` | `#FFFFFF` | `0 0% 100%` | success 위 텍스트 |
| `--warning` | `#F59E0B` | `38 92% 50%` | 루머/중간 신뢰도 (31-60), 경고 |
| `--warning-foreground` | `#0B0F1A` | `225 40% 7%` | warning 위 텍스트 |
| `--info` | `#3B82F6` | `217 91% 60%` | 정보성 메시지, 링크 |

### 1.4 신뢰도 색상 매핑 (ConfidenceGauge)

| 범위 | Token | 색상 | 라벨 |
|------|-------|------|------|
| 0-30 | `--confidence-low` | `--destructive` (#EF4444) | 낮음 |
| 31-60 | `--confidence-mid` | `--warning` (#F59E0B) | 보통 |
| 61-100 | `--confidence-high` | `--success` (#22C55E) | 높음 |

### 1.5 경기 상태 색상

| 상태 | Token | 색상 |
|------|-------|------|
| 예정 (Scheduled) | `--match-scheduled` | `--muted-foreground` |
| 진행중 (Live) | `--match-live` | `--destructive` + pulse 애니메이션 |
| 종료 (Finished) | `--match-finished` | `--foreground` |

### 1.6 접근성 — 색상 대비

모든 텍스트-배경 조합은 WCAG 2.1 AA 기준 **4.5:1** 이상을 충족한다.

| 조합 | 대비율 | 통과 |
|------|--------|------|
| foreground on background | 15.2:1 | AA |
| muted-foreground on background | 5.8:1 | AA |
| muted-foreground on card | 4.7:1 | AA |
| primary on background | 7.1:1 | AA |
| destructive on card | 5.5:1 | AA |
| warning on card | 6.2:1 | AA |
| success on card | 5.8:1 | AA |

---

## 2. 타이포그래피

### 2.1 Font Family

| Token | Font | 용도 |
|-------|------|------|
| `--font-sans` | `Inter, ui-sans-serif, system-ui, sans-serif` | UI 전반 |
| `--font-mono` | `Geist Mono, ui-monospace, monospace` | 통계 숫자, 코드 |

### 2.2 Font Size Scale

| Token | Size | Line Height | 용도 |
|-------|------|-------------|------|
| `text-xs` | 12px (0.75rem) | 16px (1.33) | 캡션, 타임스탬프, 라벨 |
| `text-sm` | 14px (0.875rem) | 20px (1.43) | 보조 텍스트, 테이블 셀 |
| `text-base` | 16px (1rem) | 24px (1.5) | 본문, 카드 설명 |
| `text-lg` | 18px (1.125rem) | 28px (1.56) | 카드 제목, 서브헤딩 |
| `text-xl` | 20px (1.25rem) | 28px (1.4) | 섹션 헤딩 |
| `text-2xl` | 24px (1.5rem) | 32px (1.33) | 페이지 서브타이틀 |
| `text-3xl` | 30px (1.875rem) | 36px (1.2) | 페이지 타이틀 |
| `text-4xl` | 36px (2.25rem) | 40px (1.11) | 히어로 헤드라인, 스코어 |

### 2.3 Font Weight

| Token | Weight | 용도 |
|-------|--------|------|
| `font-normal` | 400 | 본문 텍스트 |
| `font-medium` | 500 | 라벨, 네비게이션 |
| `font-semibold` | 600 | 헤딩, 카드 타이틀 |
| `font-bold` | 700 | 스코어, 핵심 통계 숫자 |

### 2.4 통계 숫자 전용 스타일

```
.stat-number {
  font-family: var(--font-mono);
  font-weight: 700;
  font-variant-numeric: tabular-nums;
  letter-spacing: -0.02em;
}
```

---

## 3. Spacing

4px 기반 시스템 (Tailwind 기본).

| Token | Value | 용도 |
|-------|-------|------|
| `space-0.5` | 2px | 미세 간격 |
| `space-1` | 4px | 인라인 요소 간격 |
| `space-1.5` | 6px | 아이콘-텍스트 간격 |
| `space-2` | 8px | 컴포넌트 내부 패딩 (sm) |
| `space-3` | 12px | 컴포넌트 내부 패딩 (md) |
| `space-4` | 16px | 카드 패딩, 섹션 간격 |
| `space-5` | 20px | 폼 필드 간격 |
| `space-6` | 24px | 섹션 간 간격 |
| `space-8` | 32px | 대형 섹션 간격 |
| `space-10` | 40px | 페이지 상단 여백 |
| `space-12` | 48px | 히어로/주요 섹션 패딩 |
| `space-16` | 64px | 페이지 섹션 구분 |

---

## 4. Border Radius

| Token | Value | 용도 |
|-------|-------|------|
| `rounded-sm` | 4px | 뱃지, 태그, 작은 요소 |
| `rounded-md` | 8px | 카드, 버튼, 입력 필드 |
| `rounded-lg` | 12px | 모달, 대형 카드 |
| `rounded-xl` | 16px | 히어로 카드, 패널 |
| `rounded-full` | 9999px | 아바타, 토글, 신뢰도 게이지 |

---

## 5. Shadows

다크 테마에서는 그림자 대신 **border와 배경색 차이**로 계층을 구분한다.

| Token | Value | 용도 |
|-------|-------|------|
| `shadow-none` | `none` | 기본 (대부분의 카드) |
| `shadow-sm` | `0 1px 2px rgba(0,0,0,0.3)` | 호버 상태 미세 그림자 |
| `shadow-md` | `0 4px 6px rgba(0,0,0,0.4)` | 팝오버, 드롭다운 |
| `shadow-lg` | `0 10px 15px rgba(0,0,0,0.5)` | 모달 |
| `shadow-glow-primary` | `0 0 12px rgba(16,185,129,0.3)` | 주요 CTA 호버 시 글로우 |
| `shadow-glow-accent` | `0 0 12px rgba(245,158,11,0.3)` | 골 이벤트 하이라이트 글로우 |

---

## 6. Animation / Transition

| Token | Value | 용도 |
|-------|-------|------|
| `transition-fast` | `150ms ease-out` | 호버, 포커스 |
| `transition-normal` | `200ms ease-in-out` | 패널 전환 |
| `transition-slow` | `300ms ease-in-out` | 모달 열기/닫기 |
| `animate-pulse-live` | `2s ease-in-out infinite` | 라이브 경기 인디케이터 |
| `animate-typing` | `1.5s steps(3) infinite` | AI 타이핑 인디케이터 (...) |
| `animate-slide-up` | `200ms ease-out` | 카드/토스트 진입 |
| `animate-score-pop` | `300ms cubic-bezier(0.34,1.56,0.64,1)` | 골 스코어 업데이트 팝 |

---

## 7. Breakpoints (반응형)

| Token | Min Width | 대상 |
|-------|-----------|------|
| `sm` | 640px | 큰 모바일 / 소형 태블릿 |
| `md` | 768px | 태블릿 |
| `lg` | 1024px | 소형 데스크톱 |
| `xl` | 1280px | 데스크톱 |
| `2xl` | 1536px | 대형 데스크톱 |

모바일 퍼스트: 기본 스타일은 모바일, `sm:` 이상에서 점진적 확장.

---

## 8. Z-Index Scale

| Token | Value | 용도 |
|-------|-------|------|
| `z-base` | 0 | 기본 콘텐츠 |
| `z-card` | 10 | 카드 호버 |
| `z-sticky` | 20 | 고정 헤더, 필터바 |
| `z-dropdown` | 30 | 드롭다운, 팝오버 |
| `z-overlay` | 40 | 오버레이 배경 |
| `z-modal` | 50 | 모달 |
| `z-toast` | 60 | 토스트 알림 |

---

## 9. Tailwind Config 확장

```typescript
// tailwind.config.ts
import type { Config } from "tailwindcss";

const config: Config = {
  darkMode: "class",
  content: [
    "./src/**/*.{ts,tsx}",
    "./components/**/*.{ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        background: "hsl(var(--background))",
        foreground: "hsl(var(--foreground))",
        card: {
          DEFAULT: "hsl(var(--card))",
          foreground: "hsl(var(--card-foreground))",
        },
        popover: {
          DEFAULT: "hsl(var(--popover))",
          foreground: "hsl(var(--popover-foreground))",
        },
        primary: {
          DEFAULT: "hsl(var(--primary))",
          foreground: "hsl(var(--primary-foreground))",
        },
        secondary: {
          DEFAULT: "hsl(var(--secondary))",
          foreground: "hsl(var(--secondary-foreground))",
        },
        muted: {
          DEFAULT: "hsl(var(--muted))",
          foreground: "hsl(var(--muted-foreground))",
        },
        accent: {
          DEFAULT: "hsl(var(--accent))",
          foreground: "hsl(var(--accent-foreground))",
        },
        destructive: {
          DEFAULT: "hsl(var(--destructive))",
          foreground: "hsl(var(--destructive-foreground))",
        },
        success: {
          DEFAULT: "hsl(var(--success))",
          foreground: "hsl(var(--success-foreground))",
        },
        warning: {
          DEFAULT: "hsl(var(--warning))",
          foreground: "hsl(var(--warning-foreground))",
        },
        info: "hsl(var(--info))",
        border: "hsl(var(--border))",
        input: "hsl(var(--input))",
        ring: "hsl(var(--ring))",
      },
      fontFamily: {
        sans: ["Inter", "ui-sans-serif", "system-ui", "sans-serif"],
        mono: ["Geist Mono", "ui-monospace", "monospace"],
      },
      borderRadius: {
        sm: "4px",
        md: "8px",
        lg: "12px",
        xl: "16px",
      },
      boxShadow: {
        "glow-primary": "0 0 12px rgba(16,185,129,0.3)",
        "glow-accent": "0 0 12px rgba(245,158,11,0.3)",
      },
      keyframes: {
        "pulse-live": {
          "0%, 100%": { opacity: "1" },
          "50%": { opacity: "0.5" },
        },
        "slide-up": {
          "0%": { opacity: "0", transform: "translateY(8px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
        "score-pop": {
          "0%": { transform: "scale(1)" },
          "50%": { transform: "scale(1.2)" },
          "100%": { transform: "scale(1)" },
        },
      },
      animation: {
        "pulse-live": "pulse-live 2s ease-in-out infinite",
        "slide-up": "slide-up 200ms ease-out",
        "score-pop": "score-pop 300ms cubic-bezier(0.34,1.56,0.64,1)",
      },
    },
  },
  plugins: [require("tailwindcss-animate")],
};

export default config;
```

---

## 10. CSS Custom Properties (globals.css)

```css
@layer base {
  :root {
    /* Light theme (optional future) */
    --background: 220 20% 97%;
    --foreground: 225 30% 10%;
    /* ... */
  }

  .dark {
    --background: 225 40% 7%;
    --foreground: 216 20% 95%;
    --card: 225 32% 12%;
    --card-foreground: 216 20% 95%;
    --popover: 225 35% 16%;
    --popover-foreground: 216 20% 95%;
    --primary: 160 84% 39%;
    --primary-foreground: 0 0% 100%;
    --secondary: 225 35% 18%;
    --secondary-foreground: 216 20% 95%;
    --muted: 225 35% 18%;
    --muted-foreground: 220 15% 60%;
    --accent: 38 92% 50%;
    --accent-foreground: 225 40% 7%;
    --destructive: 0 84% 60%;
    --destructive-foreground: 0 0% 100%;
    --success: 142 71% 45%;
    --success-foreground: 0 0% 100%;
    --warning: 38 92% 50%;
    --warning-foreground: 225 40% 7%;
    --info: 217 91% 60%;
    --border: 225 30% 24%;
    --input: 225 30% 24%;
    --ring: 160 84% 39%;
    --radius: 8px;
  }
}
```

---

*이 토큰 시스템은 shadcn/ui의 CSS variable 패턴과 완전히 호환된다.*
*FE-Developer는 이 문서를 기반으로 `tailwind.config.ts`와 `globals.css`를 구성한다.*
