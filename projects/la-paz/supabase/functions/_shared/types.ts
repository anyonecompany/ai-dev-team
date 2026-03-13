// ================================================================
// La Paz — Shared Types for Edge Functions
// Source: API_CONTRACT.md + SSE_FORMAT.md + AI_PROMPTS.md
// ================================================================

// --- API Request Types ---

export interface ChatRequest {
  message: string;
  session_id?: string;
  locale: "ko" | "en";
}

export interface SearchRequest {
  query: string;
  limit?: number;
  locale?: "ko" | "en";
}

export interface ParseRumorsRequest {
  article_ids?: string[];
  max_articles?: number;
}

export interface SimulateTransferRequest {
  player_id: string;
  target_team_id: string;
}

export interface SimulateMatchRequest {
  home_team_id: string;
  away_team_id: string;
}

// --- API Response Types ---

export interface SearchResponse {
  results: SearchResult[];
  query_time_ms: number;
}

export interface SearchResult {
  doc_id: string;
  title: string;
  snippet: string;
  similarity: number;
  doc_type: string;
}

export interface ParseRumorsResponse {
  parsed_count: number;
  rumors_created: number;
  rumors_updated: number;
  sources_created: number;
  errors: { article_id: string; error: string }[];
}

export interface ErrorResponse {
  error: {
    code: string;
    message: string;
    details?: unknown;
  };
}

// --- SSE Event Types ---

export type SSEEventType =
  | "token"
  | "sources"
  | "metadata"
  | "result"
  | "done"
  | "error";

export interface SSEEvent {
  event: SSEEventType;
  data: Record<string, unknown>;
}

export interface TokenEvent {
  content: string;
}

export interface SourceItem {
  title: string;
  doc_type: string;
  ref_id: string;
  similarity: number;
}

export interface SourcesEvent {
  sources: SourceItem[];
}

export interface MetadataEvent {
  intent?: string;
  entities?: { name: string; type: string }[];
  language?: string;
  ai_generated: true;
  simulation_type?: "transfer" | "match";
}

export interface DoneEvent {
  model: string;
  latency_ms: number;
  tokens_used?: number;
  session_id?: string;
  message_id?: string;
  simulation_id?: string;
  processed?: number;
  rumors_found?: number;
}

export interface ErrorEventData {
  code: string;
  message: string;
  fallback: boolean;
}

// --- AI Structured Output Types ---

export interface IntentClassification {
  intent:
    | "stat_lookup"
    | "comparison"
    | "transfer"
    | "injury"
    | "schedule"
    | "prediction"
    | "opinion"
    | "news"
    | "other";
  sub_intent: string | null;
  entities: {
    name: string;
    type: "player" | "team" | "competition" | "manager" | "match";
    confidence: number;
  }[];
  temporal_frame:
    | "current_season"
    | "last_season"
    | "career"
    | "specific_date"
    | "recent"
    | "all_time"
    | "unknown";
  language: "ko" | "en";
}

export interface TransferSimulationResult {
  team_strength_change: {
    before: number;
    after: number;
    delta: number;
  };
  formation_impact: {
    current_formation: string;
    suggested_formation: string;
    analysis: string;
  };
  position_fit: {
    score: number;
    reasoning: string;
  };
  salary_feasibility: {
    assessment: "feasible" | "stretch" | "unlikely";
    reasoning: string;
  };
  overall_rating: number;
  summary: string;
  caveats: string[];
}

export interface MatchSimulationResult {
  predicted_score: {
    home: number;
    away: number;
  };
  win_probability: {
    home: number;
    draw: number;
    away: number;
  };
  key_factors: string[];
  head_to_head_analysis: string;
  form_analysis: {
    home: string;
    away: string;
  };
  disclaimer: string;
}

export interface ParsedRumor {
  is_transfer_rumor: boolean;
  player: { name: string; canonical_name: string } | null;
  from_team: { name: string; canonical_name: string } | null;
  to_team: { name: string; canonical_name: string } | null;
  confidence_score: number;
  status: "rumor" | "confirmed" | "denied";
  key_quote: string | null;
  source_reliability: number;
}

// --- AI Call Options ---

export interface AICallOptions {
  model?: string;
  maxTokens?: number;
  temperature?: number;
  stream?: boolean;
  timeoutMs?: number;
  tools?: unknown[];
  toolChoice?: unknown;
  responseSchema?: Record<string, unknown>;
}
