import type {
  AskResponse,
  MatchInfo,
  MatchPreviewData,
  Question,
  StandingEntry,
} from "@/types";

const BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "https://lapaz-live.fly.dev";
const DEFAULT_TIMEOUT_MS = 30_000;

interface AskStreamHandlers {
  onMetadata?: (data: { category: string; confidence: number; cached?: boolean }) => void;
  onChunk?: (text: string) => void;
  onAnswer?: (text: string) => void;
  onDone?: (data: {
    id: string;
    status: string;
    source_count: number;
    generation_time_ms?: number;
    total_time_ms?: number;
    cleaned_answer?: string;
  }) => void;
}

export async function askQuestion(
  question: string,
  matchContext?: { home_team: string; away_team: string; match_date: string }
): Promise<AskResponse> {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), DEFAULT_TIMEOUT_MS);
  try {
    const res = await fetch(`${BASE_URL}/api/ask`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question, match_context: matchContext }),
      signal: controller.signal,
    });
    if (!res.ok) throw new Error("질문 처리에 실패했습니다. 다시 시도해주세요.");
    return res.json();
  } catch (e) {
    if (e instanceof DOMException && e.name === "AbortError") {
      throw new Error("요청 시간이 초과되었습니다. 다시 시도해주세요.");
    }
    throw e;
  } finally {
    clearTimeout(timer);
  }
}

export async function askQuestionStream(
  question: string,
  matchContext?: { home_team: string; away_team: string; match_date: string; current_minute?: number },
  handlers?: AskStreamHandlers,
  options?: { force_football?: boolean; history?: Array<{ role: string; content: string }> }
): Promise<void> {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), DEFAULT_TIMEOUT_MS * 2);
  let res: Response;
  try {
    res = await fetch(`${BASE_URL}/api/ask/stream`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        question,
        match_context: matchContext,
        ...(options?.force_football ? { force_football: true } : {}),
        ...(options?.history && options.history.length > 0 ? { history: options.history } : {}),
      }),
      signal: controller.signal,
    });
  } catch (e) {
    clearTimeout(timer);
    if (e instanceof DOMException && e.name === "AbortError") {
      throw new Error("요청 시간이 초과되었습니다. 다시 시도해주세요.");
    }
    throw e;
  }

  if (!res.ok || !res.body) {
    clearTimeout(timer);
    throw new Error("답변 스트리밍에 실패했습니다. 다시 시도해주세요.");
  }

  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  const flushEvent = (rawEvent: string) => {
    const payload = rawEvent
      .split("\n")
      .filter((line) => line.startsWith("data: "))
      .map((line) => line.slice(6))
      .join("");

    if (!payload) return;

    const event = JSON.parse(payload) as {
      type: string;
      text?: string;
      category?: string;
      confidence?: number;
      cached?: boolean;
      id?: string;
      status?: string;
      source_count?: number;
      generation_time_ms?: number;
      total_time_ms?: number;
      cleaned_answer?: string;
      message?: string;
    };

    if (event.type === "metadata" && event.category && event.confidence !== undefined) {
      handlers?.onMetadata?.({
        category: event.category,
        confidence: event.confidence,
        cached: event.cached,
      });
      return;
    }

    if (event.type === "chunk" && event.text) {
      handlers?.onChunk?.(event.text);
      return;
    }

    if (event.type === "answer" && event.text) {
      handlers?.onAnswer?.(event.text);
      return;
    }

    if (event.type === "done" && event.id && event.status) {
      handlers?.onDone?.({
        id: event.id,
        status: event.status,
        source_count: event.source_count ?? 0,
        generation_time_ms: event.generation_time_ms,
        total_time_ms: event.total_time_ms,
        cleaned_answer: event.cleaned_answer,
      });
      return;
    }

    if (event.type === "error") {
      throw new Error(event.message || "스트리밍 중 오류가 발생했습니다.");
    }
  };

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });
    const parts = buffer.split("\n\n");
    buffer = parts.pop() ?? "";
    for (const part of parts) {
      flushEvent(part);
    }
  }

  if (buffer.trim()) {
    flushEvent(buffer);
  }

  clearTimeout(timer);
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
  if (!res.ok) throw new Error("질문 목록을 불러오지 못했습니다.");
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
  if (!res.ok) throw new Error("상태 업데이트에 실패했습니다.");
  return res.json();
}

export async function getMatchInfo(): Promise<MatchInfo> {
  const res = await fetch(`${BASE_URL}/api/match/live`);
  if (!res.ok) throw new Error("경기 정보를 불러오지 못했습니다.");
  return res.json();
}

export async function getMatchPreview(): Promise<MatchPreviewData> {
  const res = await fetch(`${BASE_URL}/api/match/preview`);
  if (!res.ok) throw new Error("경기 프리뷰를 불러오지 못했습니다.");
  return res.json();
}

export async function getStandings(): Promise<StandingEntry[]> {
  const res = await fetch(`${BASE_URL}/api/standings`);
  if (!res.ok) throw new Error("순위 정보를 불러오지 못했습니다.");
  return res.json();
}
