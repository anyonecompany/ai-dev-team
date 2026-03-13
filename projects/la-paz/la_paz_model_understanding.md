# La Paz — Model & Architecture Understanding Report

> Generated: 2026-02-20
> Scope: Read-only codebase analysis (no code modifications)
> Analyst: Claude Opus 4.6

---

## 1. High-Level Objective

**La Paz** is a **B2C2C football AI Q&A service** built on a **Smart Wrapper + RAG (Retrieval-Augmented Generation)** architecture. It is **not** a custom-trained ML model project. Instead, it orchestrates pre-trained models and LLM APIs to deliver fact-grounded football intelligence.

### What Problem It Solves

| Audience | Problem | Solution |
|----------|---------|----------|
| **B2C (Fans)** | Football data is scattered across sources; fans can't ask natural-language questions and get accurate, sourced answers | RAG-powered chat (Korean/English), semantic search, team/player lookup, match predictions |
| **B2B (Media/Analytics)** | No aggregated fan engagement analytics or trend data | API-key-secured endpoints for trend snapshots, fan segments, entity buzz rankings |

### Core Value Proposition
Ingest data from 6+ football sources, normalize into 31 Supabase tables, embed as 384-dim vectors, and serve answers through LLM generation with source attribution — all verifiable, no hallucination by design.

---

## 2. Model Architecture Hypothesis

### 2.1 Classification: This is NOT a Traditional ML Project

After scanning the entire codebase (6,000+ lines Python, 3,600+ lines TypeScript, 1,200 lines SQL):

| Question | Answer | Evidence |
|----------|--------|----------|
| **Is there a custom model architecture?** | **No** | Zero `class ...Model(nn.Module)`, zero training loops, zero loss functions |
| **Is there model training code?** | **No** | `scikit-learn` is in `requirements.txt` but never imported in any agent file |
| **Is there a neural network definition?** | **No** | No PyTorch `nn.*`, no TensorFlow, no custom layers |
| **What "AI" does it use?** | **Pre-trained embeddings + LLM API calls** | SentenceTransformer (inference only) + Gemini/DeepSeek (API calls) |

