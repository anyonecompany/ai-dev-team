-- ================================================================
-- La Paz — Football AI B2C2C Platform
-- Supabase Schema v2.0 (PostgreSQL + pgvector)
-- 5-Domain: Structure, Match, Performance, Narrative, Tactics
-- ================================================================

-- 0) Extensions
create extension if not exists "uuid-ossp";
create extension if not exists vector;

-- ================================================================
-- A. STRUCTURE DOMAIN (8 tables)
-- ================================================================

create table if not exists competitions (
  id            uuid primary key default uuid_generate_v4(),
  source_id     text not null,
  name          text not null,
  country       text,
  source        text not null,                       -- fbref | transfermarkt | statsbomb
  meta          jsonb default '{}',
  created_at    timestamptz default now(),
  unique (source, source_id)
);

create table if not exists seasons (
  id            uuid primary key default uuid_generate_v4(),
  competition_id uuid references competitions(id),
  year          text not null,                       -- e.g. "2024-2025"
  name          text,
  start_date    date,
  end_date      date,
  is_current    boolean default false,
  meta          jsonb default '{}',
  created_at    timestamptz default now(),
  unique (competition_id, year)
);

create table if not exists teams (
  id            uuid primary key default uuid_generate_v4(),
  name          text not null,
  canonical     text not null,                       -- 정규화된 팀명
  aliases       jsonb default '[]',                  -- 다른 이름들
  country       text,
  founded_year  int,
  stadium       text,
  crest_url     text,
  source        text,
  meta          jsonb default '{}',
  created_at    timestamptz default now(),
  unique (canonical)
);

create table if not exists players (
  id            uuid primary key default uuid_generate_v4(),
  name          text not null,
  full_name     text,
  nationality   text,
  birth_date    date,
  position      text,
  height_cm     real,
  weight_kg     real,
  preferred_foot text,
  source        text,
  meta          jsonb default '{}',
  created_at    timestamptz default now()
);

create table if not exists managers (
  id            uuid primary key default uuid_generate_v4(),
  name          text not null,
  nationality   text,
  birth_date    date,
  source        text,
  meta          jsonb default '{}',
  created_at    timestamptz default now()
);

create table if not exists team_seasons (
  id            uuid primary key default uuid_generate_v4(),
  team_id       uuid references teams(id),
  season_id     uuid references seasons(id),
  competition_id uuid references competitions(id),
  meta          jsonb default '{}',
  created_at    timestamptz default now(),
  unique (team_id, season_id, competition_id)
);

create table if not exists player_contracts (
  id            uuid primary key default uuid_generate_v4(),
  player_id     uuid references players(id),
  team_id       uuid references teams(id),
  start_date    date,
  end_date      date,
  jersey_number int,
  is_active     boolean default true,
  source        text,
  meta          jsonb default '{}',
  created_at    timestamptz default now()
);

create table if not exists manager_tenures (
  id            uuid primary key default uuid_generate_v4(),
  manager_id    uuid references managers(id),
  team_id       uuid references teams(id),
  start_date    date,
  end_date      date,
  is_active     boolean default true,
  source        text,
  meta          jsonb default '{}',
  created_at    timestamptz default now()
);

-- ================================================================
-- B. MATCH DOMAIN (3 tables)
-- ================================================================

create table if not exists matches (
  id            uuid primary key default uuid_generate_v4(),
  source_id     text not null,
  competition_id uuid references competitions(id),
  season_id     uuid references seasons(id),
  match_date    date,
  matchday      int,
  home_team_id  uuid references teams(id),
  away_team_id  uuid references teams(id),
  home_score    int,
  away_score    int,
  stadium       text,
  referee       text,
  attendance    int,
  source        text not null,
  meta          jsonb default '{}',
  created_at    timestamptz default now(),
  unique (source, source_id)
);

create table if not exists lineups (
  id            uuid primary key default uuid_generate_v4(),
  match_id      uuid references matches(id) on delete cascade,
  team_id       uuid references teams(id),
  player_id     uuid references players(id),
  position      text,
  is_starter    boolean default true,
  jersey_number int,
  minutes_played int default 0,
  meta          jsonb default '{}',
  created_at    timestamptz default now()
);

