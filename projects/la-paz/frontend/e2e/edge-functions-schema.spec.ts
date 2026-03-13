import { test, expect } from "@playwright/test";

/**
 * Edge Function schema validation tests.
 * These tests verify the expected request/response schemas for each
 * Supabase Edge Function without making actual API calls.
 * They validate the TypeScript-level contract.
 */

// --- Schema definitions matching the Edge Functions ---

interface ChatRequest {
  message: string;
  session_id?: string;
  locale?: "ko" | "en";
}

interface ChatSSEMetadata {
  intent: string;
  entities: Array<{ name: string; type: string; confidence: number }>;
  language: string;
  ai_generated: boolean;
}

interface ChatSSEDone {
  session_id: string;
  message_id: string;
  model: string;
  latency_ms: number;
}

interface SearchRequest {
  query: string;
  limit?: number;
  locale?: "ko" | "en";
}

interface SearchResponse {
  results: Array<{
    doc_id: string;
    title: string;
    snippet: string;
    similarity: number;
    doc_type: string;
  }>;
  query_time_ms: number;
}

interface ParseRumorsRequest {
  article_ids?: string[];
  max_articles?: number;
}

interface ParseRumorsResponse {
  parsed_count: number;
  rumors_created: number;
  rumors_updated: number;
  sources_created: number;
  errors: Array<{ article_id: string; error: string }>;
}

interface SimulateTransferRequest {
  player_id: string;
  target_team_id: string;
}

interface TransferSimulationResult {
  team_strength_change: { before: number; after: number; delta: number };
  formation_impact: {
    current_formation: string;
    suggested_formation: string;
    analysis: string;
  };
  position_fit: { score: number; reasoning: string };
  salary_feasibility: {
    assessment: "feasible" | "stretch" | "unlikely";
    reasoning: string;
  };
  overall_rating: number;
  summary: string;
  caveats: string[];
}

interface SimulateMatchRequest {
  home_team_id: string;
  away_team_id: string;
}

interface MatchSimulationResult {
  predicted_score: { home: number; away: number };
  win_probability: { home: number; draw: number; away: number };
  key_factors: string[];
  head_to_head_analysis: string;
  form_analysis: { home: string; away: string };
  disclaimer: string;
}

// --- Tests ---

test.describe("Chat Edge Function schema", () => {
  test("ChatRequest has required fields", () => {
    const req: ChatRequest = { message: "손흥민 시즌 기록" };
    expect(req.message).toBeTruthy();
    expect(typeof req.message).toBe("string");
  });

  test("ChatRequest supports optional fields", () => {
    const req: ChatRequest = {
      message: "EPL standings",
      session_id: "uuid-123",
      locale: "en",
    };
    expect(req.session_id).toBe("uuid-123");
    expect(req.locale).toBe("en");
  });

  test("ChatSSE metadata has ai_generated flag", () => {
    const meta: ChatSSEMetadata = {
      intent: "stat_lookup",
      entities: [{ name: "Son Heung-min", type: "player", confidence: 0.95 }],
      language: "ko",
      ai_generated: true,
    };
    expect(meta.ai_generated).toBe(true);
    expect(meta.entities.length).toBeGreaterThan(0);
  });

  test("ChatSSE done event includes latency", () => {
    const done: ChatSSEDone = {
      session_id: "s-1",
      message_id: "m-1",
      model: "claude-sonnet-4-20250514",
      latency_ms: 1234,
    };
    expect(done.latency_ms).toBeGreaterThan(0);
  });
});

test.describe("Search Edge Function schema", () => {
  test("SearchRequest has required query field", () => {
    const req: SearchRequest = { query: "EPL standings" };
    expect(req.query).toBeTruthy();
  });

  test("SearchResponse has results and query_time_ms", () => {
    const res: SearchResponse = {
      results: [
        {
          doc_id: "d-1",
          title: "EPL standings 2025-26",
          snippet: "Manchester City leads...",
          similarity: 0.85,
          doc_type: "league_standing",
        },
      ],
      query_time_ms: 42,
    };
    expect(res.results.length).toBe(1);
    expect(res.query_time_ms).toBeGreaterThanOrEqual(0);
    expect(res.results[0].similarity).toBeLessThanOrEqual(1);
  });
});

