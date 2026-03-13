# La Paz — Component Spec (T-D2)

> Version: 1.0.0
> Date: 2026-03-05
> UI Library: shadcn/ui (Radix UI + Tailwind CSS)
> Design Tokens: `DESIGN_TOKENS.md` 참조

---

## 1. RumorCard — 이적 루머 카드

### Props

```typescript
interface RumorCardProps {
  id: string;
  player: {
    id: string;
    name: string;
    imageUrl: string | null;
    position: string;
  };
  fromTeam: {
    id: string;
    name: string;
    logoUrl: string | null;
  };
  toTeam: {
    id: string;
    name: string;
    logoUrl: string | null;
  };
  confidenceScore: number;       // 0-100
  status: "rumor" | "confirmed" | "denied";
  sourceCount: number;
  firstReportedAt: string;        // ISO 8601
  lastUpdatedAt: string;          // ISO 8601
}
```

### 레이아웃

```
┌─────────────────────────────────────────────┐
│ [PlayerImg]  Player Name (Position)         │
│              FromTeam → ToTeam              │
│                                             │
│  ConfidenceGauge ███████░░░ 72%   [status]  │
│                                             │
│  📰 3 sources  ·  2h ago                   │
└─────────────────────────────────────────────┘
```

### 상태

| 상태 | 표현 |
|------|------|
| 기본 | `border-border` 테두리, `card` 배경 |
| 호버 | `border-primary/50` 테두리, 미세 `shadow-sm` |
| 확정 이적 | 좌측 `success` 보더 4px |
| 루머 부인 | 좌측 `destructive` 보더 4px, 텍스트 `line-through` 처리 |

### 반응형

| 화면 | 레이아웃 |
|------|---------|
| 모바일 (<640px) | 풀 너비, 세로 스택 |
| sm~md | 2열 그리드 |
| lg+ | 3열 그리드 |

### 접근성

- 전체 카드가 `<a>` 또는 `<Link>`로 감싸짐 (키보드 Tab 접근)
- `aria-label`: `"{player.name} 이적 루머: {fromTeam.name}에서 {toTeam.name}으로, 신뢰도 {confidenceScore}%"`
- 신뢰도 게이지에 `role="meter"`, `aria-valuenow`, `aria-valuemin="0"`, `aria-valuemax="100"`
- 팀 로고 이미지에 `alt="{team.name} 로고"`

---

## 2. MatchCard — 경기 카드

### Props

```typescript
interface MatchCardProps {
  id: string;
  homeTeam: {
    id: string;
    name: string;
    logoUrl: string | null;
    score: number | null;
  };
  awayTeam: {
    id: string;
    name: string;
    logoUrl: string | null;
    score: number | null;
  };
  competition: {
    id: string;
    name: string;
    logoUrl: string | null;
  };
  matchDate: string;              // ISO 8601
  status: "scheduled" | "live" | "finished" | "postponed";
  venue?: string;
  matchday?: number;
}
```

### 레이아웃

```
┌───────────────────────────────────────────┐
│  [LeagueBadge] Premier League  ·  MD 28   │
│                                           │
│  [HomeLogo]  Home Team    2               │
│                           -               │
│  [AwayLogo]  Away Team    1               │
│                                           │
│  🕐 Mar 5, 2026 20:00  ·  [LIVE] 🔴      │
└───────────────────────────────────────────┘
```

### 상태

| 상태 | 표현 |
|------|------|
| 예정 | 시간만 표시, 스코어 "-" |
| 라이브 | `destructive` 색상 "LIVE" 뱃지 + `animate-pulse-live`, 스코어 표시 |
| 종료 | "FT" 라벨, 스코어 `font-bold` |
| 연기 | "POSTPONED" 뱃지 in `warning` |

### 반응형

| 화면 | 레이아웃 |
|------|---------|
| 모바일 | 풀 너비, 세로 스택 |
| md+ | 그리드 (날짜 그룹별) |

### 접근성

- 카드 전체 클릭 가능 (Link)
- `aria-label`: `"{homeTeam.name} vs {awayTeam.name}, {competition.name}, {matchDate}"`
- 라이브 상태: `aria-live="polite"` (스코어 변경 시 스크린 리더 알림)

---

## 3. StandingsTable — 순위표