### 2.2 Actual Architecture: RAG Pipeline

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        LA PAZ ARCHITECTURE                              │
│                                                                         │
│  DATA INGESTION (Agents 1-3)                                           │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐                 │
│  │ Agent 1      │  │ Agent 2      │  │ Agent 3      │                 │
│  │ Structure    │──│ Match+Perf   │  │ Narrative    │                 │
│  │ StatsBomb    │  │ Events, xG   │  │ Transfers    │                 │
│  │ FD.org       │  │ Standings    │  │ Injuries     │                 │
│  │ FBref        │  │ Top Scorers  │  │ RSS News     │                 │
│  │ API-Football │  │ Understat    │  │ Transfermarkt│                 │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘                 │
│         │                  │                  │                         │
│  ───────┴──────────────────┴──────────────────┴───────                 │
│                            │                                            │
│  DOCUMENT GENERATION + EMBEDDING (Agent 4)                             │
│  ┌─────────────────────────────────────────────┐                       │
│  │ doc_generators.py → Natural language docs    │                       │
│  │ SentenceTransformer (MiniLM-L12-v2, 384d)   │  ← PRE-TRAINED      │
│  │ Batch embed → pgvector (Supabase)            │     NO TRAINING     │
│  └──────────────────────┬──────────────────────┘                       │
│                         │                                               │
│  RAG SERVING (Agent 5)                                                  │
│  ┌─────────────────────────────────────────────┐                       │
│  │ Query → Korean→English Translation           │                       │
│  │ Hybrid Search:                               │                       │
│  │   1. Entity direct fetch (SQL)               │                       │
│  │   2. pgvector cosine similarity              │                       │
│  │   3. ILIKE keyword fallback                  │                       │
│  │   4. DuckDuckGo web search (last resort)     │                       │
│  │ Context ranking → LLM Generation:            │                       │
│  │   Primary:  Gemini 2.0 Flash (Google)        │  ← API CALLS ONLY   │
│  │   Fallback: DeepSeek V3.2                    │     NO FINE-TUNING   │
│  │   Fallback: Web search formatted response    │                       │
│  └─────────────────────────────────────────────┘                       │
└─────────────────────────────────────────────────────────────────────────┘
```

### 2.3 Model Components (All Pre-Trained, Zero Custom Training)

| Component | Model | Usage | Trainable? |
|-----------|-------|-------|------------|
| **Embedding** | `paraphrase-multilingual-MiniLM-L12-v2` | Document + query embedding (384-dim) | No — inference only |
| **Generation (primary)** | Gemini 2.0 Flash | RAG answer generation | No — API call |
| **Generation (fallback)** | DeepSeek V3.2 | RAG answer generation | No — API call |
| **Search** | pgvector (ivfflat) | Cosine similarity over 384-dim vectors | No — index-based |
| **Translation** | Hardcoded dictionary | Korean entity/term → English mapping | No — static dict |
| **scikit-learn** | Listed in requirements | **Never imported anywhere** | N/A — unused |

---

## 3. Inference: What Type of AI System Is This?

| Category | Is La Paz This? | Explanation |
|----------|----------------|-------------|
| **Tactical Analysis** | Partially | Has `formations` table and `match_events` data (passes, shots, tackles with x/y coordinates). But no tactical model — data is collected and served raw, not analyzed |
| **Player Evaluation** | Partially | Collects `player_season_stats` (goals, assists, xG, xA) and generates player profile documents. But no evaluation model — profiles are template-generated text, not scored |
| **Match Outcome Prediction** | No | Has `fan_predictions` table for fans to submit predictions, but there is **no predictive model** — it's a voting/opinion feature, not ML prediction |
| **Graph-Based Modeling** | No | No graph structures, no GNN, no network analysis. Team/player relationships are stored as relational FK joins |
| **Sequence Modeling** | No | No LSTM, no transformer training, no time-series models. Match events have temporal ordering but are stored as flat records |
| **RAG / Information Retrieval** | **Yes — this is the core** | The entire system is a Retrieval-Augmented Generation pipeline: embed → search → generate |

### Summary Classification

> **La Paz is a domain-specific RAG application for football, not an ML model-building project.**
> It uses pre-trained embedding models and commercial LLM APIs to provide grounded Q&A over structured football data.

---

## 4. Data Schema Expectations

### 4.1 Input Data Types

| Domain | Tables | Row Counts (Observed) | Sources |
|--------|--------|----------------------|---------|
| **Structure** | competitions, seasons, teams, players, managers, team_seasons, player_contracts, manager_tenures | teams: 32, players: unknown | StatsBomb, football-data.org, FBref, API-Football |
| **Match** | matches, lineups, match_events | matches: 350, events: 297,832 | StatsBomb (primary), football-data.org |
| **Performance** | player_match_stats, player_season_stats, team_match_stats, team_season_stats | team_stats: **0 rows** | football-data.org standings, Understat xG |
| **Narrative** | transfers, injuries, articles | unknown | Transfermarkt, BBC/Guardian/ESPN/Reddit RSS |
| **RAG** | documents (384-dim pgvector) | 350 rows | Generated by Agent 4 |
| **Fan Engagement** | users, chat_sessions, chat_messages, fan_events, fan_predictions | unknown | User interactions |
| **B2B** | trend_snapshots, fan_segments, b2b_clients, b2b_api_logs | unknown | Aggregated from fan_events |
| **Pipeline** | agent_status, pipeline_runs | 5 agents tracked | Internal IPC |

### 4.2 Data Flow

```
External Sources                    Supabase (31 tables)             Documents (pgvector)
─────────────────                  ─────────────────────            ──────────────────────
StatsBomb Open Data ─────┐
football-data.org API ───┤
FBref (soccerdata) ──────┤──→  Structure + Match tables ──→  match_report docs
Understat API ───────────┤                                    team_profile docs
Transfermarkt ───────────┤──→  Narrative tables ──────────→  player_profile docs
RSS Feeds (4 sources) ───┤                                    transfer_news docs
API-Football (K리그) ────┘──→  Performance tables ────────→  league_standing docs
                                                               scorer_ranking docs
                                                               article docs

                                                    384-dim embedding per doc
                                                    ivfflat index (50 lists)
