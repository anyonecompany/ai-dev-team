import { test, expect } from "@playwright/test";

test.describe("AI disclaimer (chat page)", () => {
  test("chat page shows AI-related disclaimer text", async ({ page }) => {
    await page.goto("/chat", { waitUntil: "domcontentloaded" });

    // The chat page should show the "La Paz AI" heading indicating AI service
    await expect(page.getByText("La Paz AI")).toBeVisible({ timeout: 10_000 });

    // Check for AI-related text (either Korean or English)
    const aiIndicators = page.getByText(/AI|인공지능/);
    await expect(aiIndicators.first()).toBeVisible();
  });

  test("chat page has Powered by RAG disclaimer", async ({ page }) => {
    await page.goto("/chat", { waitUntil: "domcontentloaded" });
    await expect(page.getByText("Powered by RAG + Claude API")).toBeVisible();
  });
});

test.describe("AI disclaimer (transfer simulation page)", () => {
  test("transfer sim page loads with simulation heading", async ({ page }) => {
    await page.goto("/simulate/transfer", { waitUntil: "domcontentloaded" });
    await expect(page.getByText(/이적 시뮬레이션|Transfer Simulation/i)).toBeVisible({
      timeout: 10_000,
    });
  });

  test("transfer sim page shows placeholder guidance text", async ({ page }) => {
    await page.goto("/simulate/transfer", { waitUntil: "domcontentloaded" });
    // Before running a simulation, guidance text is shown
    await expect(
      page.getByText(/선수와 팀을 선택|Select a player/i)
    ).toBeVisible();
  });
});

test.describe("AI disclaimer (match simulation page)", () => {
  test("match sim page loads correctly", async ({ page }) => {
    await page.goto("/simulate/match", { waitUntil: "domcontentloaded" });
    await expect(page.getByText(/경기 예측|Match Prediction/i)).toBeVisible({
      timeout: 10_000,
    });
  });
});
