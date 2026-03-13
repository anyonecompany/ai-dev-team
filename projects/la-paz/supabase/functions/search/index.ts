// ================================================================
// La Paz — Edge Function: search
// Hybrid semantic + keyword search (API_CONTRACT.md §2)
// ================================================================

import { serve } from "https://deno.land/std@0.208.0/http/server.ts";
import { getSupabaseClient, getUserFromRequest, getClientIp } from "../_shared/supabase.ts";
import { handleCors, corsHeaders } from "../_shared/cors.ts";
import { SearchRequestSchema, validateRequest } from "../_shared/validate.ts";
import { checkRateLimit, logFanEvent } from "../_shared/rate-limit.ts";
import { getErrorMessage } from "../_shared/ai-client.ts";
import type { SearchResponse, SearchResult } from "../_shared/types.ts";

// 한→영 엔티티 매핑 (간단한 dictionary)
const ENTITY_MAP: Record<string, string> = {
  "손흥민": "Son Heung-min",
  "이강인": "Lee Kang-in",
  "김민재": "Kim Min-jae",
  "황희찬": "Hwang Hee-chan",
  "조규성": "Cho Gyu-sung",
  "정우영": "Jeong Woo-yeong",
  "백승호": "Paik Seung-ho",
  "토트넘": "Tottenham Hotspur",
  "맨시티": "Manchester City",
  "맨유": "Manchester United",
  "리버풀": "Liverpool",
  "첼시": "Chelsea",
  "아스널": "Arsenal",
  "바르셀로나": "Barcelona",
  "레알 마드리드": "Real Madrid",
  "바이에른 뮌헨": "Bayern Munich",
  "파리 생제르맹": "Paris Saint-Germain",
  "유벤투스": "Juventus",
  "인터 밀란": "Inter Milan",
  "AC 밀란": "AC Milan",
  "나폴리": "Napoli",
  "도르트문트": "Borussia Dortmund",
  "프리미어리그": "Premier League",
  "라리가": "La Liga",
  "분데스리가": "Bundesliga",
  "세리에A": "Serie A",
  "리그앙": "Ligue 1",
};

function mapEntities(query: string): string {
  let mapped = query;
  for (const [ko, en] of Object.entries(ENTITY_MAP)) {
    if (mapped.includes(ko)) {
      mapped = mapped.replace(ko, en);
    }
  }
  return mapped;
}

serve(async (req: Request) => {
  const corsResp = handleCors(req);
  if (corsResp) return corsResp;

  if (req.method !== "POST") {
    return new Response(
      JSON.stringify({ error: { code: "INVALID_INPUT", message: "Method not allowed" } }),
      { status: 405, headers: { ...corsHeaders, "Content-Type": "application/json" } },
    );
  }

  const startTime = Date.now();
  const supabase = getSupabaseClient();
  const userId = getUserFromRequest(req);
  const clientIp = getClientIp(req);

  // Rate limit check
  const rateLimit = await checkRateLimit(supabase, userId, clientIp);
  if (!rateLimit.allowed) {
    return new Response(
      JSON.stringify({
        error: { code: "RATE_LIMITED", message: getErrorMessage("rate_limit", "ko") },
      }),
      { status: 429, headers: { ...corsHeaders, "Content-Type": "application/json" } },
    );
  }

  try {
    const body = await req.json();
    const validation = validateRequest(SearchRequestSchema, body);
    if (!validation.success) {
      return new Response(
        JSON.stringify({ error: { code: "INVALID_INPUT", message: validation.error } }),
        { status: 400, headers: { ...corsHeaders, "Content-Type": "application/json" } },
      );
    }

    const { query, limit, locale } = validation.data;

    // 한→영 엔티티 매핑
    const searchQuery = locale === "ko" ? mapEntities(query) : query;

    const results: SearchResult[] = [];

    // 1. pgvector 시맨틱 검색 — match_documents RPC
    // 임베딩 생성은 외부에서 미리 수행되어야 하므로, 여기서는 키워드 기반으로 대체
    // 실제 프로덕션에서는 임베딩 API 호출 후 match_documents RPC 사용

    // 2. 키워드 검색 (ILIKE fallback)
    const { data: keywordResults } = await supabase
      .from("documents")
      .select("id, doc_type, ref_id, title, content, metadata")
      .or(
        `title.ilike.%${searchQuery}%,content.ilike.%${searchQuery}%`,
      )
      .order("created_at", { ascending: false })
      .limit(limit!);

    if (keywordResults) {
      for (const doc of keywordResults) {
        // 중복 방지
        if (results.find((r) => r.doc_id === doc.id)) continue;

        const snippet = doc.content
          ? doc.content.substring(0, 300)
          : "";

        results.push({
          doc_id: doc.id,
          title: doc.title,
          snippet,
          similarity: 0.5, // 키워드 매치는 고정 유사도
          doc_type: doc.doc_type,
        });
      }
    }

    // 원본 한국어 쿼리로도 추가 검색 (locale === "ko" && 변환된 경우)
    if (searchQuery !== query) {
      const { data: koResults } = await supabase
        .from("documents")
        .select("id, doc_type, ref_id, title, content, metadata")
        .or(`title.ilike.%${query}%,content.ilike.%${query}%`)
        .order("created_at", { ascending: false })
        .limit(limit!);

      if (koResults) {
        for (const doc of koResults) {
          if (results.find((r) => r.doc_id === doc.id)) continue;
          results.push({
            doc_id: doc.id,
            title: doc.title,
            snippet: doc.content ? doc.content.substring(0, 300) : "",
            similarity: 0.4,
            doc_type: doc.doc_type,
          });
        }
      }
    }

    // 유사도 기준 정렬 + limit 적용
    results.sort((a, b) => b.similarity - a.similarity);
    const finalResults = results.slice(0, limit!);

    const response: SearchResponse = {
      results: finalResults,
      query_time_ms: Date.now() - startTime,
    };

    // Log fan event for rate limiting + analytics
    logFanEvent(supabase, {
      userId,
      eventType: "search",
      clientIp,
      payload: {
        query,
        results_count: finalResults.length,
      },
    }).catch(() => {});

    return new Response(JSON.stringify(response), {
      status: 200,
      headers: { ...corsHeaders, "Content-Type": "application/json" },
    });
  } catch (err) {
    const message = err instanceof Error ? err.message : "Internal error";
    return new Response(
      JSON.stringify({ error: { code: "INTERNAL_ERROR", message } }),
      { status: 500, headers: { ...corsHeaders, "Content-Type": "application/json" } },
    );
  }
});