```

### 4.3 Expected Output

| Output Type | Format | Consumer |
|------------|--------|----------|
| RAG chat answers | JSON `{answer, sources[], model, latency_ms}` | Fan (B2C) |
| Streaming answers | SSE stream (token-by-token) | Fan (B2C) |
| Match listings | JSON array of match objects | Fan (B2C) |
| Team/Player profiles | JSON with nested season stats | Fan (B2C) |
| Semantic search results | JSON `{results[], query_time_ms}` | Fan (B2C) |
| Fan predictions | Stored; no ML predictions returned | Fan (B2C) |
| Trend snapshots | JSON with entity buzz/query volume | B2B (API-key) |
| Fan segments | JSON with criteria, user_count, top_teams | B2B (API-key) |

---

## 5. Scan Results

### 5.1 Model Architecture Definitions

| Location | Finding |
|----------|---------|
| `agents/agent_4_document.py:53-56` | `SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")` — pre-trained, inference only |
| `agents/agent_5_api.py:975-976` | Same model loaded at API startup for query embedding |
| `agents/agent_5_api.py:86-104` | Pydantic models (`ChatReq`, `ChatResp`, `PredictionReq`) — data validation, not ML |
| **No custom architectures found** | Zero `nn.Module` subclasses, zero training loops |

### 5.2 Data Ingestion Pipeline

| Agent | File | Lines | Sources | Output Tables |
|-------|------|-------|---------|---------------|
| 1 (Structure) | `agent_1_structure.py` | 533 | StatsBomb > FD.org > FBref > API-Football | competitions, seasons, teams, players, team_seasons |
| 2 (Match) | `agent_2_match.py` + `collectors/` | 115 + 1,170 | StatsBomb, FD.org, Understat, API-Football | matches, lineups, match_events, player/team stats |
| 3 (Narrative) | `agent_3_narrative.py` | 351 | Transfermarkt, RSS feeds | transfers, injuries, articles |
| 4 (Document) | `agent_4_document.py` + `doc_generators.py` | 227 + 812 | All upstream tables | documents (with 384-dim embeddings) |
| 5 (API) | `agent_5_api.py` | 1,000 | documents + raw tables + LLM APIs | REST responses, chat messages, fan events |

### 5.3 Feature Engineering Logic

There is **no traditional feature engineering** (no feature vectors, no normalization pipelines, no train/test splits). Instead:

| Process | Location | Description |
|---------|----------|-------------|
| **Document generation** | `doc_generators.py` | Converts structured DB rows into natural language text (7 document types) |
| **Embedding** | `agent_4_document.py:59-90` | Batch-encodes document text into 384-dim vectors using SentenceTransformer |
| **Korean→English translation** | `agent_5_api.py:130-210` | Hardcoded dictionary maps (선수명/팀명/축구용어 → English equivalents) |
| **Hybrid search ranking** | `agent_5_api.py:560-590` | Merges entity direct-fetch (sim=1.0) + vector search + keyword search, sorts by similarity score |
| **Entity extraction** | `agent_5_api.py:440-550` | Pattern-matching NER to identify player/team names in Korean queries |

### 5.4 Supabase Usage Points

| File | Usage | Tables Touched |
|------|-------|----------------|
| `shared_config.py` | Client init, upsert, insert, select, RPC, status tracking | agent_status, fan_events |
| `agent_1_structure.py` | Batch upsert structure data | competitions, seasons, teams, players, team_seasons |
| `agent_2_match.py` + collectors | Batch upsert match/performance data | matches, lineups, match_events, *_stats |
| `agent_3_narrative.py` | Batch upsert narrative data | transfers, injuries, articles |
| `agent_4_document.py` | Read all tables, write embeddings | documents (pgvector) |
| `agent_5_api.py` | Read for RAG, write chat/fan data, B2B queries | All 31 tables (read/write varies) |
| `frontend/lib/supabase.ts` | Client-side auth | users (via Supabase Auth) |