create table if not exists match_events (
  id            uuid primary key default uuid_generate_v4(),
  match_id      uuid references matches(id) on delete cascade,
  source_id     text,
  minute        int,
  second        int,
  type          text not null,                       -- pass, shot, tackle, goal, card ...
  player_name   text,
  team_name     text,
  outcome       text,
  x_start       real,
  y_start       real,
  x_end         real,
  y_end         real,
  meta          jsonb default '{}',
  created_at    timestamptz default now()
);

-- ================================================================
-- C. PERFORMANCE DOMAIN (4 tables)
-- ================================================================

create table if not exists player_match_stats (
  id            uuid primary key default uuid_generate_v4(),
  player_id     uuid references players(id),
  match_id      uuid references matches(id),
  team_id       uuid references teams(id),
  minutes       int default 0,
  goals         int default 0,
  assists       int default 0,
  shots         int default 0,
  shots_on_target int default 0,
  passes        int default 0,
  passes_completed int default 0,
  tackles       int default 0,
  interceptions int default 0,
  fouls         int default 0,
  cards_yellow  int default 0,
  cards_red     int default 0,
  xg            real,
  xa            real,
  source        text,
  meta          jsonb default '{}',
  created_at    timestamptz default now()
);

create table if not exists player_season_stats (
  id            uuid primary key default uuid_generate_v4(),
  player_id     uuid references players(id),
  season_id     uuid references seasons(id),
  team_id       uuid references teams(id),
  competition_id uuid references competitions(id),
  appearances   int default 0,
  minutes       int default 0,
  goals         int default 0,
  assists       int default 0,
  xg            real,
  xa            real,
  source        text,
  meta          jsonb default '{}',
  created_at    timestamptz default now(),
  unique (player_id, season_id, team_id, competition_id)
);

create table if not exists team_match_stats (
  id            uuid primary key default uuid_generate_v4(),
  team_id       uuid references teams(id),
  match_id      uuid references matches(id),
  possession    real,
  shots         int default 0,
  shots_on_target int default 0,
  passes        int default 0,
  pass_accuracy real,
  corners       int default 0,
  fouls         int default 0,
  xg            real,
  source        text,
  meta          jsonb default '{}',
  created_at    timestamptz default now()
);

create table if not exists team_season_stats (
  id            uuid primary key default uuid_generate_v4(),
  team_id       uuid references teams(id),
  season_id     uuid references seasons(id),
  competition_id uuid references competitions(id),
  position      int,
  played        int default 0,
  won           int default 0,
  draw          int default 0,
  lost          int default 0,
  goals_for     int default 0,
  goals_against int default 0,
  goal_diff     int default 0,
  points        int default 0,
  xg_for        real,
  xg_against    real,
  source        text,
  meta          jsonb default '{}',
  created_at    timestamptz default now(),
  unique (team_id, season_id, competition_id)
);

-- ================================================================
-- D. NARRATIVE DOMAIN (3 tables)
-- ================================================================

create table if not exists transfers (
  id            uuid primary key default uuid_generate_v4(),
  player_id     uuid references players(id),
  from_team_id  uuid references teams(id),
  to_team_id    uuid references teams(id),
  transfer_date date,
  fee           real,
  fee_currency  text default 'EUR',
  transfer_type text,                                -- permanent, loan, free, loan_return
  season        text,
  source        text,
  meta          jsonb default '{}',
  created_at    timestamptz default now()
);

create table if not exists injuries (
  id            uuid primary key default uuid_generate_v4(),
  player_id     uuid references players(id),
  team_id       uuid references teams(id),
  injury_type   text,
  start_date    date,
  end_date      date,
  games_missed  int default 0,
  source        text,
  meta          jsonb default '{}',
  created_at    timestamptz default now()
);

create table if not exists articles (
  id            uuid primary key default uuid_generate_v4(),
  source_name   text not null,                       -- bbc, guardian, espn, reddit
  title         text not null,
  url           text unique,
  summary       text,
  content       text,
  published_at  timestamptz,
  language      text default 'en',
  tags          jsonb default '[]',
  meta          jsonb default '{}',
  created_at    timestamptz default now()
);

create index if not exists idx_articles_published on articles(published_at desc);

-- ================================================================
-- E. TACTICS DOMAIN (1 table)
-- ================================================================

create table if not exists formations (
  id            uuid primary key default uuid_generate_v4(),
  match_id      uuid references matches(id) on delete cascade,
  team_id       uuid references teams(id),
  formation     text not null,                       -- e.g. "4-3-3", "3-5-2"
  period        text default 'full',                 -- full, first_half, second_half
  players_positions jsonb default '{}',              -- {player_name: {x, y, role}}
  meta          jsonb default '{}',
  created_at    timestamptz default now()
);

