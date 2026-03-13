# La Paz — Fan Intelligence Platform Architecture

> Version: 1.0.0
> Date: 2026-02-20
> Status: Proposal
> Scope: Re-architecture from RAG wrapper to fan-intelligence data platform

---

## Executive Summary

La Paz is a football Q&A service. Its current value proposition is answering questions. This document redefines it as a **fan intelligence platform** where the primary asset is not the answers, but the **structured understanding of what fans ask, when they ask it, and why**.

Every query becomes a data point. Every session becomes a demand signal. The B2B product sells aggregated fan demand intelligence — not football data (which is commodity), but **what fans want to know about football** (which is proprietary).

---

## 1. Current State Audit

### What Is Tracked Today

| Call Site | Event Type | Payload | What's Missing |
|-----------|-----------|---------|----------------|
| `POST /chat` | `chat` | `{query (200 chars), model, source_count}` | Intent, entities resolved, topic, satisfaction, response quality |
| `POST /chat/stream` | `chat` | Same + `{stream: true}` | Same |
| `GET /teams/{id}` | `page_view` | `{entity_name}` | Referral source (from chat? from search? direct?) |
| `GET /players/{id}` | `page_view` | `{entity_name}` | Same |
| `GET /search` | `search` | `{query (200 chars), results count}` | Entities, intent, clicked results |
| `POST /predictions` | `prediction` | `{home, away}` | No tracking of view-to-submit funnel |

### What Is Not Tracked At All

- **Query intent** — why the user asked (stats lookup, comparison, opinion, news, prediction)
- **Entity resolution** — which players/teams were identified and whether they matched
- **Response satisfaction** — did the user follow up, rephrase, or abandon?
- **Session trajectory** — did chat lead to page_view? Did search lead to chat?
- **Temporal context** — was this query about a live match, a historical event, or a transfer window?
- **Language/locale signal** — Korean query about La Liga vs Korean query about K리그
- **Conversion events** — anonymous→registered, free→returning, passive→active

### Structural Problems

1. **`fan_events.payload` is unstructured jsonb.** No schema enforcement means every event is a snowflake. Aggregation requires per-event-type JSON parsing.
2. **`generate_trend_snapshot` RPC only counts.** It counts entity mentions but doesn't classify demand type. "10 mentions of Son Heung-min" tells you nothing; "7 stat queries + 2 injury queries + 1 transfer rumor query about Son" tells you everything.
3. **user_id stored in cleartext.** `fan_events` links directly to `users.id`. The B2B endpoint exposes `trend_snapshots` publicly. If the aggregation ever leaks per-user data into snapshots, it's a privacy breach.
4. **No intent signal → B2B products are noise.** `entity_buzz` counts mentions. But a B2B client (media company, betting platform, sponsor) doesn't want mention counts — they want demand signals: "fans are asking about X's injury status 3x more than last week" or "transfer-related queries for Team Y spiked 400% after the transfer window opened."

---

## 2. Revised Architecture

### 2.1 Design Principle

```
Every query is classified, anonymized, and stored as a structured demand signal
before it enters the RAG pipeline. The RAG answer is a B2C delivery mechanism.
The classified demand signal is the B2B product.
```

### 2.2 New Request Flow

```
User Query
    │
    ▼
┌─────────────────────────────────┐
│  LAYER 1: Structured Logging    │  ← Capture raw query + metadata
│  (query_log table)              │
└──────────────┬──────────────────┘
               │
               ▼
┌─────────────────────────────────┐
│  LAYER 2: Intent Classification │  ← LLM-based classification (no custom ML)
│  (LLM structured output)       │     Gemini/DeepSeek → JSON schema
└──────────────┬──────────────────┘
               │
               ▼
┌─────────────────────────────────┐
│  LAYER 3: Demand Signal Store   │  ← Anonymized, classified, indexed
│  (demand_signals table)         │     entity + intent + temporal context
└──────────────┬──────────────────┘
               │
               ├──────────────────────────────┐
               ▼                              ▼
┌──────────────────────────┐    ┌──────────────────────────┐
│  B2C: RAG Pipeline       │    │  B2B: Fan Demand API     │
│  (existing Agent 5)      │    │  (new aggregation layer) │
│  Answer the question     │    │  Sell the insight         │
└──────────────────────────┘    └──────────────────────────┘
```

---

## 3. Layer 1: Structured Query Logging

### Problem

`track_fan_event` dumps a partial JSON blob into `fan_events.payload`. There's no schema, no required fields, and no separation between query data and behavioral data.

### Solution: `query_logs` Table

```sql
create table if not exists query_logs (
  id              uuid primary key default uuid_generate_v4(),
  -- Identity (anonymized)
  anon_id         text not null,            -- SHA-256(user_id + daily_salt), NOT user_id
  session_hash    text,                     -- SHA-256(session_id + daily_salt)
  -- Raw query
  query_text      text not null,
  query_lang      text default 'ko',        -- detected language
  channel         text not null default 'chat',  -- chat | search | stream
  -- Resolution metadata (filled by intent classifier)
  entities_json   jsonb default '[]',       -- [{name, type, db_id, confidence}]
  intent          text,                     -- stat_lookup | comparison | news | opinion | prediction | transfer | injury | schedule | how_to
  sub_intent      text,                     -- player_stat | team_stat | h2h | form | lineup | ...
  temporal_frame  text,                     -- live | today | this_week | this_season | historical | transfer_window
  -- Response metadata
  source_count    int default 0,
  rag_hit         boolean default false,    -- did vector search return useful docs?
  model_used      text,
  latency_ms      real,
  -- Session context
  is_followup     boolean default false,    -- rephrased or continuation of prior query
  query_position  int default 1,            -- nth query in session
  -- Timestamps
  created_at      timestamptz default now()
);

create index idx_ql_anon on query_logs(anon_id, created_at);
create index idx_ql_intent on query_logs(intent, created_at);
create index idx_ql_entity on query_logs using gin(entities_json);
create index idx_ql_temporal on query_logs(temporal_frame, created_at);
```

### What Changes in Agent 5