### Props

```typescript
interface StandingsTableProps {
  competition: {
    id: string;
    name: string;
    season: string;
  };
  rows: StandingsRow[];
}

interface StandingsRow {
  position: number;
  team: {
    id: string;
    name: string;
    logoUrl: string | null;
  };
  played: number;
  won: number;
  drawn: number;
  lost: number;
  goalsFor: number;
  goalsAgainst: number;
  goalDifference: number;
  points: number;
  recentForm: ("W" | "D" | "L")[];  // 최근 5경기
}
```

### 레이아웃

```
┌───────────────────────────────────────────────────────────────────┐
│ #  Team           P   W   D   L   GD   Pts   Form               │
│─────────────────────────────────────────────────────────────────│
│ 1  [Logo] Arsenal  28  20  5   3  +42   65   🟢🟢🔴🟢🟢       │
│ 2  [Logo] Man City 28  19  6   3  +38   63   🟢🟡🟢🟢🟡       │
│ 3  [Logo] Liverpool28  18  5   5  +30   59   🟢🟢🟢🔴🟢       │
│ ...                                                              │
└───────────────────────────────────────────────────────────────────┘
```

### Form 도트 색상

| 결과 | 색상 | 형태 |
|------|------|------|
| W (승) | `success` | 채워진 원 |
| D (무) | `warning` | 채워진 원 |
| L (패) | `destructive` | 채워진 원 |

### 반응형

| 화면 | 표시 컬럼 |
|------|----------|
| 모바일 (<640px) | #, Team, Pts, Form (나머지 숨김) |
| sm | + P, GD |
| md+ | 전체 컬럼 |

### 접근성

- `<table>` 시맨틱 사용, `<th scope="col">` 헤더
- 팀 행 클릭 시 팀 프로필로 이동
- Form 도트: `aria-label="최근 5경기: 승, 승, 패, 승, 승"` (텍스트 변환)
- 정렬 가능 컬럼에 `aria-sort` 속성

---

## 4. PlayerStatCard — 선수 통계 카드

### Props

```typescript
interface PlayerStatCardProps {
  player: {
    id: string;
    name: string;
    imageUrl: string | null;
    position: "GK" | "DF" | "MF" | "FW";
    nationality: string;
    dateOfBirth: string;
    currentTeam: {
      id: string;
      name: string;
      logoUrl: string | null;
    };
  };
  seasonStats: {
    season: string;
    appearances: number;
    goals: number;
    assists: number;
    xG?: number;
    xA?: number;
    minutesPlayed: number;
    rating?: number;              // 0-10
  };
  miniChart?: {
    type: "bar" | "line";
    data: { label: string; value: number }[];
  };
}
```

### 레이아웃

```
┌─────────────────────────────────────────────┐
│ [PlayerImage]                               │
│                                             │
│ Player Name                                 │
│ Position · Team Name                        │
│                                             │
│  ┌────┐ ┌────┐ ┌────┐ ┌────┐              │
│  │ 12 │ │  8 │ │ 9.2│ │ 7.4│              │
│  │Goals│ │Ast │ │ xG │ │Rtg │              │
│  └────┘ └────┘ └────┘ └────┘              │
│                                             │
│  [===== Mini Bar Chart =====]               │
└─────────────────────────────────────────────┘
```

### 상태

| 상태 | 표현 |
|------|------|
| 기본 | `card` 배경, `rounded-lg` |
| 호버 | `border-primary/30` |
| 데이터 없음 | 통계 자리에 "—" 표시 |

### 숫자 스타일

- 모든 통계 숫자: `font-mono font-bold tabular-nums`
- xG, 평점: 소수점 1자리
- 골/어시/출장: 정수

### 반응형

| 화면 | 레이아웃 |
|------|---------|
| 모바일 | 풀 너비 카드 |
| md+ | 프로필 페이지 내 사이드바 고정 |

### 접근성

- 통계 그리드: `role="list"`, 각 항목 `role="listitem"`
- 미니 차트: `aria-label`로 데이터 텍스트 제공
- 선수 이미지: `alt="{player.name}"`

---

## 5. ChatBubble — AI 챗 메시지

### Props