test.describe("Parse-Rumors Edge Function schema", () => {
  test("ParseRumorsRequest defaults (no article_ids)", () => {
    const req: ParseRumorsRequest = { max_articles: 10 };
    expect(req.max_articles).toBe(10);
    expect(req.article_ids).toBeUndefined();
  });

  test("ParseRumorsResponse has all counter fields", () => {
    const res: ParseRumorsResponse = {
      parsed_count: 5,
      rumors_created: 2,
      rumors_updated: 1,
      sources_created: 3,
      errors: [{ article_id: "a-1", error: "Player not found" }],
    };
    expect(res.parsed_count).toBe(5);
    expect(res.errors.length).toBe(1);
  });
});

test.describe("Simulate-Transfer Edge Function schema", () => {
  test("SimulateTransferRequest has required IDs", () => {
    const req: SimulateTransferRequest = {
      player_id: "p-1",
      target_team_id: "t-1",
    };
    expect(req.player_id).toBeTruthy();
    expect(req.target_team_id).toBeTruthy();
  });

  test("TransferSimulationResult has all required fields", () => {
    const result: TransferSimulationResult = {
      team_strength_change: { before: 75, after: 80, delta: 5 },
      formation_impact: {
        current_formation: "4-3-3",
        suggested_formation: "4-2-3-1",
        analysis: "Player fits as a left winger.",
      },
      position_fit: { score: 85, reasoning: "Natural left-wing position." },
      salary_feasibility: {
        assessment: "feasible",
        reasoning: "Within wage cap.",
      },
      overall_rating: 82,
      summary: "Good transfer fit.",
      caveats: ["Limited recent data"],
    };
    expect(result.overall_rating).toBeGreaterThanOrEqual(0);
    expect(result.overall_rating).toBeLessThanOrEqual(100);
    expect(result.team_strength_change.delta).toBe(
      result.team_strength_change.after - result.team_strength_change.before
    );
    expect(["feasible", "stretch", "unlikely"]).toContain(
      result.salary_feasibility.assessment
    );
  });
});

test.describe("Simulate-Match Edge Function schema", () => {
  test("SimulateMatchRequest has required team IDs", () => {
    const req: SimulateMatchRequest = {
      home_team_id: "t-home",
      away_team_id: "t-away",
    };
    expect(req.home_team_id).toBeTruthy();
    expect(req.away_team_id).toBeTruthy();
  });

  test("MatchSimulationResult probabilities sum to 100", () => {
    const result: MatchSimulationResult = {
      predicted_score: { home: 2, away: 1 },
      win_probability: { home: 45, draw: 30, away: 25 },
      key_factors: ["Home advantage", "Recent form"],
      head_to_head_analysis: "Home team won 3 of last 5.",
      form_analysis: { home: "WWDLW", away: "LDWWL" },
      disclaimer:
        "이 예측은 통계 데이터 기반의 팬 엔터테인먼트 콘텐츠입니다.",
    };
    const totalProb =
      result.win_probability.home +
      result.win_probability.draw +
      result.win_probability.away;
    expect(totalProb).toBe(100);
    expect(result.disclaimer).toBeTruthy();
    expect(result.key_factors.length).toBeGreaterThan(0);
  });

  test("MatchSimulationResult scores are non-negative", () => {
    const result: MatchSimulationResult = {
      predicted_score: { home: 0, away: 0 },
      win_probability: { home: 30, draw: 40, away: 30 },
      key_factors: [],
      head_to_head_analysis: "No data",
      form_analysis: { home: "N/A", away: "N/A" },
      disclaimer: "For entertainment only.",
    };
    expect(result.predicted_score.home).toBeGreaterThanOrEqual(0);
    expect(result.predicted_score.away).toBeGreaterThanOrEqual(0);
  });
});
