-- ================================================================
-- 011_mvp_rls.sql
-- La Paz Web MVP — 신규 테이블 RLS 정책
-- 기준: MVP_SPEC_v1.md §4.5 (보안)
-- 의존성: 010_mvp_tables.sql
-- ================================================================

-- ============================================
-- 1. transfer_rumors — 공개 읽기, service_role 쓰기
-- ============================================
alter table transfer_rumors enable row level security;

-- 모든 사용자(anon/authenticated) 읽기 가능
create policy "transfer_rumors_public_read" on transfer_rumors
  for select using (true);

-- 쓰기는 service_role만 (Edge Function에서 service_role key 사용)
create policy "transfer_rumors_service_write" on transfer_rumors
  for insert with check (false);

create policy "transfer_rumors_service_update" on transfer_rumors
  for update using (false);

create policy "transfer_rumors_service_delete" on transfer_rumors
  for delete using (false);

-- ============================================
-- 2. rumor_sources — 공개 읽기, service_role 쓰기
-- ============================================
alter table rumor_sources enable row level security;

create policy "rumor_sources_public_read" on rumor_sources
  for select using (true);

create policy "rumor_sources_service_write" on rumor_sources
  for insert with check (false);

create policy "rumor_sources_service_update" on rumor_sources
  for update using (false);

create policy "rumor_sources_service_delete" on rumor_sources
  for delete using (false);

-- ============================================
-- 3. simulations — 자기 데이터 읽기, service_role 쓰기, 비로그인 읽기 전용
-- ============================================
alter table simulations enable row level security;

-- 로그인 사용자: 자기 시뮬레이션만 읽기
create policy "simulations_owner_read" on simulations
  for select using (
    auth.uid() = user_id
  );

-- 비로그인 사용자 (user_id IS NULL): 누구나 읽기 가능
create policy "simulations_anon_read" on simulations
  for select using (
    user_id is null
  );

-- 쓰기는 service_role만 (Edge Function에서 service_role key 사용)
create policy "simulations_service_write" on simulations
  for insert with check (false);

create policy "simulations_service_update" on simulations
  for update using (false);

-- ============================================
-- 4. fan_predictions — 기존 정책 유지 + ai_prediction 공개 읽기
-- ============================================
-- 기존 RLS는 이미 활성화됨 (schema.sql J-7)
-- 기존 정책 "fan_predictions_self"는 auth.uid() = user_id
--
-- ai_prediction 컬럼은 테이블 레벨 RLS에 포함되므로,
-- 공개 읽기 정책 추가 (ai_prediction이 있는 행만)
create policy "fan_predictions_ai_public_read" on fan_predictions
  for select using (
    ai_prediction is not null
  );