```typescript
interface ChatBubbleProps {
  role: "user" | "assistant";
  content: string;                  // Markdown 지원
  sources?: {
    title: string;
    url: string;
    type: "article" | "stat" | "match";
  }[];
  isStreaming?: boolean;
  timestamp: string;
  locale: "ko" | "en";
}
```

### 레이아웃

```
사용자 메시지:
                              ┌──────────────────────┐
                              │ 손흥민 이번 시즌 골 수? │ user
                              └──────────────────────┘
                                              12:34

AI 메시지:
┌──────────────────────────────────────────────┐
│ ⚠ AI가 생성한 답변입니다                        │ ← 인공지능기본법 고지
│                                              │
│ 손흥민은 2025-26 시즌 현재까지 12골을            │
│ 기록하고 있습니다.                              │
│                                              │
│ 📎 Sources:                                   │
│ ┌────────────────────────┐                    │
│ │ 📊 player_season_stats │                    │
│ │ 📰 Transfermarkt       │                    │
│ └────────────────────────┘                    │
│                                              │
│ AI 응답은 부정확할 수 있습니다.                  │ ← 면책 조항
└──────────────────────────────────────────────┘
12:34
```

### 상태

| 상태 | 표현 |
|------|------|
| 사용자 메시지 | 우측 정렬, `primary` 배경, 흰색 텍스트 |
| AI 메시지 | 좌측 정렬, `card` 배경 |
| 스트리밍 중 | 마지막 줄에 `···` 타이핑 인디케이터 (`animate-typing`) |
| 에러 | `destructive` 보더, "응답 생성에 실패했습니다" 메시지 + 재시도 버튼 |

### 인공지능기본법 라벨

- AI 버블 **상단**에 `"AI가 생성한 답변입니다"` 라벨 (text-xs, muted-foreground)
- AI 버블 **하단**에 `"AI 응답은 부정확할 수 있습니다."` 면책 조항 (text-xs, muted-foreground)
- 라벨은 항상 표시 (숨기기 불가)

### 소스 인용 카드

```typescript
interface SourceCardProps {
  title: string;
  url: string;
  type: "article" | "stat" | "match";
  favicon?: string;
}
```

- 타입별 아이콘: article → 📰, stat → 📊, match → ⚽
- 클릭 시 외부 링크 (새 탭)
- 최대 5개 표시, 초과 시 "더 보기" 토글

### 반응형

| 화면 | 최대 너비 |
|------|----------|
| 모바일 | 85% |
| md+ | 70% |
| lg+ | 60% |

### 접근성

- 메시지 목록: `role="log"`, `aria-live="polite"`
- AI 라벨: `role="status"`
- 소스 링크: `target="_blank" rel="noopener noreferrer"`
- 스트리밍 인디케이터: `aria-label="AI가 답변을 생성 중입니다"`

---

## 6. SimulationForm — 시뮬레이션 입력 폼

### Props

```typescript
interface SimulationFormProps {
  type: "transfer" | "match";
  onSubmit: (params: TransferSimParams | MatchSimParams) => void;
  isLoading: boolean;
}

interface TransferSimParams {
  playerId: string;
  targetTeamId: string;
}

interface MatchSimParams {
  homeTeamId: string;
  awayTeamId: string;
}
```

### 레이아웃 — 이적 시뮬레이션

```
┌─────────────────────────────────────────────┐
│ 이적 시뮬레이션                               │
│                                             │
│ 선수 선택                                    │
│ ┌─────────────────────────────────────┐      │
│ │ 🔍 선수 검색...            [Combobox]│      │
│ └─────────────────────────────────────┘      │
│                                             │
│ 이적 목표 팀                                  │
│ ┌─────────────────────────────────────┐      │
│ │ 🔍 팀 검색...              [Combobox]│      │
│ └─────────────────────────────────────┘      │
│                                             │
│          [시뮬레이션 실행 ▶]                  │
│                                             │
│ ⚠ AI가 생성한 분석 결과입니다                  │
└─────────────────────────────────────────────┘
```

### 상태

| 상태 | 표현 |
|------|------|
| 기본 | 폼 활성, 버튼 `primary` |
| 로딩 | 버튼에 스피너, 폼 입력 비활성화 |
| 에러 | 에러 메시지 토스트, 폼 재활성화 |
| 완료 | 결과 패널로 스크롤/전환 |