-- ================================================================
-- F. RAG — DOCUMENTS + pgvector (1 table + 1 RPC)
-- ================================================================

create table if not exists documents (
  id            uuid primary key default uuid_generate_v4(),
  doc_type      text not null,                       -- match_report | team_profile | player_profile | transfer_news | tactical_analysis | league_standing
  ref_id        text,                                -- 원본 FK (matches.id 등)
  title         text not null,
  content       text not null,
  embedding     vector(384),                         -- all-MiniLM-L6-v2
  metadata      jsonb default '{}',
  created_at    timestamptz default now()
);

create index if not exists idx_documents_embedding
  on documents using ivfflat (embedding vector_cosine_ops) with (lists = 50);

create index if not exists idx_documents_type on documents(doc_type);

-- 벡터 검색 함수
create or replace function match_documents(
  query_embedding vector(384),
  match_count     int default 5,
  filter_type     text default null
)
returns table (
  id        uuid,
  doc_type  text,
  ref_id    text,
  title     text,
  content   text,
  metadata  jsonb,
  similarity float
)
language plpgsql
set search_path = public
as $$
begin
  return query
    select
      d.id,
      d.doc_type,
      d.ref_id,
      d.title,
      d.content,
      d.metadata,
      1 - (d.embedding <=> query_embedding) as similarity
    from documents d
    where (filter_type is null or d.doc_type = filter_type)
    order by d.embedding <=> query_embedding
    limit match_count;
end;
$$;

-- ================================================================
-- G. FAN ENGAGEMENT — B2C (5 tables)
-- ================================================================

create table if not exists users (
  id            uuid primary key default uuid_generate_v4(),
  email         text unique,
  display_name  text,
  avatar_url    text,
  favorite_team uuid references teams(id),
  country       text,
  locale        text default 'ko',
  meta          jsonb default '{}',
  created_at    timestamptz default now()
);

create table if not exists chat_sessions (
  id            uuid primary key default uuid_generate_v4(),
  user_id       uuid references users(id),
  title         text,
  model_used    text default 'deepseek-chat',
  message_count int default 0,
  created_at    timestamptz default now(),
  updated_at    timestamptz default now()
);

create table if not exists chat_messages (
  id            uuid primary key default uuid_generate_v4(),
  session_id    uuid references chat_sessions(id) on delete cascade,
  role          text not null check (role in ('system', 'user', 'assistant')),
  content       text not null,
  tokens_used   int default 0,
  latency_ms    real,
  model         text,
  created_at    timestamptz default now()
);

create table if not exists fan_events (
  id            uuid primary key default uuid_generate_v4(),
  user_id       uuid references users(id),
  session_id    uuid,
  event_type    text not null,                       -- chat, search, page_view, prediction, share
  entity_type   text,                                -- team, player, match, competition
  entity_id     text,
  payload       jsonb default '{}',
  created_at    timestamptz default now()
);

create index if not exists idx_fan_events_type on fan_events(event_type);
create index if not exists idx_fan_events_created on fan_events(created_at);

create table if not exists fan_predictions (
  id            uuid primary key default uuid_generate_v4(),
  user_id       uuid references users(id),
  match_id      uuid references matches(id),
  predicted_home int,
  predicted_away int,
  confidence     real,
  is_correct     boolean,
  created_at    timestamptz default now()
);

-- ================================================================
-- H. B2B DATA PRODUCTS (4 tables + 1 RPC)
-- ================================================================

create table if not exists trend_snapshots (
  id            uuid primary key default uuid_generate_v4(),
  snapshot_date date not null,
  metric_type   text not null,                       -- entity_buzz, topic_trend, query_volume
  entity_type   text,
  entity_id     text,
  entity_name   text,
  value         real not null,
  sample_size   int default 0,
  breakdown     jsonb default '{}',
  created_at    timestamptz default now()
);

create index if not exists idx_trend_date on trend_snapshots(snapshot_date);

create table if not exists fan_segments (
  id            uuid primary key default uuid_generate_v4(),
  segment_name  text not null,
  description   text,
  criteria      jsonb not null,
  user_count    int default 0,
  avg_sessions  real,
  top_teams     jsonb default '[]',
  top_topics    jsonb default '[]',
  updated_at    timestamptz default now(),
  created_at    timestamptz default now()
);

