import { test } from "@playwright/test";
test("S0 Smoke load", async ({ page }) => { await page.goto("/"); });
