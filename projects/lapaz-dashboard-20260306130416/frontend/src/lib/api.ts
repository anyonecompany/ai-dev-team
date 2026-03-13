import type { AskResponse, MatchInfo, Question } from "@/types";

const BASE_URL = "http://localhost:8000";

export async function askQuestion(
  question: string,
  matchContext?: { home_team: string; away_team: string; match_date: string }
): Promise<AskResponse> {
  const res = await fetch(`${BASE_URL}/api/ask`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question, match_context: matchContext }),
  });
  if (!res.ok) throw new Error(`Failed to ask question: ${res.status}`);
  return res.json();
}

export async function getQuestions(
  status?: string,
  limit = 20,
  offset = 0
): Promise<{ questions: Question[]; total: number }> {
  const params = new URLSearchParams();
  if (status) params.set("status", status);
  params.set("limit", String(limit));
  params.set("offset", String(offset));
  const res = await fetch(`${BASE_URL}/api/questions?${params}`);
  if (!res.ok) throw new Error(`Failed to fetch questions: ${res.status}`);
  return res.json();
}

export async function updateQuestionStatus(
  id: string,
  status: string
): Promise<{ id: string; status: string; updated_at: string }> {
  const res = await fetch(`${BASE_URL}/api/questions/${id}/status`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ status }),
  });
  if (!res.ok) throw new Error(`Failed to update status: ${res.status}`);
  return res.json();
}

export async function getMatchInfo(): Promise<MatchInfo> {
  const res = await fetch(`${BASE_URL}/api/match/live`);
  if (!res.ok) throw new Error(`Failed to fetch match info: ${res.status}`);
  return res.json();
}