create table if not exists b2b_clients (
  id            uuid primary key default uuid_generate_v4(),
  company_name  text not null,
  api_key       text not null unique,
  contact_email text,
  plan          text default 'free',                 -- free | starter | enterprise
  rate_limit    int default 100,                     -- requests per day
  is_active     boolean default true,
  meta          jsonb default '{}',
  created_at    timestamptz default now()
);

create table if not exists b2b_api_logs (
  id            uuid primary key default uuid_generate_v4(),
  client_id     uuid references b2b_clients(id),
  endpoint      text not null,
  method        text not null,
  status_code   int,
  latency_ms    real,
  request_meta  jsonb default '{}',
  created_at    timestamptz default now()
);

create index if not exists idx_b2b_logs_client on b2b_api_logs(client_id, created_at);

-- 트렌드 집계 함수
create or replace function generate_trend_snapshot(target_date date default current_date)
returns int
language plpgsql
set search_path = public
as $$
declare
  inserted int := 0;
begin
  -- entity_buzz: 지난 24h 동안 팬 이벤트에서 가장 많이 언급된 엔티티
  insert into trend_snapshots (snapshot_date, metric_type, entity_type, entity_id, entity_name, value, sample_size)
  select
    target_date,
    'entity_buzz',
    fe.entity_type,
    fe.entity_id,
    coalesce(fe.payload->>'entity_name', fe.entity_id),
    count(*)::real,
    count(distinct fe.user_id)
  from fan_events fe
  where fe.created_at >= target_date::timestamptz
    and fe.created_at < (target_date + interval '1 day')::timestamptz
    and fe.entity_type is not null
  group by fe.entity_type, fe.entity_id, fe.payload->>'entity_name'
  having count(*) >= 2;

  get diagnostics inserted = row_count;

  -- query_volume: 시간대별 쿼리 수
  insert into trend_snapshots (snapshot_date, metric_type, entity_type, value, sample_size, breakdown)
  select
    target_date,
    'query_volume',
    'hourly',
    count(*)::real,
    count(distinct user_id),
    jsonb_object_agg(hr, cnt)
  from (
    select
      user_id,
      extract(hour from created_at)::int as hr,
      count(*) as cnt
    from fan_events
    where event_type = 'chat'
      and created_at >= target_date::timestamptz
      and created_at < (target_date + interval '1 day')::timestamptz
    group by user_id, hr
  ) sub
  group by 1, 2, 3;

  return inserted;
end;
$$;

-- ================================================================
-- I. PIPELINE MANAGEMENT (2 tables)
-- ================================================================

create table if not exists agent_status (
  agent_name    text primary key,
  status        text not null default 'idle',        -- idle | running | waiting | completed | error
  detail        text,
  started_at    timestamptz,
  completed_at  timestamptz,
  updated_at    timestamptz default now()
);

create table if not exists pipeline_runs (
  id            uuid primary key default uuid_generate_v4(),
  run_name      text,
  status        text default 'running',
  agents_config jsonb default '{}',
  stats         jsonb default '{}',
  started_at    timestamptz default now(),
  completed_at  timestamptz
);

-- ================================================================
-- J. RLS POLICIES
-- ================================================================

-- ---------------------------------------------------------------
-- J-1. STRUCTURE DOMAIN — 공개 읽기 전용 (anon/authenticated SELECT)
-- ---------------------------------------------------------------
alter table competitions enable row level security;
alter table seasons enable row level security;
alter table teams enable row level security;
alter table players enable row level security;
alter table managers enable row level security;
alter table team_seasons enable row level security;
alter table player_contracts enable row level security;
alter table manager_tenures enable row level security;

create policy "competitions_public_read" on competitions
  for select using (true);

create policy "seasons_public_read" on seasons
  for select using (true);

create policy "teams_public_read" on teams
  for select using (true);

create policy "players_public_read" on players
  for select using (true);

create policy "managers_public_read" on managers
  for select using (true);

create policy "team_seasons_public_read" on team_seasons
  for select using (true);

create policy "player_contracts_public_read" on player_contracts
  for select using (true);

create policy "manager_tenures_public_read" on manager_tenures
  for select using (true);

-- ---------------------------------------------------------------
-- J-2. MATCH DOMAIN — 공개 읽기 전용
-- ---------------------------------------------------------------
alter table matches enable row level security;
alter table lineups enable row level security;
alter table match_events enable row level security;

