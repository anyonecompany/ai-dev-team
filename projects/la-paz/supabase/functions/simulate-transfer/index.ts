// ================================================================
// La Paz — Edge Function: simulate-transfer
// Transfer Simulation (API_CONTRACT.md §4, AI_PROMPTS.md §2)
// ================================================================

import { serve } from "https://deno.land/std@0.208.0/http/server.ts";
import { getSupabaseClient, getUserFromRequest, getClientIp } from "../_shared/supabase.ts";
import { handleCors, corsHeaders } from "../_shared/cors.ts";
import { SimulateTransferRequestSchema, validateRequest } from "../_shared/validate.ts";
import { createSSEStream, type SSEWriter } from "../_shared/sse.ts";
import { callAI, getErrorMessage } from "../_shared/ai-client.ts";
import { checkRateLimit, logFanEvent } from "../_shared/rate-limit.ts";
import type { TransferSimulationResult } from "../_shared/types.ts";

// --- Prompt (AI_PROMPTS.md §2) ---

const TRANSFER_SYSTEM_PROMPT = `You are a football transfer analyst AI for La Paz platform.

## STRICT RULES
1. Base your analysis ONLY on the provided player statistics and team data.
2. Do NOT invent statistics, market values, or salary figures not in the context.
3. If critical data is missing, note it in the caveats array.
4. Provide a balanced analysis — highlight both benefits and risks.
5. The overall_rating must reflect the data quality (lower if data is sparse).

## ANALYSIS FRAMEWORK
- Team Strength: Compare team stats before/after the hypothetical transfer
- Formation Impact: How does the player fit the team's current/alternative formation
- Position Fit: Player's position vs team's needs
- Salary Feasibility: Based on team's wage structure (if available)`;