### Combobox

- shadcn/ui `<Command>` + `<Popover>` 조합
- 디바운스 검색 (300ms)
- 선수: 이름 + 현재 팀 표시
- 팀: 이름 + 리그 표시
- 최근 검색 3개 기억 (로컬)

### 반응형

| 화면 | 레이아웃 |
|------|---------|
| 모바일 | 풀 너비, 세로 스택 |
| lg+ | 좌측 1/3 고정 (결과 패널과 분할) |

### 접근성

- Combobox: `role="combobox"`, `aria-expanded`, `aria-controls`
- 로딩 시 `aria-busy="true"`
- 필수 필드 `aria-required="true"`
- AI 고지 라벨: 폼 하단에 상시 표시

---

## 7. SimulationResult — 시뮬레이션 결과

### Props

```typescript
interface SimulationResultProps {
  type: "transfer" | "match";
  result: TransferSimResult | MatchSimResult;
  isStreaming: boolean;
}

interface TransferSimResult {
  teamStrengthChange: number;       // -100 ~ +100
  positionFit: number;              // 0-100
  formationImpact: string;          // 텍스트 분석
  salaryFeasibility: "feasible" | "stretch" | "unlikely";
  overallRating: number;            // 0-100
  analysis: string;                 // 상세 분석 텍스트 (Markdown)
}

interface MatchSimResult {
  predictedScore: { home: number; away: number };
  winProbability: { home: number; draw: number; away: number };
  keyFactors: string[];
  headToHeadAnalysis: string;
  analysis: string;
}
```

### 레이아웃 — 이적 시뮬레이션 결과

```
┌─────────────────────────────────────────────┐
│ ⚠ AI가 생성한 분석 결과입니다                  │
│                                             │
│ 종합 점수                                    │
│ ████████████████░░░░  78/100                │
│                                             │
│ ┌──────────┐ ┌──────────┐ ┌──────────┐     │
│ │ 전력 변화  │ │ 포지션    │ │ 연봉      │     │
│ │   +12     │ │ 적합도    │ │ 가능      │     │
│ │           │ │  85%     │ │           │     │
│ └──────────┘ └──────────┘ └──────────┘     │
│                                             │
│ 포메이션 영향                                 │
│ "4-3-3에서 좌측 윙으로 자연스럽게 배치..."      │
│                                             │
│ 상세 분석                                    │
│ [Markdown rendered analysis ...]             │
│                                             │
│ AI 분석은 참고용이며 실제와 다를 수 있습니다.    │
└─────────────────────────────────────────────┘
```

### 숫자 색상 매핑

| 값 | 색상 |
|-----|------|
| 전력 변화 양수 | `success` |
| 전력 변화 음수 | `destructive` |
| 포지션 적합도 61-100 | `success` |
| 포지션 적합도 31-60 | `warning` |
| 포지션 적합도 0-30 | `destructive` |

### 반응형

| 화면 | 레이아웃 |
|------|---------|
| 모바일 | 풀 너비, 세로 스택 |
| lg+ | 우측 2/3 (폼과 분할) |

### 접근성

- 스트리밍 중: `aria-live="polite"` 영역
- 게이지/미터: `role="meter"` + `aria-valuenow`
- AI 고지 라벨: 결과 영역 상단 + 하단

---

## 8. ConfidenceGauge — 신뢰도 게이지

### Props

```typescript
interface ConfidenceGaugeProps {
  value: number;              // 0-100
  size?: "sm" | "md" | "lg";
  showLabel?: boolean;        // default true
  showPercentage?: boolean;   // default true
}
```

### 크기 variant

| Size | 높이 | 너비 | 폰트 |
|------|------|------|------|
| sm | 6px | 60px | text-xs |
| md | 8px | 100px | text-sm |
| lg | 12px | 160px | text-base |

### 색상 로직

```typescript
function getConfidenceColor(value: number) {
  if (value <= 30) return "destructive"; // 빨강
  if (value <= 60) return "warning";     // 앰버
  return "success";                       // 초록
}
```

### 레이아웃

```
md 사이즈:
██████████░░░░░░░░░░ 52%
         warning

lg 사이즈:
████████████████████████░░░░░░░░ 82%  높음
                    success
```

### 접근성