### 5.5 Config Files

| File | Purpose |
|------|---------|
| `.env` | API keys (SUPABASE_URL, SUPABASE_SERVICE_KEY, GOOGLE_API_KEY, DEEPSEEK_API_KEY, FOOTBALL_DATA_TOKEN, API_FOOTBALL_KEY) |
| `requirements.txt` | 32 Python packages (35 lines) |
| `frontend/package.json` | 7 direct Node.js dependencies |
| `frontend/tsconfig.json` | TypeScript strict mode, ESNext target |
| `frontend/next.config.ts` | Webpack, asset optimization |
| `.claude/settings.local.json` | Agent Teams configuration (75 lines) |
| `supabase/schema.sql` | Full DB schema (749 lines, 31 tables) |

### 5.6 Environment Variables

| Variable | Required | Used By | Purpose |
|----------|----------|---------|---------|
| `SUPABASE_URL` | Yes | All agents | Supabase project URL |
| `SUPABASE_SERVICE_KEY` | Yes | All agents | Server-side DB access (bypasses RLS) |
| `GOOGLE_API_KEY` | Yes | Agent 5 | Gemini 2.0 Flash LLM generation |
| `DEEPSEEK_API_KEY` | Optional | Agent 5 | DeepSeek V3.2 fallback LLM |
| `FOOTBALL_DATA_TOKEN` | Yes | Agent 1, 2 | football-data.org API auth |
| `API_FOOTBALL_KEY` | Yes | K-League collectors | API-Football (K리그 data) |
| `APP_ENV` | Optional | Config | local/staging/prod |
| `CORS_ORIGINS` | Optional | Agent 5 | Allowed CORS origins |
| `NEXT_PUBLIC_API_URL` | Optional | Frontend | API base URL |

---

## 6. Gaps in Implementation

### 6.1 Critical Gaps

| Gap | Severity | Evidence | Impact |
|-----|----------|----------|--------|
| **team_season_stats has 0 rows** | High | `evaluation_result.json` → `"team_stats": 0` | Team profile documents lack standings data; B2B trends incomplete |
| **All RAG queries use "fallback" model** | High | All 5 evaluation queries show `"model": "fallback"` with 0 sources | Gemini/DeepSeek LLM calls are failing; answers come from web search fallback only |
| **RAG returns 0 source documents** | High | All evaluations show `"sources": 0` | Vector search may not be finding relevant documents despite 350 docs existing |
| **/predictions endpoint returns 500** | Medium | Smoke test: `"status": 500` | Fan prediction feature is broken |
| **No automated tests** | Medium | No `tests/` or `__tests__/` directory found | No regression safety net |
| **scikit-learn imported but unused** | Low | In `requirements.txt` but zero imports in code | Dead dependency |

### 6.2 Data Completeness Gaps

| Table | Expected | Observed | Gap |
|-------|----------|----------|-----|
| teams | Hundreds (5 leagues + K리그) | 32 | Only ~32 teams collected (1-2 leagues?) |
| matches | Thousands | 350 | Limited match history |
| match_events | Proportional | 297,832 | Rich but only for collected matches |
| documents | Proportional to data | 350 | 1:1 with matches, but missing team/player docs? |
| team_season_stats | ≥32 (one per team/season) | **0** | Standings collection failed or never ran |
| player_season_stats | Hundreds | Unknown | Not in evaluation snapshot |

### 6.3 Architectural Gaps

| Gap | Description |
|-----|-------------|
| **No fine-tuning pipeline** | No ability to fine-tune embedding model on football-domain data (would improve retrieval quality) |
| **Hardcoded Korean translation** | Entity maps are static dictionaries (~50 entries); doesn't scale to all players/teams |
| **No caching layer** | Every query re-embeds and re-searches; no Redis/in-memory cache for frequent queries |
| **No evaluation framework** | Evaluation is a one-off JSON dump, not a repeatable benchmark suite |
| **No data freshness monitoring** | No alerts when data collection fails or goes stale |
| **agent_5_api.py exceeds 500-line limit** | 1,000 lines; violates project's own coding standard |