const TRANSFER_SCHEMA = {
  type: "object" as const,
  properties: {
    team_strength_change: {
      type: "object",
      properties: {
        before: { type: "number" },
        after: { type: "number" },
        delta: { type: "number" },
      },
      required: ["before", "after", "delta"],
    },
    formation_impact: {
      type: "object",
      properties: {
        current_formation: { type: "string" },
        suggested_formation: { type: "string" },
        analysis: { type: "string" },
      },
      required: ["current_formation", "suggested_formation", "analysis"],
    },
    position_fit: {
      type: "object",
      properties: {
        score: { type: "number" },
        reasoning: { type: "string" },
      },
      required: ["score", "reasoning"],
    },
    salary_feasibility: {
      type: "object",
      properties: {
        assessment: { type: "string", enum: ["feasible", "stretch", "unlikely"] },
        reasoning: { type: "string" },
      },
      required: ["assessment", "reasoning"],
    },
    overall_rating: { type: "number" },
    summary: { type: "string" },
    caveats: { type: "array", items: { type: "string" } },
  },
  required: [
    "team_strength_change",
    "formation_impact",
    "position_fit",
    "salary_feasibility",
    "overall_rating",
    "summary",
    "caveats",
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

  let body: unknown;
  try {
    body = await req.json();
  } catch {
    return new Response(
      JSON.stringify({ error: { code: "INVALID_INPUT", message: "Invalid JSON" } }),
      { status: 400, headers: { ...corsHeaders, "Content-Type": "application/json" } },
    );
  }

  const validation = validateRequest(SimulateTransferRequestSchema, body);
  if (!validation.success) {
    return new Response(
      JSON.stringify({ error: { code: "INVALID_INPUT", message: validation.error } }),
      { status: 400, headers: { ...corsHeaders, "Content-Type": "application/json" } },
    );
  }

  const { player_id, target_team_id } = validation.data;
  const supabase = getSupabaseClient();
  const userId = getUserFromRequest(req);
  const clientIp = getClientIp(req);

  // Rate limit
  const rateLimit = await checkRateLimit(supabase, userId, clientIp);
  if (!rateLimit.allowed) {
    return new Response(
      JSON.stringify({ error: { code: "RATE_LIMITED", message: getErrorMessage("rate_limit") } }),
      { status: 429, headers: { ...corsHeaders, "Content-Type": "application/json" } },
    );
  }

  // Validate player/team existence
  const [playerRes, teamRes] = await Promise.all([
    supabase.from("players").select("id, name, position, meta").eq("id", player_id).maybeSingle(),
    supabase.from("teams").select("id, name").eq("id", target_team_id).maybeSingle(),
  ]);

  if (!playerRes.data || !teamRes.data) {
    return new Response(
      JSON.stringify({
        error: {
          code: "INVALID_INPUT",
          message: !playerRes.data ? "Player not found" : "Team not found",
        },
      }),
      { status: 404, headers: { ...corsHeaders, "Content-Type": "application/json" } },
    );
  }

  return createSSEStream(async (writer: SSEWriter) => {
    const startTime = Date.now();

    // 1. Send metadata
    writer.send("metadata", {
      ai_generated: true,
      simulation_type: "transfer",
    });

    // 2. Gather data (including player's current team for comparison per AI_PROMPTS.md §2)
    // Find player's current team
    const { data: currentContract } = await supabase
      .from("player_contracts")
      .select("team_id, teams(name)")
      .eq("player_id", player_id)
      .eq("is_active", true)
      .limit(1)
      .maybeSingle();

    const currentTeamId = currentContract?.team_id ?? null;

    const [playerStats, teamStats, squadRes, formationsRes, currentTeamStats] = await Promise.all([
      supabase
        .from("player_season_stats")
        .select("*")
        .eq("player_id", player_id)
        .order("created_at", { ascending: false })
        .limit(1)
        .maybeSingle(),
      supabase
        .from("team_season_stats")
        .select("*")
        .eq("team_id", target_team_id)
        .order("created_at", { ascending: false })
        .limit(1)
        .maybeSingle(),
      supabase
        .from("player_contracts")
        .select("player_id, players(name, position)")
        .eq("team_id", target_team_id)
        .eq("is_active", true)
        .limit(30),
      supabase
        .from("formations")
        .select("formation")
        .eq("team_id", target_team_id)
        .order("created_at", { ascending: false })
        .limit(3),
      // Player's current team stats (for comparison)
      currentTeamId
        ? supabase
            .from("team_season_stats")
            .select("*")
            .eq("team_id", currentTeamId)
            .order("created_at", { ascending: false })
            .limit(1)
            .maybeSingle()
        : Promise.resolve({ data: null }),
    ]);

    // Build context
    const currentTeamName = (currentContract as Record<string, unknown>)?.teams
      ? ((currentContract as Record<string, unknown>).teams as { name: string }).name
      : "Unknown";

    const contextParts = [
      `Player: ${playerRes.data.name} (${playerRes.data.position ?? "unknown"})`,
      `Player Current Team: ${currentTeamName}`,
      `Player Current Season Stats:\n${JSON.stringify(playerStats.data ?? {}, null, 2)}`,
      `\nPlayer's Current Team Stats (for comparison):\n${JSON.stringify(currentTeamStats.data ?? {}, null, 2)}`,
      `\nTarget Team: ${teamRes.data.name}`,
      `Target Team Current Season Stats:\n${JSON.stringify(teamStats.data ?? {}, null, 2)}`,
      `\nTarget Team Current Squad:\n${JSON.stringify(squadRes.data ?? [], null, 2)}`,
      `\nTarget Team Recent Formations:\n${JSON.stringify(formationsRes.data ?? [], null, 2)}`,
    ];

    const contextPrompt = `${TRANSFER_SYSTEM_PROMPT}

## INPUT CONTEXT
${contextParts.join("\n")}`;

    // 3. Claude AI structured output
    let result: TransferSimulationResult | null = null;
    let modelUsed = "claude-sonnet-4-20250514";

    for await (const event of callAI(contextPrompt, `Analyze the hypothetical transfer of ${playerRes.data.name} to ${teamRes.data.name}.`, {
      maxTokens: 2048,
      temperature: 0.3,
      timeoutMs: 60_000,
      tools: [{
        name: "analyze_transfer",
        description: "Analyze a hypothetical player transfer",
        input_schema: TRANSFER_SCHEMA,
      }],
      toolChoice: { type: "tool", name: "analyze_transfer" },
    })) {
      if (event.event === "result") {
        result = event.data as unknown as TransferSimulationResult;
        writer.send("result", event.data);
      } else if (event.event === "error") {
        writer.send("error", event.data);
        if (!(event.data as { fallback: boolean }).fallback) return;
      } else if (event.event === "done") {
        modelUsed = (event.data as { model: string }).model;
      }
    }

    // 4. Save to simulations table
    const { data: sim } = await supabase
      .from("simulations")
      .insert({
        user_id: userId,
        sim_type: "transfer",
        params: { player_id, target_team_id },
        result: result ?? {},
        model_used: modelUsed,
        latency_ms: Date.now() - startTime,
      })
      .select("id")
      .single();

    // 5. Done event (SSE_FORMAT.md §2.5)
    writer.send("done", {
      simulation_id: sim?.id ?? null,
      model: modelUsed,
      latency_ms: Date.now() - startTime,
      tokens_used: 0,
    });

    // 6. Async: log fan event
    logFanEvent(supabase, {
      userId,
      eventType: "simulation",
      clientIp,
      payload: {
        sim_type: "transfer",
        player_id,
        target_team_id,
        model: modelUsed,
      },
    }).catch(() => {});
  });
});