- `role="meter"`
- `aria-valuenow={value}`
- `aria-valuemin="0"`
- `aria-valuemax="100"`
- `aria-label="신뢰도 {value}%"`
- 색상 외에 텍스트 라벨("낮음/보통/높음") 제공 (색맹 대응)

---

## 9. EventTimeline — 경기 이벤트 타임라인

### Props

```typescript
interface EventTimelineProps {
  events: MatchEvent[];
  homeTeamId: string;
  awayTeamId: string;
}

interface MatchEvent {
  id: string;
  type: "goal" | "assist" | "yellow_card" | "red_card" | "substitution" | "penalty" | "own_goal";
  minute: number;
  additionalTime?: number;
  player: {
    id: string;
    name: string;
  };
  relatedPlayer?: {              // 어시스트 제공자, 교체 투입 선수
    id: string;
    name: string;
  };
  teamId: string;
}
```

### 이벤트 아이콘

| 타입 | 아이콘 | 색상 |
|------|--------|------|
| goal | ⚽ | `accent` |
| assist | 👟 | `muted-foreground` |
| yellow_card | 🟨 | `warning` |
| red_card | 🟥 | `destructive` |
| substitution | 🔄 | `info` |
| penalty | ⚽(P) | `accent` |
| own_goal | ⚽(OG) | `destructive` |

### 레이아웃

```
         Home Events    │ Min │    Away Events
─────────────────────────────────────────────────
  ⚽ Player A (Assist B) │ 23' │
                         │ 35' │ 🟨 Player C
  🔄 Player D ↔ Player E │ 60' │
                         │ 78' │ ⚽ Player F
  🟥 Player G            │ 85' │
```

### 반응형

| 화면 | 레이아웃 |
|------|---------|
| 모바일 | 단일 컬럼 리스트 (팀 뱃지로 구분) |
| md+ | 양쪽 분할 타임라인 (위 레이아웃) |

### 접근성

- `<ol>` 시맨틱
- 각 이벤트: `aria-label="{minute}분 {type}: {player.name}"`
- 분 숫자: `font-mono tabular-nums`

---

## 10. TeamBadge — 팀 뱃지

### Props

```typescript
interface TeamBadgeProps {
  team: {
    id: string;
    name: string;
    logoUrl: string | null;
  };
  size?: "xs" | "sm" | "md" | "lg";
  showName?: boolean;           // default true
  linkable?: boolean;           // default true
}
```

### 크기 variant

| Size | 로고 크기 | 폰트 |
|------|----------|------|
| xs | 16px | text-xs |
| sm | 24px | text-sm |
| md | 32px | text-base |
| lg | 48px | text-lg |

### 레이아웃

```
md 사이즈:
[32px Logo] Team Name
```

### 상태

| 상태 | 표현 |
|------|------|
| 기본 | 로고 + 이름 |
| 로고 없음 | 이름 첫 글자 원형 아바타 (secondary 배경) |
| linkable | 호버 시 이름에 underline + `primary` 색상 |

### 접근성

- 로고 `alt="{team.name} 로고"`
- linkable인 경우 `<Link>` 래핑, `aria-label="{team.name} 프로필 보기"`
- 로고 없을 때 fallback 아바타에 `aria-hidden="true"`, 이름 텍스트에 의존

---

## 공통 패턴

### 로딩 상태

모든 데이터 의존 컴포넌트에 Skeleton 로딩 적용:
- shadcn/ui `<Skeleton>` 사용
- 실제 레이아웃과 동일한 형태의 Skeleton
- `animate-pulse` (Tailwind 기본)

### 에러 상태

데이터 로드 실패 시:
- 인라인 에러 메시지 (destructive 텍스트)
- "다시 시도" 버튼
- 전체 페이지 에러는 Next.js `error.tsx` 바운더리

### 빈 상태

데이터가 없을 때:
- 일러스트 또는 아이콘 (muted-foreground)
- 설명 텍스트 ("경기 데이터가 없습니다")
- 가능한 경우 CTA ("다른 날짜 선택하기")

---

*이 컴포넌트 스펙은 FE-Developer가 shadcn/ui 기반으로 구현할 때의 단일 소스이다.*
*모든 Props 인터페이스는 `types/components.ts`에 정의한다.*
