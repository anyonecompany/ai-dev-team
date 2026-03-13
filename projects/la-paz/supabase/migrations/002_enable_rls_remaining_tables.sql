-- ================================================================
-- Migration: 002_enable_rls_remaining_tables
-- Description: 기존 RLS 미적용 테이블에만 RLS 활성화 + 정책 적용
-- Date: 2026-02-19
-- Note: users, chat_sessions, chat_messages, fan_events,
--       fan_predictions, b2b_api_logs는 이미 RLS 적용됨 → 제외
-- ================================================================

BEGIN;

-- ---------------------------------------------------------------
-- 1. STRUCTURE DOMAIN — 공개 읽기 전용
-- ---------------------------------------------------------------
ALTER TABLE public.competitions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.seasons ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.teams ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.players ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.managers ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.team_seasons ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.player_contracts ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.manager_tenures ENABLE ROW LEVEL SECURITY;

DO $$ BEGIN
  CREATE POLICY "competitions_public_read" ON public.competitions FOR SELECT USING (true);
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

DO $$ BEGIN
  CREATE POLICY "seasons_public_read" ON public.seasons FOR SELECT USING (true);
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

DO $$ BEGIN
  CREATE POLICY "teams_public_read" ON public.teams FOR SELECT USING (true);
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

DO $$ BEGIN
  CREATE POLICY "players_public_read" ON public.players FOR SELECT USING (true);
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

DO $$ BEGIN
  CREATE POLICY "managers_public_read" ON public.managers FOR SELECT USING (true);
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

DO $$ BEGIN
  CREATE POLICY "team_seasons_public_read" ON public.team_seasons FOR SELECT USING (true);
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

DO $$ BEGIN
  CREATE POLICY "player_contracts_public_read" ON public.player_contracts FOR SELECT USING (true);
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

DO $$ BEGIN
  CREATE POLICY "manager_tenures_public_read" ON public.manager_tenures FOR SELECT USING (true);
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

-- ---------------------------------------------------------------
-- 2. MATCH DOMAIN — 공개 읽기 전용
-- ---------------------------------------------------------------
ALTER TABLE public.matches ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.lineups ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.match_events ENABLE ROW LEVEL SECURITY;

DO $$ BEGIN
  CREATE POLICY "matches_public_read" ON public.matches FOR SELECT USING (true);
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

DO $$ BEGIN
  CREATE POLICY "lineups_public_read" ON public.lineups FOR SELECT USING (true);
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

DO $$ BEGIN
  CREATE POLICY "match_events_public_read" ON public.match_events FOR SELECT USING (true);
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

-- ---------------------------------------------------------------
-- 3. PERFORMANCE DOMAIN — 공개 읽기 전용
-- ---------------------------------------------------------------
ALTER TABLE public.player_match_stats ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.player_season_stats ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.team_match_stats ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.team_season_stats ENABLE ROW LEVEL SECURITY;

DO $$ BEGIN
  CREATE POLICY "player_match_stats_public_read" ON public.player_match_stats FOR SELECT USING (true);
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

DO $$ BEGIN
  CREATE POLICY "player_season_stats_public_read" ON public.player_season_stats FOR SELECT USING (true);
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

DO $$ BEGIN
  CREATE POLICY "team_match_stats_public_read" ON public.team_match_stats FOR SELECT USING (true);
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

DO $$ BEGIN
  CREATE POLICY "team_season_stats_public_read" ON public.team_season_stats FOR SELECT USING (true);
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

-- ---------------------------------------------------------------
-- 4. NARRATIVE DOMAIN — 공개 읽기 전용
-- ---------------------------------------------------------------
ALTER TABLE public.transfers ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.injuries ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.articles ENABLE ROW LEVEL SECURITY;

DO $$ BEGIN
  CREATE POLICY "transfers_public_read" ON public.transfers FOR SELECT USING (true);
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

DO $$ BEGIN
  CREATE POLICY "injuries_public_read" ON public.injuries FOR SELECT USING (true);
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

DO $$ BEGIN
  CREATE POLICY "articles_public_read" ON public.articles FOR SELECT USING (true);
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

-- ---------------------------------------------------------------
-- 5. TACTICS — 공개 읽기 전용
-- ---------------------------------------------------------------
ALTER TABLE public.formations ENABLE ROW LEVEL SECURITY;

DO $$ BEGIN
  CREATE POLICY "formations_public_read" ON public.formations FOR SELECT USING (true);
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

-- ---------------------------------------------------------------
-- 6. RAG DOCUMENTS — 공개 읽기 전용
-- ---------------------------------------------------------------
ALTER TABLE public.documents ENABLE ROW LEVEL SECURITY;

DO $$ BEGIN
  CREATE POLICY "documents_public_read" ON public.documents FOR SELECT USING (true);
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

-- ---------------------------------------------------------------
-- 7. B2B CLIENTS — service_role 전용 (api_key 보호!)
-- ---------------------------------------------------------------
ALTER TABLE public.b2b_clients ENABLE ROW LEVEL SECURITY;

DO $$ BEGIN
  CREATE POLICY "b2b_clients_service_only" ON public.b2b_clients FOR ALL USING (false);
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

-- ---------------------------------------------------------------
-- 8. B2B DATA PRODUCTS — 공개 읽기 전용
-- ---------------------------------------------------------------
ALTER TABLE public.trend_snapshots ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.fan_segments ENABLE ROW LEVEL SECURITY;

DO $$ BEGIN
  CREATE POLICY "trend_snapshots_public_read" ON public.trend_snapshots FOR SELECT USING (true);
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

DO $$ BEGIN
  CREATE POLICY "fan_segments_public_read" ON public.fan_segments FOR SELECT USING (true);
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

-- ---------------------------------------------------------------
-- 9. PIPELINE — service_role 전용
-- ---------------------------------------------------------------
ALTER TABLE public.agent_status ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.pipeline_runs ENABLE ROW LEVEL SECURITY;

DO $$ BEGIN
  CREATE POLICY "agent_status_service_only" ON public.agent_status FOR ALL USING (false);
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

DO $$ BEGIN
  CREATE POLICY "pipeline_runs_service_only" ON public.pipeline_runs FOR ALL USING (false);
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

-- ---------------------------------------------------------------
-- 10. team_stats, player_stats (CSV에서 발견된 추가 테이블)
-- ---------------------------------------------------------------
DO $$ BEGIN
  ALTER TABLE public.team_stats ENABLE ROW LEVEL SECURITY;
  CREATE POLICY "team_stats_public_read" ON public.team_stats FOR SELECT USING (true);
EXCEPTION WHEN undefined_table THEN NULL;
         WHEN duplicate_object THEN NULL;
END $$;

DO $$ BEGIN
  ALTER TABLE public.player_stats ENABLE ROW LEVEL SECURITY;
  CREATE POLICY "player_stats_public_read" ON public.player_stats FOR SELECT USING (true);
EXCEPTION WHEN undefined_table THEN NULL;
         WHEN duplicate_object THEN NULL;
END $$;

COMMIT;
