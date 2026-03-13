// ================================================================
// La Paz — Edge Function: parse-rumors
// Articles → Transfer Rumors Entity Extraction (API_CONTRACT.md §3)
// ================================================================

import { serve } from "https://deno.land/std@0.208.0/http/server.ts";
import { getSupabaseClient } from "../_shared/supabase.ts";
import { handleCors, corsHeaders } from "../_shared/cors.ts";
import { ParseRumorsRequestSchema, validateRequest } from "../_shared/validate.ts";
import { callAI } from "../_shared/ai-client.ts";
import type { ParsedRumor, ParseRumorsResponse } from "../_shared/types.ts";

// --- Prompt (AI_PROMPTS.md §4) ---

const PARSE_RUMORS_SYSTEM_PROMPT = `You are a football transfer news analyst for La Paz platform.

## TASK
Extract transfer rumor entities from the provided article text.
Determine if the article contains a transfer rumor and extract structured data.

## STRICT RULES
1. Only extract information EXPLICITLY stated in the article text.
2. Do NOT infer transfers that are not mentioned.
3. canonical_name must be the most commonly used English name (e.g., "Son Heung-min", not "손흥민" or "Sonny").
4. confidence_score reflects how certain the article is about the transfer (not your certainty about the extraction).
5. source_reliability is based on the article's source (1=tabloid/social, 2=local media, 3=national media, 4=tier 1 journalist, 5=official announcement).
6. If the article is NOT about a transfer, set is_transfer_rumor to false and all entity fields to null.`;

const PARSED_RUMOR_SCHEMA = {
  type: "object" as const,
  properties: {
    is_transfer_rumor: { type: "boolean" },
    player: {
      type: ["object", "null"],
      properties: {
        name: { type: "string" },
        canonical_name: { type: "string" },
      },
      required: ["name", "canonical_name"],
    },
    from_team: {
      type: ["object", "null"],
      properties: {
        name: { type: "string" },
        canonical_name: { type: "string" },
      },
      required: ["name", "canonical_name"],
    },
    to_team: {
      type: ["object", "null"],
      properties: {
        name: { type: "string" },
        canonical_name: { type: "string" },
      },
      required: ["name", "canonical_name"],
    },
    confidence_score: { type: "number", minimum: 0, maximum: 100 },
    status: { type: "string", enum: ["rumor", "confirmed", "denied"] },
    key_quote: { type: ["string", "null"] },
    source_reliability: { type: "number", minimum: 1, maximum: 5 },
  },
  required: [
    "is_transfer_rumor",
    "player",
    "from_team",
    "to_team",
    "confidence_score",
    "status",
    "key_quote",
    "source_reliability",
  ],
};

