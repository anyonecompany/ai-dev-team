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

export interface StandingEntry {
  rank: number;
  team_name: string;
  team_id: number;
  played: number;
  wins: number;
  draws: number;
  losses: number;
  goals_for: number;
  goals_against: number;
  goal_diff: number;
  points: number;
  form: string[];
}

export interface PlayerInfo {
  name: string;
  position: string;
  country: string;
  number?: number;
}

export interface TeamStats {
  team_name: string;
  team_id: number;
  standings?: StandingEntry;
  squad: PlayerInfo[];
  recent_form: string[];
  top_scorers: Record<string, unknown>[];
}

export interface MatchPreviewData {
  home: TeamStats;
  away: TeamStats;
  standings: StandingEntry[];
  match_date: string;
  match_id?: number;
}
