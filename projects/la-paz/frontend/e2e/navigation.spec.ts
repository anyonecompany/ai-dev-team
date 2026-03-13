import { test, expect } from "@playwright/test";

test.describe("Desktop navigation", () => {
  test.use({ viewport: { width: 1280, height: 720 } });

  const navLinks = [
    { label: "Matches", path: "/matches" },
    { label: "Transfers", path: "/transfers" },
    { label: "Standings", path: "/standings" },
    { label: "Home", path: "/" },
  ];

  for (const { label, path } of navLinks) {
    test(`header link "${label}" navigates to ${path}`, async ({ page }) => {
      await page.goto("/", { waitUntil: "domcontentloaded" });
      const nav = page.locator("header nav");
      await nav.getByText(label, { exact: true }).click();
      await page.waitForURL(`**${path}`);
      expect(page.url()).toContain(path);
    });
  }

  test("logo click navigates to home", async ({ page }) => {
    await page.goto("/matches", { waitUntil: "domcontentloaded" });
    await page.locator("header").getByText("La Paz").click();
    await page.waitForURL("**/");
    expect(new URL(page.url()).pathname).toBe("/");
  });

  test("search icon navigates to chat", async ({ page }) => {
    await page.goto("/", { waitUntil: "domcontentloaded" });
    await page.locator('header a[aria-label="검색"]').click();
    await page.waitForURL("**/chat");
    expect(page.url()).toContain("/chat");
  });
});

test.describe("Mobile navigation", () => {
  test.use({ viewport: { width: 375, height: 812 } });

  const mobileLinks = [
    { label: "Match", path: "/matches" },
    { label: "Trans", path: "/transfers" },
    { label: "Chat", path: "/chat" },
    { label: "Sim", path: "/simulate/transfer" },
    { label: "Home", path: "/" },
  ];

  for (const { label, path } of mobileLinks) {
    test(`mobile nav "${label}" navigates to ${path}`, async ({ page }) => {
      await page.goto("/", { waitUntil: "domcontentloaded" });
      const mobileNav = page.locator("nav.fixed");
      await mobileNav.getByText(label, { exact: true }).click();
      await page.waitForURL(`**${path}`);
      expect(page.url()).toContain(path);
    });
  }

  test("mobile nav is visible on small screens", async ({ page }) => {
    await page.goto("/", { waitUntil: "domcontentloaded" });
    await expect(page.locator("nav.fixed")).toBeVisible();
  });
});

test.describe("Language switch", () => {
  test("language toggle button exists", async ({ page }) => {
    await page.goto("/", { waitUntil: "domcontentloaded" });
    const langBtn = page.locator('button[aria-label="언어 전환"]');
    await expect(langBtn).toBeVisible();
  });
});
