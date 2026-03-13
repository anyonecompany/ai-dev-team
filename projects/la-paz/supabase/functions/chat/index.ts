// ================================================================
// La Paz — Edge Function: chat
// RAG Pipeline + SSE Streaming (API_CONTRACT.md §1)
// ================================================================

import { serve } from "https://deno.land/std@0.208.0/http/server.ts";
import { getSupabaseClient, getUserFromRequest, getClientIp } from "../_shared/supabase.ts";
import { handleCors, corsHeaders } from "../_shared/cors.ts";
import { ChatRequestSchema, validateRequest } from "../_shared/validate.ts";
import { createSSEStream, type SSEWriter } from "../_shared/sse.ts";
import { callAI, getErrorMessage } from "../_shared/ai-client.ts";
import { checkRateLimit, logFanEvent } from "../_shared/rate-limit.ts";
import type { IntentClassification, SourceItem } from "../_shared/types.ts";

// --- 한→영 엔티티 매핑 ---
const ENTITY_MAP: Record<string, string> = {
  "손흥민": "Son Heung-min",
  "이강인": "Lee Kang-in",
  "김민재": "Kim Min-jae",
  "황희찬": "Hwang Hee-chan",
  "토트넘": "Tottenham Hotspur",
  "맨시티": "Manchester City",
  "맨유": "Manchester United",
  "리버풀": "Liverpool",
  "첼시": "Chelsea",
  "아스널": "Arsenal",
  "바르셀로나": "Barcelona",
  "레알 마드리드": "Real Madrid",
  "바이에른 뮌헨": "Bayern Munich",
  "아스톤빌라": "Aston Villa",
  "빌라": "Aston Villa",
  "에메리": "Unai Emery",
  "캐릭": "Michael Carrick",
  "브루노": "Bruno Fernandes",
  "왓킨스": "Ollie Watkins",
  "디알로": "Amad Diallo",
  "메이누": "Kobbie Mainoo",
  "마즈라위": "Noussair Mazraoui",
  "도르구": "Patrick Dorgu",
  "드리흐트": "Matthijs de Ligt",
  "우가르테": "Manuel Ugarte",
  "오나나": "Amadou Onana",
  "티엘레만스": "Youri Tielemans",
  "맥긴": "John McGinn",
  "올드 트래포드": "Old Trafford",
  "EPL": "Premier League",
  "프리미어리그": "Premier League",
};

// --- Prompts (AI_PROMPTS.md §1) ---

const INTENT_SYSTEM_PROMPT = `You are an intent classifier for a football intelligence platform.
Analyze the user's query and extract structured information.
Do NOT answer the question — only classify it.

Respond with valid JSON matching the schema exactly.`;

const RAG_SYSTEM_PROMPT = `You are La Paz, an expert football analyst AI.

## STRICT RULES
1. Answer ONLY based on the provided context documents below.
2. If the context does not contain the answer, respond: "해당 데이터가 없습니다." (Korean) or "No data available for this query." (English)
3. NEVER generate statistics, scores, dates, or any factual claims not present in the context.
4. NEVER hallucinate player names, team names, match results, or transfer fees.
5. Cite sources using numbered references [1], [2], etc. that map to the sources array.
6. Match the user's language (Korean or English) based on their query.

## RESPONSE FORMAT
- Be concise and factual.
- Use numbered citations inline: "손흥민은 이번 시즌 12골을 기록했습니다 [1]."
- End with a brief disclaimer if the data might be incomplete.

## CONTEXT DOCUMENTS
{context}`;

const INTENT_SCHEMA = {
  type: "object" as const,
  properties: {
    intent: {
      type: "string",
      enum: ["stat_lookup", "comparison", "transfer", "injury", "schedule", "prediction", "opinion", "news", "other"],
    },
    sub_intent: { type: ["string", "null"] },
    entities: {
      type: "array",
      items: {
        type: "object",
        properties: {
          name: { type: "string" },
          type: { type: "string", enum: ["player", "team", "competition", "manager", "match"] },
          confidence: { type: "number" },
        },
        required: ["name", "type", "confidence"],
      },
    },
    temporal_frame: {
      type: "string",
      enum: ["current_season", "last_season", "career", "specific_date", "recent", "all_time", "unknown"],
    },
    language: { type: "string", enum: ["ko", "en"] },
  },
  required: ["intent", "sub_intent", "entities", "temporal_frame", "language"],
};

