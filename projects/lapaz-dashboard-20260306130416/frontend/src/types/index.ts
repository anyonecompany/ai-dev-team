export interface MatchContext {
  home_team: string;
  away_team: string;
  match_date: string;
  current_minute?: number;
}

export interface Question {
  id: string;
  question: string;
  answer: string;
  category: string;
  confidence: number;
  source_count: number;
  generation_time_ms: number;
  status: "draft" | "published" | "archived";
  match_context?: MatchContext;
  created_at: string;
  updated_at: string;
}

export interface MatchInfo {
  home_team: string;
  away_team: string;
  match_date: string;
  kickoff_time: string;
  status: "upcoming" | "live" | "finished";
  current_minute?: number;
}

export interface AskResponse {
  id: string;
  question: string;
  answer: string;
  category: string;
  confidence: number;
  source_count: number;
  generation_time_ms: number;
  status: string;
}
