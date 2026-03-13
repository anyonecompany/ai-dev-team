export type Locale = "ko" | "en";

export type MatchStatus = "scheduled" | "live" | "finished" | "postponed";
export type RumorStatus = "rumor" | "confirmed" | "denied";
export type Position = "GK" | "DF" | "MF" | "FW";
export type FormResult = "W" | "D" | "L";

export interface TeamBrief {
  id: string;
  name: string;
  logoUrl: string | null;
}

export interface PlayerBrief {
  id: string;
  name: string;
  imageUrl: string | null;
  position: string;
}

export interface CompetitionBrief {
  id: string;
  name: string;
  logoUrl: string | null;
}