function mapEntities(query: string): string {
  let mapped = query;
  for (const [ko, en] of Object.entries(ENTITY_MAP)) {
    if (mapped.includes(ko)) mapped = mapped.replace(ko, en);
  }
  return mapped;
}

// Reverse map: English → Korean variants for bilingual search
const REVERSE_ENTITY_MAP: Record<string, string[]> = {};
for (const [ko, en] of Object.entries(ENTITY_MAP)) {
  if (!REVERSE_ENTITY_MAP[en]) REVERSE_ENTITY_MAP[en] = [];
  REVERSE_ENTITY_MAP[en].push(ko);
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

  let body: unknown;
  try {
    body = await req.json();
  } catch {
    return new Response(
      JSON.stringify({ error: { code: "INVALID_INPUT", message: "Invalid JSON" } }),
      { status: 400, headers: { ...corsHeaders, "Content-Type": "application/json" } },
    );
  }

  const validation = validateRequest(ChatRequestSchema, body);
  if (!validation.success) {
    return new Response(
      JSON.stringify({ error: { code: "INVALID_INPUT", message: validation.error } }),
      { status: 400, headers: { ...corsHeaders, "Content-Type": "application/json" } },
    );
  }

  const { message, session_id, locale } = validation.data;
  const supabase = getSupabaseClient();
  const userId = getUserFromRequest(req);
  const clientIp = getClientIp(req);

  // Rate limit check
  const rateLimit = await checkRateLimit(supabase, userId, clientIp);
  if (!rateLimit.allowed) {
    return new Response(
      JSON.stringify({
        error: { code: "RATE_LIMITED", message: getErrorMessage("rate_limit", locale) },
      }),
      { status: 429, headers: { ...corsHeaders, "Content-Type": "application/json" } },
    );
  }

  return createSSEStream(async (writer: SSEWriter) => {
    const startTime = Date.now();

    // 1. Intent Classification (Claude structured output)
    let intent: IntentClassification | null = null;
    try {
      for await (const event of callAI(INTENT_SYSTEM_PROMPT, message, {
        model: "claude-sonnet-4-20250514",
        maxTokens: 512,
        temperature: 0,
        tools: [{
          name: "classify_intent",
          description: "Classify the football query intent",
          input_schema: INTENT_SCHEMA,
        }],
        toolChoice: { type: "tool", name: "classify_intent" },
      })) {
        if (event.event === "result") {
          intent = event.data as unknown as IntentClassification;
        }
      }
    } catch {
      // Intent classification failure is non-fatal
    }

    // 2. Send metadata event
    writer.send("metadata", {
      intent: intent?.intent ?? "other",
      entities: intent?.entities ?? [],
      language: intent?.language ?? locale,
      ai_generated: true,
    });

    // 3. Hybrid Search
    // DB schema: documents(id, collection, content, metadata jsonb, embedding vector(1024))
    // metadata contains: title, ref_id, doc_type, etc.
    const searchQuery = locale === "ko" ? mapEntities(message) : message;
    const allDocs: Array<{
      id: string;
      doc_type: string;
      ref_id: string | null;
      title: string;
      content: string;
      metadata: unknown;
      similarity: number;
    }> = [];
    const seenIds = new Set<string>();

    // Helper: extract doc fields from DB row (collection/metadata schema)
    const toDoc = (row: Record<string, unknown>) => {
      const meta = (row.metadata ?? {}) as Record<string, unknown>;
      return {
        id: String(row.id),
        doc_type: (meta.doc_type as string) ?? (row.collection as string) ?? "unknown",
        ref_id: (meta.ref_id as string) ?? null,
        title: (meta.title as string) ?? (meta.page_title as string) ?? "",
        content: (row.content as string) ?? "",
        metadata: meta,
      };
    };

    // 3a. Entity direct SQL lookup (if intent has entities)
    if (intent?.entities && intent.entities.length > 0) {
      for (const entity of intent.entities) {
        const collections = entity.type === "player"
          ? ["player_profile", "player_profiles", "fan_player_profile"]
          : entity.type === "team"
            ? ["team_profile", "match_context"]
            : entity.type === "manager"
              ? ["manager_analysis"]
              : [];

        if (collections.length > 0) {
          // Search with both English name and Korean variants
          const searchNames = [entity.name];
          const koVariants = REVERSE_ENTITY_MAP[entity.name];
          if (koVariants) searchNames.push(...koVariants);
          // Also check if entity.name itself is Korean (from intent classifier)
          const enVariant = ENTITY_MAP[entity.name];
          if (enVariant) searchNames.push(enVariant);

          for (const name of searchNames) {
            const { data: entityDocs } = await supabase
              .from("documents")
              .select("id, collection, content, metadata")
              .in("collection", collections)
              .ilike("content", `%${name}%`)
              .limit(3);
            if (entityDocs) {
              for (const row of entityDocs) {
                const d = toDoc(row);
                if (!seenIds.has(d.id)) {
                  seenIds.add(d.id);
                  allDocs.push({ ...d, similarity: 0.95 });
                }
              }
            }
          }
        }
      }
    }

    // 3b. pgvector cosine similarity (match_documents RPC)
    // Note: requires embedding generation; if embedding is not available, skip
    // In production, call an embedding API here. For now, skip if no embedding endpoint.

    // 3c. Keyword search (ILIKE fallback) — search in content
    // Extract key terms from the mapped query for better matching
    const keyTerms = new Set<string>();
    // Add full mapped query
    keyTerms.add(searchQuery);
    // Add individual entity names from the mapped query
    for (const en of Object.values(ENTITY_MAP)) {
      if (searchQuery.includes(en)) keyTerms.add(en);
    }
    // Add original Korean entity names from the message
    for (const ko of Object.keys(ENTITY_MAP)) {
      if (message.includes(ko)) keyTerms.add(ko);
    }

    for (const term of keyTerms) {
      if (allDocs.length >= 15) break; // enough context
      const { data: docs } = await supabase
        .from("documents")
        .select("id, collection, content, metadata")
        .ilike("content", `%${term}%`)
        .order("created_at", { ascending: false })
        .limit(4);

      if (docs) {
        for (const row of docs) {
          const d = toDoc(row);
          if (!seenIds.has(d.id)) {
            seenIds.add(d.id);
            allDocs.push({ ...d, similarity: 0.7 });
          }
        }
      }
    }

    // 3d. Search pre-generated Q&A by collection (both English + Korean)
    const qaSearchTerms = [searchQuery];
    if (searchQuery !== message) qaSearchTerms.push(message);
    let qaDocs: Record<string, unknown>[] | null = null;
    for (const qaTerm of qaSearchTerms) {
      const { data } = await supabase
        .from("documents")
        .select("id, collection, content, metadata")
        .eq("collection", "pre_generated_qa")
        .ilike("content", `%${qaTerm}%`)
        .limit(2);
      if (data && data.length > 0) {
        qaDocs = data as Record<string, unknown>[];
        break;
      }
    }

    if (qaDocs) {
      for (const row of qaDocs) {
        const d = toDoc(row);
        if (!seenIds.has(d.id)) {
          seenIds.add(d.id);
          allDocs.push({ ...d, similarity: 0.9 });
        }
      }
    }

    // Sort by similarity descending, limit to top 8 for context window
    allDocs.sort((a, b) => b.similarity - a.similarity);
    const topDocs = allDocs.slice(0, 8);

    const sources: SourceItem[] = [];
    let contextDocs = "";

    topDocs.forEach((doc, idx) => {
      sources.push({
        title: doc.title,
        doc_type: doc.doc_type,
        ref_id: doc.ref_id ?? doc.id,
        similarity: doc.similarity,
      });

      contextDocs += `\n---\n[Document ${idx + 1}]\nTitle: ${doc.title}\nType: ${doc.doc_type}\nSimilarity: ${doc.similarity}\nContent:\n${doc.content}\n---\n`;
    });

    // 4. Send sources event
    writer.send("sources", { sources });

    // 5. No context → fixed response
    if (sources.length === 0) {
      const noDataMsg = locale === "ko"
        ? "해당 데이터가 없습니다."
        : "No data available for this query.";

      writer.send("token", { content: noDataMsg });

      // Save session/message
      const sessionId = session_id ?? crypto.randomUUID();
      const messageId = crypto.randomUUID();

      await ensureSession(supabase, sessionId, userId, message);
      await saveMessage(supabase, sessionId, "user", message);
      await saveMessage(supabase, sessionId, "assistant", noDataMsg);

      writer.send("done", {
        session_id: sessionId,
        message_id: messageId,
        model: "none",
        latency_ms: Date.now() - startTime,
      });
      return;
    }

    // 6. RAG Generation (Claude SSE → Gemini fallback)
    const ragPrompt = RAG_SYSTEM_PROMPT.replace("{context}", contextDocs);
    let fullText = "";
    let modelUsed = "claude-sonnet-4-20250514";

    for await (const event of callAI(ragPrompt, message, {
      stream: true,
      maxTokens: 4096,
      temperature: 0.3,
      timeoutMs: 30_000,
    })) {
      if (event.event === "token") {
        fullText += (event.data as { content: string }).content;
        writer.send("token", event.data);
      } else if (event.event === "error") {
        writer.send("error", event.data);
        if (!(event.data as { fallback: boolean }).fallback) return;
      } else if (event.event === "done") {
        modelUsed = (event.data as { model: string }).model;
      }
    }

    // 7. Save chat session/messages
    const sessionId = session_id ?? crypto.randomUUID();
    const messageId = crypto.randomUUID();

    await ensureSession(supabase, sessionId, userId, message);
    await saveMessage(supabase, sessionId, "user", message);
    await saveMessage(supabase, sessionId, "assistant", fullText, modelUsed, Date.now() - startTime);

    // 8. Done event
    writer.send("done", {
      session_id: sessionId,
      message_id: messageId,
      model: modelUsed,
      latency_ms: Date.now() - startTime,
    });

    // 9. Async: log fan event + query_logs
    logFanEvent(supabase, {
      userId,
      eventType: "chat",
      clientIp,
      payload: {
        intent: intent?.intent,
        entities: intent?.entities,
        has_sources: sources.length > 0,
        model: modelUsed,
      },
    }).catch(() => {});

    // query_logs: 팬 데이터 로깅 원칙 (CLAUDE.md §4)
    // anon_id는 user_id를 익명화한 해시 (평문 user_id 저장 금지)
    const anonId = userId
      ? await crypto.subtle.digest("SHA-256", new TextEncoder().encode(userId + new Date().toISOString().slice(0, 10)))
          .then((buf) => Array.from(new Uint8Array(buf)).map((b) => b.toString(16).padStart(2, "0")).join(""))
      : "anonymous";
    const sessionHash = sessionId
      ? await crypto.subtle.digest("SHA-256", new TextEncoder().encode(sessionId + new Date().toISOString().slice(0, 10)))
          .then((buf) => Array.from(new Uint8Array(buf)).map((b) => b.toString(16).padStart(2, "0")).join(""))
      : null;

    supabase.from("query_logs").insert({
      anon_id: anonId,
      session_hash: sessionHash,
      query_text: message,
      ui_language: intent?.language ?? locale,
      intent_type: intent?.intent ?? null,
      team_tags: intent?.entities?.filter((e) => e.type === "team").map((e) => e.name) ?? [],
      player_tags: intent?.entities?.filter((e) => e.type === "player").map((e) => e.name) ?? [],
      league_tags: intent?.entities?.filter((e) => e.type === "competition").map((e) => e.name) ?? [],
      retrieval_success: sources.length > 0,
      response_type: sources.length > 0 ? "rag" : "direct_lookup",
    }).then(() => {}).catch(() => {});
  });
});

// --- Helper functions ---

async function ensureSession(
  supabase: ReturnType<typeof getSupabaseClient>,
  sessionId: string,
  userId: string | null,
  firstMessage: string,
): Promise<void> {
  const { data: existing } = await supabase
    .from("chat_sessions")
    .select("id")
    .eq("id", sessionId)
    .maybeSingle();

  if (!existing) {
    await supabase.from("chat_sessions").insert({
      id: sessionId,
      user_id: userId,
      title: firstMessage.substring(0, 100),
      model_used: "claude-sonnet-4-20250514",
      message_count: 0,
    });
  }

  await supabase
    .from("chat_sessions")
    .update({ message_count: (existing ? 1 : 0) + 1, updated_at: new Date().toISOString() })
    .eq("id", sessionId);
}

async function saveMessage(
  supabase: ReturnType<typeof getSupabaseClient>,
  sessionId: string,
  role: "user" | "assistant",
  content: string,
  model?: string,
  latencyMs?: number,
): Promise<void> {
  await supabase.from("chat_messages").insert({
    session_id: sessionId,
    role,
    content,
    model: model ?? null,
    latency_ms: latencyMs ?? null,
  });
}
