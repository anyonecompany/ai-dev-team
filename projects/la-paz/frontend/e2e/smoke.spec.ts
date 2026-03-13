import { test, expect } from "@playwright/test";

/**
 * Smoke tests: verify that major pages load successfully
 * and render their core UI elements.
 */

const pages = [
  { path: "/", heading: "La Paz" },
  { path: "/matches", heading: /match/i },
  { path: "/transfers", heading: /이적|transfer/i },
  { path: "/standings", heading: /순위|standing/i },
  { path: "/chat", heading: /La Paz AI|축구/i },
  { path: "/simulate/transfer", heading: /이적 시뮬레이션|transfer/i },
  { path: "/simulate/match", heading: /경기 예측|match/i },
  { path: "/teams", heading: /팀|team/i },
];

test.describe("Smoke tests", () => {
  for (const { path, heading } of pages) {
    test(`page ${path} loads and renders core content`, async ({ page }) => {
      const response = await page.goto(path, { waitUntil: "domcontentloaded" });
      expect(response?.status()).toBeLessThan(400);
      await expect(page.getByText(heading).first()).toBeVisible({ timeout: 10_000 });
    });
  }

  test("header is present on home page", async ({ page }) => {
    await page.goto("/", { waitUntil: "domcontentloaded" });
    await expect(page.locator("header")).toBeVisible();
  });

  test("footer is present on home page", async ({ page }) => {
    await page.goto("/", { waitUntil: "domcontentloaded" });
    await expect(page.locator("footer")).toBeVisible();
  });
});