The existing `track_fan_event("chat", ...)` call is replaced. After intent classification (Layer 2), a single structured row is inserted into `query_logs`. The old `fan_events` table remains for non-query behavioral signals (page_view, prediction, share).

### Schema Guarantees

Every query log row has:
- **Anonymized identity** — cannot be reversed to user without the daily salt (stored server-side, rotated every 24h, never exposed to B2B)
- **Classified intent** — one of 9 intent categories, always populated
- **Resolved entities** — JSON array with matched DB IDs and confidence scores
- **Temporal context** — when the query is about, not when it was sent

---

## 4. Layer 2: Intent Classification

### Problem

The current pipeline treats all queries identically: embed → search → generate. A query about "손흥민 부상 상태" (Son's injury status) hits the same code path as "프리미어리그 순위" (PL standings). There's no routing, no demand signal extraction, no structured understanding.

### Solution: LLM-Based Classification Before RAG

Use the existing LLM (Gemini 2.0 Flash) to classify intent via structured output. No custom ML. The LLM is already called for generation — this adds a lightweight classification call before retrieval.

### Intent Taxonomy

```
INTENT (9 categories)
├── stat_lookup        "손흥민 이번 시즌 골 수" → player stats
├── comparison         "메시 vs 호날두 통산 기록" → entity comparison
├── news               "오늘 이적 뉴스" → current events
├── opinion            "최고의 미드필더는?" → subjective / ranking
├── prediction         "다음 엘클라시코 누가 이길까?" → future outcome
├── transfer           "음바페 이적 루머" → transfer market
├── injury             "살라 부상 언제 복귀?" → injury/fitness
├── schedule           "맨유 다음 경기" → fixture lookup
└── explainer          "오프사이드 규칙" → how football works

SUB_INTENT (context-specific)
├── player_stat | team_stat | h2h | form_guide | lineup
├── top_scorers | standings | xg_analysis | season_review
└── live_score | upcoming | result

TEMPORAL_FRAME
├── live               query references an ongoing match
├── today / this_week  near-term
├── this_season        current season context
├── historical         past seasons
└── transfer_window    aligned with transfer periods
```

### Classification Prompt (Structured Output)

```python
CLASSIFY_PROMPT = """Classify this football query. Return JSON only.

Query: "{query}"
Detected entities: {entities}

Return:
{{
  "intent": "stat_lookup|comparison|news|opinion|prediction|transfer|injury|schedule|explainer",
  "sub_intent": "<specific sub-category>",
  "temporal_frame": "live|today|this_week|this_season|historical|transfer_window",
  "entities": [
    {{"name": "<resolved name>", "type": "player|team|competition|manager", "confidence": 0.0-1.0}}
  ],
  "is_followup": false
}}"""
```

### Implementation: Zero Custom Training

```python
def classify_intent(query: str, entities: list[str]) -> dict:
    """Classify user intent using Gemini structured output.

    Uses the same LLM already loaded for RAG generation.
    Average latency: 100-200ms (Gemini Flash).
    Cost: ~0.001 USD per classification.
    """
    from openai import OpenAI
    client = OpenAI(
        api_key=GOOGLE_API_KEY,
        base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
    )
    resp = client.chat.completions.create(
        model="gemini-2.0-flash",
        messages=[
            {"role": "system", "content": "You are a football query classifier. Return valid JSON only."},
            {"role": "user", "content": CLASSIFY_PROMPT.format(query=query, entities=entities)},
        ],
        max_tokens=256,
        temperature=0.0,
        response_format={"type": "json_object"},
    )
    return json.loads(resp.choices[0].message.content)
```

### Fallback: Rule-Based Classification

If the LLM call fails (rate limit, timeout), a deterministic fallback ensures every query still gets classified:

```python
RULE_PATTERNS = {
    "injury":    ["부상", "복귀", "injury", "injured", "out", "fitness"],
    "transfer":  ["이적", "영입", "transfer", "sign", "loan", "rumor"],
    "schedule":  ["다음 경기", "일정", "schedule", "fixture", "next match"],
    "prediction":["이길", "예측", "predict", "win", "odds", "bet"],
    "news":      ["뉴스", "최근", "news", "latest", "today"],
    "comparison":["vs", "비교", "compare", "better", "versus"],
    "explainer": ["규칙", "뭐야", "what is", "how does", "explain"],
}
```

### Where It Fits in the Pipeline

```
BEFORE (current):
  query → _retrieve() → _llm_generate() → response

AFTER (proposed):
  query → _extract_entity_names()
        → classify_intent()                    ← NEW (100-200ms)
        → log_to_query_logs()                  ← NEW (async, non-blocking)
        → _retrieve(query, intent, entities)   ← ENHANCED (intent-aware retrieval)
        → _llm_generate()
        → response
```

**Net latency impact:** +100-200ms for classification (parallelizable with entity extraction). Classification and logging are async — if either fails, the RAG pipeline proceeds unaffected.

---

## 5. Layer 3: Demand Signal Aggregation

### Problem

`generate_trend_snapshot` counts entity mentions per day. This is a vanity metric. A B2B client cannot act on "Mbappe was mentioned 47 times today."

### Solution: `demand_signals` Materialized View + New Aggregation RPC

### 5.1 Demand Signal Table

```sql
create table if not exists demand_signals (
  id              uuid primary key default uuid_generate_v4(),
  signal_date     date not null,
  signal_hour     int,                        -- 0-23, null for daily rollups
  -- Dimension
  entity_type     text,                       -- player | team | competition
  entity_name     text,
  intent          text not null,              -- from intent taxonomy
  sub_intent      text,
  temporal_frame  text,
  -- Metrics
  query_count     int not null default 0,
  unique_users    int not null default 0,     -- count of distinct anon_id
  avg_latency_ms  real,
  rag_hit_rate    real,                       -- % of queries where RAG returned useful docs
  followup_rate   real,                       -- % of queries that were rephrases (signal of dissatisfaction)
  -- Derived
  intensity_score real,                       -- query_count * (1 + followup_rate) / unique_users
  -- Meta
  created_at      timestamptz default now()
);

create index idx_ds_date on demand_signals(signal_date, intent);
create index idx_ds_entity on demand_signals(entity_name, signal_date);
```

### 5.2 Aggregation RPC (Replaces `generate_trend_snapshot`)

```sql
create or replace function generate_demand_signals(target_date date default current_date)
returns int
language plpgsql
set search_path = public
as $$
declare
  inserted int := 0;
begin
  -- Hourly aggregation by entity + intent
  insert into demand_signals (
    signal_date, signal_hour,
    entity_type, entity_name, intent, sub_intent, temporal_frame,
    query_count, unique_users, avg_latency_ms, rag_hit_rate, followup_rate,
    intensity_score
  )
  select
    target_date,
    extract(hour from ql.created_at)::int,
    e->>'type',
    e->>'name',
    ql.intent,
    ql.sub_intent,
    ql.temporal_frame,
    count(*),
    count(distinct ql.anon_id),
    avg(ql.latency_ms),
    avg(case when ql.rag_hit then 1.0 else 0.0 end),
    avg(case when ql.is_followup then 1.0 else 0.0 end),
    -- intensity: high query count + high followup rate = strong demand signal
    count(*)::real
      * (1.0 + avg(case when ql.is_followup then 1.0 else 0.0 end))
      / greatest(count(distinct ql.anon_id), 1)
  from query_logs ql,
       lateral jsonb_array_elements(ql.entities_json) as e
  where ql.created_at >= target_date::timestamptz
    and ql.created_at < (target_date + interval '1 day')::timestamptz
    and ql.intent is not null
  group by 1, 2, 3, 4, 5, 6, 7;

  get diagnostics inserted = row_count;

  -- Daily rollup (signal_hour = null)
  insert into demand_signals (
    signal_date, signal_hour,
    entity_type, entity_name, intent, sub_intent, temporal_frame,
    query_count, unique_users, avg_latency_ms, rag_hit_rate, followup_rate,
    intensity_score
  )
  select
    signal_date, null,
    entity_type, entity_name, intent, sub_intent, temporal_frame,
    sum(query_count), max(unique_users),
    avg(avg_latency_ms), avg(rag_hit_rate), avg(followup_rate),
    avg(intensity_score)
  from demand_signals
  where signal_date = target_date and signal_hour is not null
  group by 1, 3, 4, 5, 6, 7;

  return inserted;
end;
$$;
```

### 5.3 `intensity_score` Explained

```
intensity_score = query_count * (1 + followup_rate) / unique_users
```

| Scenario | query_count | followup_rate | unique_users | intensity | Interpretation |
|----------|------------|---------------|-------------|-----------|----------------|
| 50 users each asked once about Kane | 50 | 0.0 | 50 | 1.0 | Normal interest |
| 10 users asked 50 times about Kane, rephrasing | 50 | 0.6 | 10 | 8.0 | Intense unsatisfied demand |
| 200 users asked once about PL standings | 200 | 0.05 | 200 | 1.05 | Broad routine interest |
| 5 users asked 30 times about a transfer rumor | 30 | 0.8 | 5 | 10.8 | Breaking news demand |

High intensity + high followup_rate = fans want something La Paz can't answer well yet. This is a product feedback signal AND a B2B demand signal.

---

## 6. Anonymization Design

### Threat Model

| Threat | Mitigation |
|--------|------------|
| B2B client reverse-engineers user identity from demand_signals | demand_signals contains only aggregated counts, no per-user rows |
| query_logs.anon_id linked back to users.id | anon_id = SHA-256(user_id + daily_salt); salt rotated daily, never exposed via API |
| Small cohort re-identification (only 1 user asked about a niche player) | Suppress demand_signals rows where unique_users < k (k=5 default) |
| Query text contains PII (user typed their name) | query_text stored only in query_logs (service_role only, never exposed to B2B) |
| Session correlation across days | session_hash uses daily salt — same session on different days produces different hashes |

### Implementation

```python
import hashlib
import os

# Daily salt: generated once per day, stored in-memory only
_DAILY_SALT = os.urandom(32).hex()
_SALT_DATE = None

def _get_daily_salt() -> str:
    """Rotate salt at midnight UTC."""
    global _DAILY_SALT, _SALT_DATE
    from datetime import date, timezone
    today = date.today()
    if _SALT_DATE != today:
        _DAILY_SALT = os.urandom(32).hex()
        _SALT_DATE = today
    return _DAILY_SALT

def anonymize_id(user_id: str | None) -> str:
    """One-way hash. Cannot be reversed without the daily salt."""
    raw = (user_id or "anonymous") + _get_daily_salt()
    return hashlib.sha256(raw.encode()).hexdigest()[:16]
```

### RLS for Query Logs

```sql
alter table query_logs enable row level security;
-- service_role only — never exposed to anon/authenticated roles
create policy "query_logs_service_only" on query_logs
  for all using (false);

alter table demand_signals enable row level security;
-- B2B clients can read aggregated signals (no per-user data)
create policy "demand_signals_b2b_read" on demand_signals
  for select using (true);
-- But only rows with sufficient anonymity
create policy "demand_signals_k_anon" on demand_signals
  for select using (unique_users >= 5);
```

### Data Retention

| Table | Retention | Reason |
|-------|-----------|--------|
| `query_logs` | 90 days | Raw query data for debugging; auto-purge via pg_cron |
| `demand_signals` | Indefinite | Aggregated, anonymized; the commercial asset |
| `fan_events` | 30 days | Behavioral signals; short-lived |
| `chat_messages` | Per user deletion request | User-owned content; GDPR-compliant |

---

## 7. Future B2B Readiness (Data Design Only)

> **Scope constraint:** This section defines only the schema keys and aggregation primitives that make future B2B products possible. No B2B API endpoints are built in the current phase.

### What the Data Layer Enables

The combination of `query_logs` + `demand_signals` produces these **queryable dimensions** for any future B2B surface:

| Schema Key | Table | Future B2B Use |
|-----------|-------|---------------|
| `entity_name` + `entity_type` | `demand_signals` | Per-entity demand lookup |
| `intent` | `demand_signals` | Intent-based demand ranking |
| `intensity_score` | `demand_signals` | Spike / trend detection |
| `followup_rate` | `demand_signals` | Content gap identification |
| `league_code` | `demand_signals` | Per-league slicing |
| `unique_users` (k≥5 enforced) | `demand_signals` | Anonymized volume indicator |

### Existing B2B Endpoints (Unchanged)

The current shallow endpoints remain as-is and are not expanded:

```
GET /b2b/trends        → raw counts from trend_snapshots
GET /b2b/fan-segments  → static segments
GET /b2b/entity-buzz   → entity mention counts
```

When query volume in `demand_signals` reaches sufficient scale, these can be replaced with intent-aware endpoints. Endpoint design is deferred to that phase.

---

## 8. Fan Segments (Future — Data Design Only)

> **Scope constraint:** Segment definitions are documented here for future reference. No segmentation logic or SQL jobs are implemented in the current phase.

### Existing Table

`fan_segments` table exists with `criteria jsonb` but is never populated. It remains as-is.

### Segment Definitions (Derivable from `query_logs`)

When sufficient data accumulates, these segments can be derived via SQL aggregation on `query_logs.intent` and `query_logs.anon_id`. No ML required.

| Segment | Derivation Key | Schema Fields Used |
|---------|---------------|-------------------|
| Stat Analysts | High `stat_lookup` / `comparison` ratio per `anon_id` | `intent`, `anon_id` |
| Transfer Watchers | High `transfer` intent ratio | `intent`, `anon_id` |
| Match-Day Fans | High `live` / `today` `temporal_frame` ratio | `temporal_frame`, `anon_id` |
| Casual Browsers | Low query count per session, diverse intents | `session_hash`, `query_position` |

Implementation is deferred until `query_logs` reaches meaningful volume (target: 10k+ rows with diverse `anon_id`).

---

## 9. Data Asset Summary

> **Scope constraint:** This section describes what the collected data enables commercially. No pricing tiers, product endpoints, or B2B features are built in the current phase.

### Core Data Asset

Football data (scores, stats, transfers) is commodity. **Fan demand intelligence** — what fans ask, when, about whom, and whether they're satisfied — is proprietary and uniquely generated by `query_logs` + `demand_signals`.

### Key Schema Fields That Enable Future Monetization

| Field | Table | Commercial Signal |
|-------|-------|------------------|
| `intensity_score` | `demand_signals` | Entity-level demand trending |
| `followup_rate` | `demand_signals` | Content gap / fan dissatisfaction indicator |
| `rag_hit_rate` | `demand_signals` | RAG quality feedback (also drives internal roadmap) |
| `intent` | `demand_signals` | Intent-based demand segmentation |
| `league_code` | `demand_signals` | Per-league demand slicing |
| `unique_users` (k≥5) | `demand_signals` | Anonymized volume — privacy-safe for regulated markets |

### Internal Feedback Loop

`followup_rate` and `rag_hit_rate` double as internal product signals: high followup_rate for a specific intent means "invest in better RAG coverage here." This data serves both B2C quality improvement and future B2B readiness simultaneously.

---

## 10. Implementation Roadmap

### Phase 1: Foundation (Week 1-2)

| Task | Change Type | Files Affected |
|------|------------|----------------|
| Create `query_logs` table | SQL migration | `supabase/migrations/004_query_logs.sql` |
| Create `demand_signals` table | SQL migration | Same file |
| Implement `anonymize_id()` | Python function | `agents/shared_config.py` |
| Implement `classify_intent()` with Gemini structured output | Python function | `agents/intent_classifier.py` (new, ~120 lines) |
| Implement rule-based fallback classifier | Python function | Same file |
| Wire classification into `/chat` and `/chat/stream` before `_retrieve()` | Modify existing | `agents/agent_5_api.py` |
| Wire `query_logs` insert (async, non-blocking) | Modify existing | `agents/agent_5_api.py` |
| Wire classification into `/search` | Modify existing | `agents/agent_5_api.py` |

### Phase 2: Aggregation (Week 3)

| Task | Change Type | Files Affected |
|------|------------|----------------|
| Create `generate_demand_signals()` RPC | SQL migration | `supabase/migrations/005_demand_signals_rpc.sql` |
| Add daily cron trigger (pg_cron or `scripts/daily_crawl.py`) | Script modification | `scripts/daily_crawl.py` |
| Implement `followup_rate` detection (compare current query to previous in session) | Python logic | `agents/agent_5_api.py` |
| Create demand_signals k-anonymity RLS policy | SQL migration | Same as above |

### Phase 3: Internal Feedback & RAG Quality (Week 4)

| Task | Change Type | Files Affected |
|------|------------|----------------|
| Use `followup_rate` per intent to prioritize RAG doc coverage gaps | Analytics review | `docs/` |
| Use `rag_hit_rate` per entity to identify missing documents | Analytics review | `docs/` |
| Implement intent-aware retrieval (route `schedule` queries to match table, `injury` to articles) | Modify existing | `agents/agent_5_api.py` |
| Generate weekly demand intelligence report (automated, internal-only) | New script | `scripts/weekly_demand_report.py` |

> B2B API endpoints are deferred. Build when `demand_signals` volume justifies it.

---

## 11. Constraints

| Constraint | Rationale |
|------------|-----------|
| **No custom ML training** | Classification uses existing LLM API (Gemini). Segmentation uses SQL aggregation. No training loops, no model files, no GPU. |
| **No new LLM provider** | Uses same Gemini 2.0 Flash already in the stack. Classification is a lightweight structured-output call. |
| **No PII in B2B layer** | `demand_signals` contains only aggregated counts. `query_logs` is service_role-only. Daily salt rotation prevents cross-day correlation. |
| **Classification failure is non-blocking** | If Gemini classification times out, rule-based fallback runs. If both fail, query proceeds to RAG unclassified; `intent` is logged as `null`. |
| **Backward compatible** | All existing B2C and B2B endpoints unchanged. No new endpoints in this phase. Old `fan_events` table retained for behavioral signals. |

---

## 12. New File Inventory

| File | Lines (est.) | Purpose |
|------|-------------|---------|
| `supabase/migrations/004_query_logs.sql` | ~80 | `query_logs` + `demand_signals` tables, indexes, RLS |
| `supabase/migrations/005_demand_signals_rpc.sql` | ~80 | `generate_demand_signals()` RPC |
| `agents/intent_classifier.py` | ~120 | `classify_intent()` + rule-based fallback |
| Modifications to `agents/agent_5_api.py` | ~80 net new | Wire classification, logging, language-adaptive prompt |
| Modifications to `agents/shared_config.py` | ~20 net new | `anonymize_id()` function |
| `scripts/weekly_demand_report.py` | ~80 | Automated internal demand intelligence summary |

**Total new code: ~440 lines. Zero new dependencies. Zero ML training. Zero new B2B endpoints.**

---

## 13. League Rollout Policy

### 13.1 Tier Definitions

| Tier | Leagues | Data Sources | Status | Coverage Goal |
|------|---------|-------------|--------|---------------|
| **Tier 1 — EU Big-5 (MVP)** | EPL, La Liga, Bundesliga, Serie A, Ligue 1 | StatsBomb (free), football-data.org (10 req/min), Understat, Transfermarkt (via soccerdata) | Partially implemented | Full: structure + matches + events + stats + transfers + articles |
| **Tier 2 — UEFA & Secondary** | Champions League, Europa League, Eredivisie, Primeira Liga, EFL Championship, Brasileirão | football-data.org (most covered), FBref fallback | Schema-ready, collectors not wired | Structure + matches + standings. Events optional. |
| **Tier 3 — Asian Expansion** | K League 1/2, J1 League, Chinese Super League, A-League, ISL, Saudi Pro League | API-Football (per-league), FBref, RSS feeds | K League implemented, others planned | Structure + matches + standings + news. Event-level data if source available. |

### 13.2 Rollout Sequencing

```
Phase 1 (MVP — current):
  Tier 1 Big-5 → full pipeline (Agents 1-5)
  ────────────────────────────────────────────
  Collectors: agent_1 + collectors/ + agent_2 + agent_3
  Documents:  match_report, team_profile, player_profile,
              transfer_news, league_standing, scorer_ranking, article
  Goal:       RAG answers any Big-5 question from DB data

Phase 2 (Expansion):
  Tier 2 UEFA/secondary → structure + match + standings only
  ────────────────────────────────────────────────────────
  Add league codes to FD_LEAGUES dict in collectors/_common.py
  Reuse existing collector functions (league-agnostic by design)
  Document generation: same generators, broader input
  Goal:       Basic coverage; fans can ask about UCL, Eredivisie

Phase 3 (Asia):
  Tier 3 Asian leagues → modular collector per region
  ────────────────────────────────────────────────────
  Pattern: kleague_collectors.py (already exists as template)
  Each region gets: {region}_collectors.py
  Shared interface: collect_{region}_structure(), collect_{region}_matches(), etc.
  Goal:       Korean/Japanese/Asian fan base served natively
```

### 13.3 Tier Gating Rules

| Rule | Enforcement |
|------|------------|
| Tier 1 data must be complete before Tier 2 work begins | `team_season_stats` row count > 0 for all 5 Big-5 leagues |
| Tier 2 does not require event-level data | `match_events` collection optional; skip if source doesn't provide x/y coords |
| Tier 3 collectors must follow the `kleague_collectors.py` pattern | Separate file per region; shared `_common.py` utilities; no cross-region imports |
| No league-specific code in Agent 5 (API server) | Agent 5 queries by `competition_id`; never by league abbreviation string |
| Fan intelligence aggregation must include `league_tag` | `query_logs` and `demand_signals` must carry league dimension for future per-league analysis |

### 13.4 Current League-Specific Coupling (Must Be Resolved)

The codebase has 6 places where league identity is hardcoded. These must be refactored to a single registry before Tier 2 rollout.

| Location | Coupling | Resolution |
|----------|---------|------------|
| `agents/agent_1_structure.py:54-58` | `FD_LEAGUES = {"PL": ..., "BL1": ...}` hardcoded Big-5 | Move to `agents/league_registry.py` as a single source of truth |
| `agents/collectors.py:31-35` | Duplicate of same dict | Import from `league_registry.py` |
| `agents/collectors/_common.py:104-108` | Third copy of abbreviation map | Import from `league_registry.py` |
| `agents/doc_generators.py:30-41` | `COMP_ABBR_MAP` fourth copy | Import from `league_registry.py` |
| `agents/agent_5_api.py:136-139` | `KOREAN_TERM_MAP` has league names hardcoded | Load from `league_registry.py` + i18n entity map |
| `agents/kleague_collectors.py:34-43` | K-League IDs hardcoded | Keep in-file (region-specific by design), but register in `league_registry.py` for discovery |

**Proposed `league_registry.py`:**

```python
"""Single source of truth for all supported leagues.

Every collector, document generator, and API endpoint imports from here.
To add a new league: add one entry to LEAGUES. No other file changes needed.
"""

from __future__ import annotations
from dataclasses import dataclass

@dataclass(frozen=True)
class League:
    code: str              # football-data.org code or internal ID
    name: str              # Canonical English name
    country: str           # Country name (English)
    country_code: str      # ISO 3166-1 alpha-2
    tier: int              # 1, 2, or 3
    fd_code: str | None    # football-data.org competition code (None if not available)
    af_id: int | None      # API-Football league ID (None if not available)
    statsbomb: bool        # Available in StatsBomb Open Data
    active: bool           # Currently collected by pipeline

LEAGUES: dict[str, League] = {
    # ── Tier 1: EU Big-5 (MVP) ──
    "PL":  League("PL",  "Premier League", "England",  "GB", 1, "PL",  39,  True,  True),
    "PD":  League("PD",  "La Liga",        "Spain",    "ES", 1, "PD",  140, True,  True),
    "BL1": League("BL1", "Bundesliga",     "Germany",  "DE", 1, "BL1", 78,  True,  True),
    "SA":  League("SA",  "Serie A",        "Italy",    "IT", 1, "SA",  135, True,  True),
    "FL1": League("FL1", "Ligue 1",        "France",   "FR", 1, "FL1", 61,  True,  True),
    # ── Tier 2: UEFA & Secondary ──
    "CL":  League("CL",  "Champions League","Europe",  "EU", 2, "CL",  2,   True,  False),
    "EL":  League("EL",  "Europa League",  "Europe",   "EU", 2, "EL",  3,   False, False),
    "DED": League("DED", "Eredivisie",     "Netherlands","NL",2, "DED", 88,  False, False),
    "PPL": League("PPL", "Primeira Liga",  "Portugal", "PT", 2, "PPL", 94,  False, False),
    "ELC": League("ELC", "Championship",   "England",  "GB", 2, "ELC", 40,  False, False),
    "BSA": League("BSA", "Brasileirão A",  "Brazil",   "BR", 2, "BSA", 71,  False, False),
    # ── Tier 3: Asian Expansion ──
    "KL1": League("KL1", "K League 1",     "South Korea","KR",3, None, 292, False, True),
    "KL2": League("KL2", "K League 2",     "South Korea","KR",3, None, 293, False, False),
    "J1":  League("J1",  "J1 League",      "Japan",    "JP", 3, None, 98,  False, False),
    "CSL": League("CSL", "Chinese Super League","China","CN", 3, None, 169, False, False),
    "SPL": League("SPL", "Saudi Pro League","Saudi Arabia","SA",3,None,307, False, False),
}

def get_active_leagues(tier: int | None = None) -> list[League]:
    """Return leagues currently collected by pipeline."""
    return [l for l in LEAGUES.values()
            if l.active and (tier is None or l.tier == tier)]

def get_league(code: str) -> League | None:
    return LEAGUES.get(code)

def get_abbr_map() -> dict[str, str]:
    """code → full name mapping (replaces COMP_ABBR_MAP)."""
    return {l.code: l.name for l in LEAGUES.values()}

def get_fd_leagues() -> dict[str, dict]:
    """football-data.org league map (replaces FD_LEAGUES)."""
    return {l.fd_code: {"name": l.name, "country": l.country}
            for l in LEAGUES.values() if l.fd_code and l.active}
```

---

## 14. League-Agnostic Schema Enforcement

### 14.1 Current State

The existing schema uses `competition_id` (UUID FK to `competitions`) as the league dimension. This is structurally correct — `competitions` already has `name`, `country`, and `source`. However:

1. **`country_code` is missing.** `competitions.country` stores "England" (string), not "GB" (ISO code). Aggregation by country requires string matching.
2. **`query_logs` has no league dimension.** When a fan asks about La Liga, there's no structured `league_tag` on the query log.
3. **`demand_signals` can't slice by league.** Without a league dimension, B2B per-league products are impossible.

### 14.2 Schema Changes

#### Add `country_code` to `competitions`

```sql
-- Migration: 006_league_agnostic.sql

-- 1. Add country_code column
alter table competitions add column if not exists country_code text;

-- 2. Backfill from existing country names
update competitions set country_code = case
  when country ilike 'england%' then 'GB'
  when country ilike 'spain%'   then 'ES'
  when country ilike 'germany%' then 'DE'
  when country ilike 'italy%'   then 'IT'
  when country ilike 'france%'  then 'FR'
  when country ilike '%korea%'  then 'KR'
  when country ilike 'japan%'   then 'JP'
  when country ilike 'netherlands%' then 'NL'
  when country ilike 'portugal%' then 'PT'
  when country ilike 'brazil%'  then 'BR'
  else upper(left(country, 2))
end
where country_code is null and country is not null;

-- 3. Add league_code column (maps to league_registry.py codes)
alter table competitions add column if not exists league_code text;

-- 4. Index for efficient league-scoped queries
create index if not exists idx_competitions_league_code
  on competitions(league_code);
create index if not exists idx_competitions_country_code
  on competitions(country_code);
```

#### Extend `query_logs` (from Section 3)

```sql
-- Add to query_logs table definition:
alter table query_logs add column if not exists league_tags    text[] default '{}';
alter table query_logs add column if not exists ui_language    text default 'ko';
alter table query_logs add column if not exists normalized_query text;

create index if not exists idx_ql_league on query_logs using gin(league_tags);
create index if not exists idx_ql_lang on query_logs(ui_language);
```

#### Extend `demand_signals` (from Section 5)

```sql
-- Add league dimension to demand_signals:
alter table demand_signals add column if not exists league_code   text;
alter table demand_signals add column if not exists country_code  text;
alter table demand_signals add column if not exists ui_language   text;

create index if not exists idx_ds_league on demand_signals(league_code, signal_date);
create index if not exists idx_ds_lang on demand_signals(ui_language, signal_date);
```

### 14.3 Entity Tagging Contract

Every table that references a league context must carry the triad: `competition_id` (FK) + `league_code` (denormalized for fast queries) + `country_code` (denormalized). This applies to:

| Table | Has `competition_id` | Needs `league_code` | Needs `country_code` |
|-------|---------------------|--------------------|--------------------|
| seasons | Yes | Add | Add (from competition) |
| team_seasons | Yes | Add | Add |
| player_season_stats | Yes | Add | Add |
| team_season_stats | Yes | Add | Add |
| matches | Yes | Add | Add |
| documents | Via metadata | Add to metadata schema | Add to metadata schema |
| **query_logs** | N/A | `league_tags[]` (array — query may reference multiple leagues) | Via league_tags lookup |
| **demand_signals** | N/A | `league_code` (single — aggregated per league) | `country_code` |

Denormalization is deliberate: future per-league aggregation queries should not require joins through `competitions` on every request.

---

## 15. Multilingual Strategy

### 15.1 Design Principle

```
Store facts in English (canonical). Localize responses at render time.
Log the user's language AND the normalized (English) query.
```

### 15.2 The Three Language Layers

```
Layer 1: USER INPUT          Layer 2: CANONICAL STORE       Layer 3: RESPONSE RENDER
─────────────────────       ────────────────────────       ───────────────────────
Korean: "손흥민 골 수"   →   English: "Heung-Min Son       →   Korean: "손흥민은 이번
Japanese: "ソン 得点"    →    goals this season"            →    시즌 15골을 기록..."
English: "Son goals"    →                                  →   English: "Son has scored
                                                                15 goals this season..."
                                                           →   Japanese: "ソンは今シーズン
                                                                15ゴールを..."
```

### 15.3 Where Each Language Lives

| Component | Language | Rationale |
|-----------|----------|-----------|
| `documents.content` | **English** | Embedding model (`paraphrase-multilingual-MiniLM-L12-v2`) handles multilingual input, but canonical English documents ensure consistent retrieval regardless of query language |
| `documents.title` | **English** | Consistent indexing |
| `documents.metadata` | **English** | Machine-readable; not user-facing |
| `query_logs.query_text` | **Original (as typed)** | Preserves user intent nuance |
| `query_logs.normalized_query` | **English** | Translation of query for cross-language aggregation |
| `query_logs.ui_language` | **ISO 639-1 code** | `ko`, `en`, `ja`, etc. |
| LLM system prompt | **Adaptive** | Instructs LLM to respond in `ui_language` |
| Frontend i18n | **Per locale** | UI chrome (buttons, labels, navigation) |

### 15.4 Normalization Pipeline

Current state: `_translate_query_to_english()` in `agent_5_api.py` uses a hardcoded 50-entry Korean dictionary. This doesn't scale.

**Proposed: LLM-based normalization (bundled with intent classification)**

The intent classification call (Section 4) already processes the query through Gemini. Extend the structured output to include normalization:

```python
CLASSIFY_AND_NORMALIZE_PROMPT = """Classify and normalize this football query.

Query: "{query}"
UI Language: "{ui_language}"
Detected entities: {entities}

Return JSON:
{{
  "intent": "stat_lookup|comparison|news|opinion|prediction|transfer|injury|schedule|explainer",
  "sub_intent": "<specific>",
  "temporal_frame": "live|today|this_week|this_season|historical|transfer_window",
  "entities": [
    {{"name": "<canonical English name>", "type": "player|team|competition", "confidence": 0.95}}
  ],
  "league_tags": ["PL", "CL"],
  "normalized_query": "<English translation of the query>",
  "is_followup": false
}}"""
```

One LLM call produces: intent + entities + league_tags + normalized_query. Cost: same ~0.001 USD. No additional latency.

**Rule-based fallback normalization:**

```python
def normalize_query_fallback(query: str, ui_language: str) -> str:
    """Deterministic normalization when LLM is unavailable."""
    if ui_language == "en":
        return query
    # Apply existing KOREAN_ENTITY_MAP + KOREAN_TERM_MAP
    normalized = _translate_query_to_english(query)
    return normalized.strip()
```

### 15.5 Response Localization

The LLM already responds in Korean because the system prompt says "한국어로 자연스럽게 답변하되". This becomes dynamic:

```python
SYSTEM_PROMPT_TEMPLATE = (
    "You are La Paz, a professional football AI assistant.\n"
    "Use the provided DB data and web search results to answer accurately.\n"
    "Respond in {language_name}.\n"
    "When citing player names, include both the local script and Latin script.\n"
    "When citing statistics, always include the source and season.\n"
    "Rules:\n"
    "- Use the provided context data thoroughly.\n"
    "- Cite numbers and dates precisely.\n"
    "- If uncertain, state that it's an estimate.\n"
)

LANGUAGE_MAP = {
    "ko": "Korean (한국어)",
    "en": "English",
    "ja": "Japanese (日本語)",
    "es": "Spanish (Español)",
    "de": "German (Deutsch)",
    "fr": "French (Français)",
    "pt": "Portuguese (Português)",
    "zh": "Chinese (中文)",
}
```

**Key constraint:** Documents remain in English. The LLM translates at generation time. This means:
- Vector search works identically for all languages (multilingual embedding model)
- Document generation runs once, not per-locale
- Adding a new language requires zero data pipeline changes — only a new system prompt language

### 15.6 Entity Map Scaling Strategy

The hardcoded `KOREAN_ENTITY_MAP` (15 players, 10 teams) cannot scale. Replace with:

**Phase 1 (immediate):** Keep hardcoded map as a fast lookup cache. Use it for the top 50 most-queried entities.

**Phase 2 (Tier 2 rollout):** Build entity alias table in Supabase:

```sql
create table if not exists entity_aliases (
  id            uuid primary key default uuid_generate_v4(),
  entity_type   text not null,        -- player | team | competition
  entity_id     uuid not null,        -- FK to players.id, teams.id, or competitions.id
  canonical     text not null,        -- English canonical name
  alias         text not null,        -- Localized alias
  language      text not null,        -- ISO 639-1
  source        text default 'manual',-- manual | auto_llm | wikidata
  created_at    timestamptz default now(),
  unique (entity_type, alias, language)
);

create index idx_ea_alias on entity_aliases(alias, language);
create index idx_ea_canonical on entity_aliases(canonical);
```

This replaces:
- `KOREAN_ENTITY_MAP` in `agent_5_api.py` → `SELECT canonical FROM entity_aliases WHERE alias = '손흥민' AND language = 'ko'`
- `teams.aliases` jsonb array → Normalized into `entity_aliases` with `entity_type = 'team'`

**Phase 3 (Tier 3 rollout):** Auto-populate from Wikidata for new leagues. Each player/team in Wikidata has multilingual labels. A one-time batch script pulls Japanese, Chinese, Arabic names for all entities.

### 15.7 Frontend i18n Extension

Current: `ko.ts` + `en.ts` (2 locales, 57 keys each).

Extension path:

| Locale | Priority | Trigger |
|--------|----------|---------|
| `ko` (Korean) | Current | Default for MVP |
| `en` (English) | Current | Already implemented |
| `ja` (Japanese) | Tier 3 | J1 League rollout |
| `es` (Spanish) | Tier 2 | La Liga native fans |
| `de` (German) | Tier 2 | Bundesliga native fans |
| `pt` (Portuguese) | Tier 2 | Brasileirão rollout |
| `zh` (Chinese) | Tier 3 | CSL rollout |

New locale files follow existing pattern: `frontend/lib/i18n/{code}.ts`. The `LocaleProvider` and `useLocaleStore` already support dynamic locale switching — no structural frontend changes needed.

### 15.8 Query Log Schema (Final)

Combining Section 3 (query_logs) + Section 14 (league-agnostic) + Section 15 (multilingual):

```sql
create table if not exists query_logs (
  id                uuid primary key default uuid_generate_v4(),
  -- Identity (anonymized)
  anon_id           text not null,
  session_hash      text,
  -- Raw query (original language)
  query_text        text not null,
  ui_language       text not null default 'ko',    -- ISO 639-1: ko, en, ja, ...
  normalized_query  text,                          -- English translation
  channel           text not null default 'chat',
  -- Classification
  intent            text,
  sub_intent        text,
  temporal_frame    text,
  entities_json     jsonb default '[]',
  league_tags       text[] default '{}',           -- ["PL", "CL"]
  -- Response metadata
  source_count      int default 0,
  rag_hit           boolean default false,
  model_used        text,
  latency_ms        real,
  -- Session context
  is_followup       boolean default false,
  query_position    int default 1,
  -- Timestamps
  created_at        timestamptz default now()
);
```

This single row captures: what the user asked (original + normalized), in what language, about which league, with what intent, and whether the system answered well. Every field feeds the fan intelligence pipeline. Every field is league-agnostic and language-agnostic by design.

---

## 16. Updated Implementation Roadmap

The original roadmap (Section 10) is extended to incorporate league rollout and multilingual support. B2B API building is deferred; Phase 3 now focuses on internal feedback and RAG quality:

### Phase 1: Foundation (Week 1-2) — unchanged

### Phase 2: Aggregation (Week 3) — unchanged

### Phase 3: Internal Feedback & RAG Quality (Week 4) — replaces former "B2B API" phase

### Phase 4: League Agnostic Refactor (Week 5)

| Task | Change Type | Files Affected |
|------|------------|----------------|
| Create `agents/league_registry.py` | New file (~80 lines) | N/A |
| Replace all hardcoded league dicts with imports from registry | Refactor | `agent_1_structure.py`, `collectors.py`, `collectors/_common.py`, `doc_generators.py` |
| Add `country_code`, `league_code` to competitions | SQL migration | `supabase/migrations/006_league_agnostic.sql` |
| Add `league_tags`, `ui_language`, `normalized_query` to query_logs | SQL migration | Same migration file |
| Add `league_code`, `country_code`, `ui_language` to demand_signals | SQL migration | Same migration file |
| Extend intent classifier to output `league_tags` + `normalized_query` | Modify | `agents/intent_classifier.py` |
| Make LLM system prompt language-adaptive | Modify | `agents/agent_5_api.py` |

### Phase 5: Multilingual & Tier 2 (Week 6-7)

| Task | Change Type | Files Affected |
|------|------------|----------------|
| Create `entity_aliases` table | SQL migration | `supabase/migrations/007_entity_aliases.sql` |
| Populate entity_aliases from existing `KOREAN_ENTITY_MAP` + `teams.aliases` | Data migration script | `scripts/migrate_aliases.py` |
| Replace hardcoded `KOREAN_ENTITY_MAP` with DB lookup + in-memory cache | Modify | `agents/agent_5_api.py` |
| Add Tier 2 league codes to `league_registry.py` (set `active=False` initially) | Modify | `agents/league_registry.py` |
| Wire Tier 2 football-data.org collection (activate leagues one by one) | Modify | `agents/agent_1_structure.py`, `agents/agent_2_match.py` |
| Add `ja.ts`, `es.ts` frontend locale files | New files | `frontend/lib/i18n/` |

### Phase 6: Tier 3 Asian Expansion (Week 8+)

| Task | Change Type | Files Affected |
|------|------------|----------------|
| Create `agents/jleague_collectors.py` following kleague pattern | New file | N/A |
| Populate Japanese entity aliases (from Wikidata or manual) | Script | `scripts/populate_aliases.py` |
| Activate J1 League in `league_registry.py` | Modify | `agents/league_registry.py` |
| Repeat pattern for CSL, SPL as demand signals justify | New files per region | `agents/{region}_collectors.py` |

---

## 17. Updated Constraints

| Constraint | Rationale |
|------------|-----------|
| **League-agnostic code only in Agent 5** | API server must never branch on league abbreviation. Query by `competition_id` or `league_code` from registry. |
| **Documents stored in English only** | Multilingual embedding model handles cross-language retrieval. One document set serves all locales. |
| **UI language detected, not assumed** | Frontend sends `Accept-Language` header or user preference. Backend logs `ui_language` per query. |
| **Entity aliases are the scaling mechanism** | No hardcoded translation dictionaries beyond the initial cache. All new locales populate `entity_aliases` table. |
| **Tier 2/3 activation is data-driven** | Only activate a league in the registry when `demand_signals` show sufficient query volume for that league from fans. The fan intelligence data itself drives the expansion roadmap. |
| **No custom ML training** | Unchanged. Normalization, classification, and localization all use the existing Gemini API. |

---

## 18. Updated File Inventory

| File | Lines (est.) | Purpose |
|------|-------------|---------|
| `supabase/migrations/004_query_logs.sql` | ~80 | `query_logs` + `demand_signals` tables, indexes, RLS |
| `supabase/migrations/005_demand_signals_rpc.sql` | ~80 | `generate_demand_signals()` RPC |
| `supabase/migrations/006_league_agnostic.sql` | ~60 | `country_code`, `league_code` columns + `entity_aliases` table |
| `agents/league_registry.py` | ~80 | Single source of truth for all leagues |
| `agents/intent_classifier.py` | ~150 | `classify_intent()` + normalization + rule-based fallback |
| Modifications to `agents/agent_5_api.py` | ~100 net new | Classification, logging, language-adaptive prompt |
| Modifications to `agents/shared_config.py` | ~20 net new | `anonymize_id()` function |
| `scripts/weekly_demand_report.py` | ~80 | Automated demand intelligence summary |
| `scripts/migrate_aliases.py` | ~60 | One-time migration from hardcoded maps to entity_aliases |

**Total new code: ~610 lines. Zero new dependencies. Zero ML training. Zero new B2B endpoints. Scales to any league and any language.**

---

*This architecture converts La Paz from a Q&A tool into an intelligence platform. The answers are the B2C hook. The demand signals are the future-ready data asset. The league-agnostic, language-neutral data layer ensures the platform scales globally without architectural rewrites. B2B product endpoints are deferred until data volume justifies them.*
