-- ================================================================
-- Migration: 003_fix_search_path_warnings
-- Description: Function Search Path Mutable 경고 수정
-- Date: 2026-02-19
-- Fixes: generate_trend_snapshot, match_documents search_path 미설정
-- ================================================================

-- 1. match_documents — 벡터 검색 함수
ALTER FUNCTION public.match_documents(vector(384), int, text)
  SET search_path = public;

-- 2. generate_trend_snapshot — 트렌드 집계 함수
ALTER FUNCTION public.generate_trend_snapshot(date)
  SET search_path = public;