---

## 7. Questions That Must Be Clarified Before Data Audit

### 7.1 Data Pipeline Questions

1. **Why does `team_season_stats` have 0 rows?** Was `collect_standings_footballdata()` never executed, or did it fail silently? This is the most critical data gap.

2. **What is the actual coverage of the 350 documents?** How many are match_reports vs team_profiles vs player_profiles? Are some document types completely empty?

3. **Why do all RAG evaluations show `"model": "fallback"` and 0 sources?** Is the Gemini API key valid? Is pgvector returning results? The entire RAG pipeline may be non-functional beyond web search fallback.

4. **Which leagues/seasons are actually populated?** The 32 teams and 350 matches — are these all from one competition (e.g., StatsBomb open data for one World Cup)? Or spread across 5 leagues?

5. **Is the K-League data actually present?** API-Football has a free-tier limit of 100 req/day. Was the K-League collection ever completed?

### 7.2 Architecture Questions

6. **Is there an intent to build custom ML models?** The requirements include `scikit-learn` and `torch` (via sentence-transformers). Is there a roadmap for training prediction models, or is this purely a RAG wrapper?

7. **What is the target RAG quality score?** Current average is 77.2/100. What threshold defines "production-ready"?

8. **Should the embedding model be fine-tuned on football domain data?** The current `paraphrase-multilingual-MiniLM-L12-v2` is a general-purpose model. Domain-specific fine-tuning could significantly improve retrieval accuracy.

9. **What is the expected data refresh cadence?** `daily_crawl.py` exists but only runs 3 football-data.org collectors. Should all agents run daily? Weekly?

### 7.3 Product Questions

10. **What does the `/predictions` endpoint actually need?** Is it purely a fan opinion store, or should it eventually include ML-based match outcome predictions?

11. **How should B2B trend_snapshots be populated?** The `generate_trend_snapshot` RPC function exists, but it depends on `fan_events` data. Is there enough user traffic to generate meaningful trends?

12. **Is the Korean→English translation dictionary sufficient?** Currently ~50 entries. What is the plan for scaling to full player/team coverage across 5 leagues + K리그?

### 7.4 Quality & Compliance Questions

13. **Why are there no automated tests?** The CLAUDE.md specifies 80% test coverage as a quality target. Is a test suite planned?

14. **Has the `.env` key rotation been completed?** CLAUDE.md notes "실제 키가 커밋된 이력 있음. 키 로테이션 필요."

15. **Is the AiDisclosure component sufficient for 인공지능기본법 compliance?** The component exists in the frontend but the disclosure text and placement need legal review.

---

## 8. Summary

| Dimension | Finding |
|-----------|---------|
| **Project Type** | RAG-based Football Q&A SaaS (B2C2C) |
| **AI Approach** | Smart Wrapper — pre-trained embeddings + LLM API calls, zero custom training |
| **Embedding Model** | `paraphrase-multilingual-MiniLM-L12-v2` (384-dim, multilingual, inference only) |
| **LLM** | Gemini 2.0 Flash (primary) / DeepSeek V3.2 (fallback) via OpenAI SDK |
| **Database** | Supabase PostgreSQL + pgvector (31 tables, RLS policies, 2 RPC functions) |
| **Data Sources** | 6+ sources: StatsBomb, football-data.org, FBref, Understat, Transfermarkt, API-Football, RSS |
| **Codebase Size** | ~11,000 lines active code (6K Python + 3.6K TypeScript + 1.2K SQL) |
| **Pipeline** | 5-agent sequential pipeline with IPC via JSON files + Supabase agent_status |
| **Current State** | Core RAG serving works but in degraded mode (fallback model, 0 sources returned) |
| **Critical Blockers** | team_season_stats empty, LLM generation failing to primary model, /predictions 500 error |
| **Missing** | Automated tests, evaluation framework, caching layer, data freshness monitoring |

---

*This report is a read-only analysis. No code was modified.*
