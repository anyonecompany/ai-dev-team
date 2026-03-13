import { test, expect } from "@playwright/test";

test.describe("Dark theme", () => {
  test("default theme applies dark class", async ({ page }) => {
    await page.goto("/", { waitUntil: "domcontentloaded" });
    // next-themes defaults to system; we check that html element has a class
    // (either "dark" or "light" depending on system preference).
    const html = page.locator("html");
    const className = await html.getAttribute("class");
    expect(className).toBeTruthy();
  });

  test("theme toggle switches between dark and light", async ({ page }) => {
    await page.goto("/", { waitUntil: "domcontentloaded" });

    // Wait for next-themes to hydrate
    await page.waitForTimeout(500);

    const html = page.locator("html");
    const initialClass = await html.getAttribute("class");

    // Click theme toggle
    const themeBtn = page.locator('button[aria-label="라이트 모드"], button[aria-label="다크 모드"]');
    await themeBtn.first().click();

    // Wait for class change
    await page.waitForTimeout(300);
    const newClass = await html.getAttribute("class");

    // The class should have changed
    expect(newClass).not.toBe(initialClass);
  });

  test("theme toggle button has accessible label", async ({ page }) => {
    await page.goto("/", { waitUntil: "domcontentloaded" });
    await page.waitForTimeout(500);

    const themeBtn = page.locator('button[aria-label="라이트 모드"], button[aria-label="다크 모드"]');
    await expect(themeBtn.first()).toBeVisible();
  });
});
