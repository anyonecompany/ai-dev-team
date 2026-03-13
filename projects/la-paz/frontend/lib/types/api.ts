// Edge Function Request/Response types — synced with API_CONTRACT.md

export interface ChatRequest {
  message: string;
  session_id?: string;
  locale: "ko" | "en";
}

export interface ChatTokenEvent {
  text: string;
}

export interface ChatSource {
  doc_id: string;
  title: string;
  snippet: string;
  doc_type: string;
  similarity: number;
}

export interface ChatSourcesEvent {
  sources: ChatSource[];
}

export interface ChatDoneEvent {
  session_id: string;
  message_id: string;
  model_used: string;
  latency_ms: number;
}

export interface SearchRequest {
  query: string;
  limit?: number;
  locale?: "ko" | "en";
}

export interface SearchResponse {
  results: Array<{
    doc_id: string;
    title: string;
    snippet: string;
    similarity: number;
    doc_type: string;
  }>;
  query_time_ms: number;
}

export interface SimulateTransferRequest {
  player_id: string;
  target_team_id: string;
}

export interface SimulateMatchRequest {
  home_team_id: string;
  away_team_id: string;
}

export interface TransferAnalysisEvent {
  section: "team_strength" | "formation_impact" | "position_fit" | "salary_feasibility" | "overall";
  data: Record<string, unknown>;
}

export interface MatchPredictionEvent {
  section: "predicted_score" | "win_probability" | "key_factors" | "head_to_head" | "overall";
  data: Record<string, unknown>;
}

export interface SSEDoneEvent {
  model: string;
  latency_ms: number;
  tokens_used?: number;
  simulation_id?: string;
}

export interface SSEErrorEvent {
  code: string;
  message: string;
  fallback: boolean;
}

export interface ErrorResponse {
  error: {
    code: string;
    message: string;
    details?: unknown;
  };
}
