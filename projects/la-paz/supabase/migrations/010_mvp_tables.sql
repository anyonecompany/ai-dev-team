-- ================================================================
-- 010_mvp_tables.sql
-- La Paz Web MVP — 신규 테이블 3개 + 기존 테이블 확장 1개
-- 기준: MVP_SPEC_v1.md §3.1 (F1), §3.4 (F4)
-- ================================================================

-- ---------- 1. transfer_rumors ----------
create table if not exists transfer_rumors (
  id                uuid primary key default uuid_generate_v4(),
  player_id         uuid not null references players(id),
  from_team_id      uuid references teams(id),
  to_team_id        uuid references teams(id),
  confidence_score  int not null default 0 check (confidence_score >= 0 and confidence_score <= 100),
  status            text not null default 'rumor' check (status in ('rumor', 'confirmed', 'denied')),
  first_reported_at timestamptz not null default now(),
  last_updated_at   timestamptz not null default now(),
  meta              jsonb default '{}',
  created_at        timestamptz default now()
);

comment on table transfer_rumors is '이적 루머 엔티티 — F1 이적 루머 허브';

-- 인덱스: 시간순 피드, 선수별 필터, 팀별 필터, 상태 필터
create index if not exists idx_transfer_rumors_reported
  on transfer_rumors (first_reported_at desc);

create index if not exists idx_transfer_rumors_player
  on transfer_rumors (player_id);

create index if not exists idx_transfer_rumors_to_team
  on transfer_rumors (to_team_id);

create index if not exists idx_transfer_rumors_from_team
  on transfer_rumors (from_team_id);

create index if not exists idx_transfer_rumors_status
  on transfer_rumors (status);

-- ---------- 2. rumor_sources ----------
create table if not exists rumor_sources (
  id               uuid primary key default uuid_generate_v4(),
  rumor_id         uuid not null references transfer_rumors(id) on delete cascade,
  source_name      text not null,
  source_url       text,
  journalist       text,
  reliability_tier int not null default 3 check (reliability_tier >= 1 and reliability_tier <= 5),
  published_at     timestamptz,
  created_at       timestamptz default now()
);

comment on table rumor_sources is '루머별 소스 추적 — F1 이적 루머 허브';

create index if not exists idx_rumor_sources_rumor
  on rumor_sources (rumor_id);

create index if not exists idx_rumor_sources_reliability
  on rumor_sources (reliability_tier);

-- ---------- 3. simulations ----------
create table if not exists simulations (
  id          uuid primary key default uuid_generate_v4(),
  user_id     uuid references users(id),
  sim_type    text not null check (sim_type in ('transfer', 'match')),
  params      jsonb not null default '{}',
  result      jsonb default '{}',
  model_used  text not null default 'claude',
  latency_ms  int,
  created_at  timestamptz default now()
);

comment on table simulations is '시뮬레이션 결과 저장 — F4 시뮬레이션';

create index if not exists idx_simulations_user
  on simulations (user_id);

create index if not exists idx_simulations_type
  on simulations (sim_type);

create index if not exists idx_simulations_created
  on simulations (created_at desc);

-- ---------- 4. fan_predictions 확장 ----------
-- ai_prediction jsonb 컬럼 추가 (AI 예측 결과와 팬 예측 비교용)
alter table fan_predictions
  add column if not exists ai_prediction jsonb;

comment on column fan_predictions.ai_prediction is 'AI 경기 예측 결과 (predicted_score, win_probability 등)';