serve(async (req: Request) => {
  const corsResp = handleCors(req);
  if (corsResp) return corsResp;

  if (req.method !== "POST") {
    return new Response(
      JSON.stringify({ error: { code: "INVALID_INPUT", message: "Method not allowed" } }),
      { status: 405, headers: { ...corsHeaders, "Content-Type": "application/json" } },
    );
  }

  try {
    const body = await req.json();
    const validation = validateRequest(ParseRumorsRequestSchema, body);
    if (!validation.success) {
      return new Response(
        JSON.stringify({ error: { code: "INVALID_INPUT", message: validation.error } }),
        { status: 400, headers: { ...corsHeaders, "Content-Type": "application/json" } },
      );
    }

    const { article_ids, max_articles } = validation.data;
    const supabase = getSupabaseClient();

    // 1. Fetch unparsed articles
    let query = supabase
      .from("articles")
      .select("id, source_name, title, content, published_at, tags")
      .order("published_at", { ascending: false });

    if (article_ids && article_ids.length > 0) {
      query = query.in("id", article_ids);
    } else {
      // 미파싱 기사: tags에 'transfer' 포함
      // 이미 파싱된 기사는 제외 (rumor_sources에 해당 article URL이 존재하는 것은 제외 불가하므로
      // meta에 parsed 플래그를 사용하거나 최근 기사만 처리)
      query = query.contains("tags", ["transfer"]).limit(max_articles!);
    }

    const { data: articles, error: fetchError } = await query;

    if (fetchError) {
      return new Response(
        JSON.stringify({ error: { code: "INTERNAL_ERROR", message: fetchError.message } }),
        { status: 500, headers: { ...corsHeaders, "Content-Type": "application/json" } },
      );
    }

    if (!articles || articles.length === 0) {
      const result: ParseRumorsResponse = {
        parsed_count: 0,
        rumors_created: 0,
        rumors_updated: 0,
        sources_created: 0,
        errors: [],
      };
      return new Response(JSON.stringify(result), {
        status: 200,
        headers: { ...corsHeaders, "Content-Type": "application/json" },
      });
    }

    // 2. Process each article
    let rumorsCreated = 0;
    let rumorsUpdated = 0;
    let sourcesCreated = 0;
    const errors: { article_id: string; error: string }[] = [];

    for (const article of articles) {
      try {
        // Build article content for AI
        const articleContent = `Article Source: ${article.source_name}
Article Title: ${article.title}
Article Content: ${article.content ?? ""}
Published At: ${article.published_at ?? "unknown"}`;

        // Claude API entity extraction
        let parsed: ParsedRumor | null = null;

        for await (const event of callAI(PARSE_RUMORS_SYSTEM_PROMPT, articleContent, {
          model: "claude-sonnet-4-20250514",
          maxTokens: 1024,
          temperature: 0,
          timeoutMs: 30_000,
          tools: [{
            name: "parse_transfer_rumor",
            description: "Extract transfer rumor entities from a football article",
            input_schema: PARSED_RUMOR_SCHEMA,
          }],
          toolChoice: { type: "tool", name: "parse_transfer_rumor" },
        })) {
          if (event.event === "result") {
            parsed = event.data as unknown as ParsedRumor;
          }
        }

        if (!parsed || !parsed.is_transfer_rumor || !parsed.player) {
          continue;
        }

        // 3. Match entities to DB
        const playerId = await matchPlayer(supabase, parsed.player.canonical_name);
        const fromTeamId = parsed.from_team
          ? await matchTeam(supabase, parsed.from_team.canonical_name)
          : null;
        const toTeamId = parsed.to_team
          ? await matchTeam(supabase, parsed.to_team.canonical_name)
          : null;

        if (!playerId) {
          errors.push({
            article_id: article.id,
            error: `Player not found: ${parsed.player.canonical_name}`,
          });
          continue;
        }

        // 4. UPSERT transfer_rumors (player_id + to_team_id 기준)
        const { data: existingRumor } = await supabase
          .from("transfer_rumors")
          .select("id, confidence_score")
          .eq("player_id", playerId)
          .eq("to_team_id", toTeamId ?? "")
          .maybeSingle();

        let rumorId: string;

        if (existingRumor) {
          // Update existing rumor
          const newConfidence = Math.max(
            existingRumor.confidence_score,
            parsed.confidence_score,
          );
          await supabase
            .from("transfer_rumors")
            .update({
              confidence_score: newConfidence,
              status: parsed.status,
              last_updated_at: new Date().toISOString(),
              meta: {
                last_article_id: article.id,
                key_quote: parsed.key_quote,
              },
            })
            .eq("id", existingRumor.id);

          rumorId = existingRumor.id;
          rumorsUpdated++;
        } else {
          // Insert new rumor
          const { data: newRumor } = await supabase
            .from("transfer_rumors")
            .insert({
              player_id: playerId,
              from_team_id: fromTeamId,
              to_team_id: toTeamId,
              confidence_score: parsed.confidence_score,
              status: parsed.status,
              meta: {
                original_player_name: parsed.player.name,
                original_from_team: parsed.from_team?.name,
                original_to_team: parsed.to_team?.name,
                key_quote: parsed.key_quote,
              },
            })
            .select("id")
            .single();

          rumorId = newRumor!.id;
          rumorsCreated++;
        }

        // 5. INSERT rumor_sources
        await supabase.from("rumor_sources").insert({
          rumor_id: rumorId,
          source_name: article.source_name,
          source_url: article.url ?? null,
          journalist: null,
          reliability_tier: parsed.source_reliability,
          published_at: article.published_at,
        });
        sourcesCreated++;
      } catch (err) {
        errors.push({
          article_id: article.id,
          error: err instanceof Error ? err.message : "Unknown error",
        });
      }
    }

    const result: ParseRumorsResponse = {
      parsed_count: articles.length,
      rumors_created: rumorsCreated,
      rumors_updated: rumorsUpdated,
      sources_created: sourcesCreated,
      errors,
    };

    return new Response(JSON.stringify(result), {
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

// --- Entity matching helpers ---

async function matchPlayer(
  supabase: ReturnType<typeof getSupabaseClient>,
  canonicalName: string,
): Promise<string | null> {
  // 1. Exact name match
  const { data: exact } = await supabase
    .from("players")
    .select("id")
    .ilike("name", canonicalName)
    .maybeSingle();

  if (exact) return exact.id;

  // 2. Full name match
  const { data: fullName } = await supabase
    .from("players")
    .select("id")
    .ilike("full_name", `%${canonicalName}%`)
    .maybeSingle();

  if (fullName) return fullName.id;

  // 3. Fuzzy match (ILIKE with partial)
  const parts = canonicalName.split(" ");
  if (parts.length >= 2) {
    const lastName = parts[parts.length - 1];
    const { data: fuzzy } = await supabase
      .from("players")
      .select("id")
      .ilike("name", `%${lastName}%`)
      .limit(1)
      .maybeSingle();

    if (fuzzy) return fuzzy.id;
  }

  return null;
}

async function matchTeam(
  supabase: ReturnType<typeof getSupabaseClient>,
  canonicalName: string,
): Promise<string | null> {
  // 1. Canonical match
  const { data: exact } = await supabase
    .from("teams")
    .select("id")
    .ilike("canonical", canonicalName)
    .maybeSingle();

  if (exact) return exact.id;

  // 2. Name match
  const { data: nameMatch } = await supabase
    .from("teams")
    .select("id")
    .ilike("name", `%${canonicalName}%`)
    .maybeSingle();

  if (nameMatch) return nameMatch.id;

  return null;
}
