// ================================================================
// La Paz — Rate Limiting (AI_FALLBACK.md §4)
// ================================================================

import type { SupabaseClient } from "npm:@supabase/supabase-js@2";

interface RateLimitResult {
  allowed: boolean;
  remaining: number;
}

export async function checkRateLimit(
  supabase: SupabaseClient,
  userId: string | null,
  clientIp: string,
): Promise<RateLimitResult> {
  const windowMs = 60_000; // 1분
  const limit = userId ? 30 : 10;
  const since = new Date(Date.now() - windowMs).toISOString();

  let query = supabase
    .from("fan_events")
    .select("id", { count: "exact", head: true })
    .gte("created_at", since)
    .in("event_type", ["chat", "search", "simulation"]);

  if (userId) {
    query = query.eq("user_id", userId);
  } else {
    query = query.eq("payload->>client_ip", clientIp);
  }

  const { count } = await query;
  const used = count ?? 0;

  return {
    allowed: used < limit,
    remaining: Math.max(0, limit - used),
  };
}

export async function logFanEvent(
  supabase: SupabaseClient,
  params: {
    userId: string | null;
    eventType: string;
    clientIp: string;
    payload?: Record<string, unknown>;
  },
): Promise<void> {
  await supabase.from("fan_events").insert({
    user_id: params.userId,
    event_type: params.eventType,
    payload: { client_ip: params.clientIp, ...params.payload },
  });
}