create policy "matches_public_read" on matches
  for select using (true);

create policy "lineups_public_read" on lineups
  for select using (true);

create policy "match_events_public_read" on match_events
  for select using (true);

-- ---------------------------------------------------------------
-- J-3. PERFORMANCE DOMAIN — 공개 읽기 전용
-- ---------------------------------------------------------------
alter table player_match_stats enable row level security;
alter table player_season_stats enable row level security;
alter table team_match_stats enable row level security;
alter table team_season_stats enable row level security;

create policy "player_match_stats_public_read" on player_match_stats
  for select using (true);

create policy "player_season_stats_public_read" on player_season_stats
  for select using (true);

create policy "team_match_stats_public_read" on team_match_stats
  for select using (true);

create policy "team_season_stats_public_read" on team_season_stats
  for select using (true);

-- ---------------------------------------------------------------
-- J-4. NARRATIVE DOMAIN — 공개 읽기 전용
-- ---------------------------------------------------------------
alter table transfers enable row level security;
alter table injuries enable row level security;
alter table articles enable row level security;

create policy "transfers_public_read" on transfers
  for select using (true);

create policy "injuries_public_read" on injuries
  for select using (true);

create policy "articles_public_read" on articles
  for select using (true);

-- ---------------------------------------------------------------
-- J-5. TACTICS DOMAIN — 공개 읽기 전용
-- ---------------------------------------------------------------
alter table formations enable row level security;

create policy "formations_public_read" on formations
  for select using (true);

-- ---------------------------------------------------------------
-- J-6. RAG DOCUMENTS — 공개 읽기 전용
-- ---------------------------------------------------------------
alter table documents enable row level security;

create policy "documents_public_read" on documents
  for select using (true);

-- ---------------------------------------------------------------
-- J-7. FAN ENGAGEMENT — 사용자별 접근 제어
-- ---------------------------------------------------------------
alter table users enable row level security;
alter table chat_sessions enable row level security;
alter table chat_messages enable row level security;
alter table fan_events enable row level security;
alter table fan_predictions enable row level security;

-- Users: 본인 데이터만 읽기/수정
create policy "users_self_read" on users
  for select using (auth.uid() = id);

create policy "users_self_update" on users
  for update using (auth.uid() = id);

-- Chat: 본인 세션만
create policy "sessions_self" on chat_sessions
  for all using (auth.uid() = user_id);

create policy "messages_self" on chat_messages
  for all using (
    session_id in (select id from chat_sessions where user_id = auth.uid())
  );

-- Fan events: 본인 것만 INSERT + 읽기
create policy "fan_events_self_read" on fan_events
  for select using (auth.uid() = user_id);

create policy "fan_events_self_insert" on fan_events
  for insert with check (auth.uid() = user_id);

-- Fan predictions: 본인 것만
create policy "fan_predictions_self" on fan_predictions
  for all using (auth.uid() = user_id);

-- ---------------------------------------------------------------
-- J-8. B2B — service_role 전용 (api_key 보호)
-- ---------------------------------------------------------------
alter table b2b_clients enable row level security;
alter table b2b_api_logs enable row level security;

-- b2b_clients: service_role만 접근 (api_key 컬럼 보호)
create policy "b2b_clients_service_only" on b2b_clients
  for all using (false);  -- service_role key는 RLS bypass

-- b2b_api_logs: service_role만 접근
create policy "b2b_logs_service_only" on b2b_api_logs
  for all using (false);  -- service_role key는 RLS bypass

-- ---------------------------------------------------------------
-- J-9. B2B DATA PRODUCTS — 공개 읽기 전용
-- ---------------------------------------------------------------
alter table trend_snapshots enable row level security;
alter table fan_segments enable row level security;

create policy "trend_snapshots_public_read" on trend_snapshots
  for select using (true);

create policy "fan_segments_public_read" on fan_segments
  for select using (true);

-- ---------------------------------------------------------------
-- J-10. PIPELINE — service_role 전용 (내부 관리)
-- ---------------------------------------------------------------
alter table agent_status enable row level security;
alter table pipeline_runs enable row level security;

-- agent_status/pipeline_runs: service_role만 접근 (파이프라인 내부)
create policy "agent_status_service_only" on agent_status
  for all using (false);  -- service_role key는 RLS bypass

create policy "pipeline_runs_service_only" on pipeline_runs
  for all using (false);  -- service_role key는 RLS bypass
