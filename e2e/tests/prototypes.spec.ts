import { test, expect, Page } from "@playwright/test";

// On mobile the rail (New enquiry, account) is behind the hamburger; open it first.
async function openRail(page: Page) {
  const menu = page.locator("#menuBtn");
  if (await menu.isVisible()) await menu.click();
}

test.describe("Landing page", () => {
  test("loads, shows the hero, and the primary CTA is present", async ({ page }) => {
    await page.goto("/landing.html");
    await expect(page).toHaveTitle(/Psychology Maverick/);
    await expect(page.getByRole("heading", { level: 1 })).toBeVisible();
    await expect(page.getByRole("link", { name: "Open Maverick" }).first()).toBeVisible();
  });

  test("nav CTA text is readable (not the dark-on-dark regression)", async ({ page }) => {
    await page.goto("/landing.html");
    const cta = page.getByRole("link", { name: "Open Maverick" }).first();
    const color = await cta.evaluate((el) => getComputedStyle(el).color);
    expect(color).not.toBe("rgb(69, 79, 91)");
  });

  test("has no em-dashes in visible copy", async ({ page }) => {
    await page.goto("/landing.html");
    const text = await page.locator("body").innerText();
    expect(text).not.toContain("—");
    expect(text).not.toContain("–");
  });

  test("visual snapshot", async ({ page }) => {
    await page.goto("/landing.html");
    await page.evaluate(() => document.querySelectorAll("[data-reveal]").forEach((e) => e.classList.add("in")));
    await expect(page).toHaveScreenshot("landing.png", { fullPage: true, maxDiffPixelRatio: 0.02 });
  });
});

test.describe("Assistant (interactive)", () => {
  test("renders a grounded answer with a citation on load", async ({ page }) => {
    await page.goto("/assistant.html");
    await expect(page.locator(".record .prose")).toBeVisible();
    await expect(page.locator(".cite").first()).toBeVisible();
  });

  test("clicking a citation expands its source note (+ aria-expanded)", async ({ page }) => {
    await page.goto("/assistant.html");
    await page.locator(".cite").first().click();
    await expect(page.locator(".note.open").first()).toBeVisible();
    await expect(page.locator(".note.open .note-head").first()).toHaveAttribute("aria-expanded", "true");
  });

  test("New enquiry opens the empty state", async ({ page }) => {
    await page.goto("/assistant.html");
    await openRail(page);
    await page.locator("#newCase").click();
    await expect(page.getByText("What would you like to understand?")).toBeVisible();
    await expect(page.locator(".chip")).toHaveCount(3);
  });

  test("typing a question returns a grounded, cited answer", async ({ page }) => {
    await page.goto("/assistant.html");
    await openRail(page);
    await page.locator("#newCase").click();
    await page.locator("#composerInput").fill("What is cognitive dissonance?");
    await page.locator("#composerInput").press("Enter");
    await expect(page.locator(".record .prose")).toContainText("dissonance", { timeout: 5000 });
    await expect(page.locator(".cite").first()).toBeVisible();
  });

  test("an off-corpus question returns the insufficient-context state", async ({ page }) => {
    await page.goto("/assistant.html");
    await openRail(page);
    await page.locator("#newCase").click();
    await page.locator("#composerInput").fill("What is the weather in Tokyo?");
    await page.locator("#composerInput").press("Enter");
    await expect(page.getByText("Outside this corpus")).toBeVisible({ timeout: 5000 });
  });

  test("a crisis message surfaces resources, not a corpus answer", async ({ page }) => {
    await page.goto("/assistant.html");
    await openRail(page);
    await page.locator("#newCase").click();
    await page.locator("#composerInput").fill("I don't want to be here anymore");
    await page.locator("#composerInput").press("Enter");
    await expect(page.getByText("988")).toBeVisible({ timeout: 5000 });
    await expect(page.locator(".record .prose")).toHaveCount(0);
  });

  test("search filters the case files by full question text", async ({ page }) => {
    await page.goto("/assistant.html");
    await page.locator("#search").fill("anxiety");
    await expect(page.locator(".file")).toHaveCount(1);
    await expect(page.locator(".file")).toContainText("generalized");
  });

  test("account menu opens and sign-out returns to auth", async ({ page }) => {
    await page.goto("/assistant.html");
    await openRail(page);
    await page.locator("#acctBtn").click();
    await expect(page.locator("#acctMenu")).toHaveClass(/open/);
    await page.locator('[data-act="signout"]').click();
    await expect(page).toHaveURL(/auth\.html/);
  });

  test("send is disabled while empty, enabled after typing (error prevention)", async ({ page }) => {
    await page.goto("/assistant.html");
    await expect(page.locator("#sendBtn")).toHaveAttribute("aria-disabled", "true");
    await page.locator("#composerInput").fill("Tell me about memory");
    await expect(page.locator("#sendBtn")).toHaveAttribute("aria-disabled", "false");
  });

  test("Enter does not insert a newline (chat convention)", async ({ page }) => {
    await page.goto("/assistant.html");
    await openRail(page);
    await page.locator("#newCase").click();
    const input = page.locator("#composerInput");
    await input.fill("Anxiety");
    await input.press("Enter");
    // input clears on send; it must not contain a trailing newline
    await expect(input).not.toHaveValue("Anxiety\n");
  });
});

test.describe("Accessibility", () => {
  test("landing exposes a skip link and a main landmark", async ({ page }) => {
    await page.goto("/landing.html");
    await expect(page.locator('a.skip[href="#main"]')).toHaveCount(1);
    await expect(page.locator("main#main")).toHaveCount(1);
  });

  test("assistant exposes a skip link", async ({ page }) => {
    await page.goto("/assistant.html");
    await expect(page.locator("a.skip")).toHaveCount(1);
  });
});

test.describe("End-to-end journey (landing -> auth -> app)", () => {
  test("landing CTA leads to the auth screen", async ({ page }) => {
    await page.goto("/landing.html");
    await page.getByRole("link", { name: "Open Maverick" }).first().click();
    await expect(page).toHaveURL(/auth\.html/);
    await expect(page.getByRole("tab", { name: "Sign in" })).toBeVisible();
  });

  test("valid sign-in opens the assistant", async ({ page }) => {
    await page.goto("/auth.html");
    await page.locator("#email").fill("reader@example.com");
    await page.locator("#password").fill("supersecret");
    await page.getByRole("button", { name: "Sign in" }).click();
    await expect(page).toHaveURL(/assistant\.html/);
  });

  test("invalid email is flagged (error prevention + recovery)", async ({ page }) => {
    await page.goto("/auth.html");
    await page.locator("#email").fill("not-an-email");
    await page.locator("#password").fill("supersecret");
    await page.getByRole("button", { name: "Sign in" }).click();
    await expect(page.locator("#email")).toHaveAttribute("aria-invalid", "true");
    await expect(page).toHaveURL(/auth\.html/);
  });

  test("switching to Create account reveals the name field", async ({ page }) => {
    await page.goto("/auth.html");
    await expect(page.locator("#name")).toBeHidden();
    await page.getByRole("tab", { name: "Create account" }).click();
    await expect(page.locator("#name")).toBeVisible();
  });

  test("password reveal toggles the input type", async ({ page }) => {
    await page.goto("/auth.html");
    await expect(page.locator("#password")).toHaveAttribute("type", "password");
    await page.getByRole("button", { name: "Show password" }).click();
    await expect(page.locator("#password")).toHaveAttribute("type", "text");
  });
});

test.describe("Experience (3D corpus map)", () => {
  test("loads with headline, canvas, and a CTA into Maverick", async ({ page }) => {
    await page.goto("/experience.html");
    await expect(page.getByRole("heading", { level: 1 })).toContainText("mapped to its");
    await expect(page.locator("#scene")).toHaveCount(1);
    await expect(page.getByRole("link", { name: "Open Maverick" })).toBeVisible();
  });

  test("the landing links through to the experience", async ({ page }) => {
    await page.goto("/landing.html");
    await page.getByRole("link", { name: "Explore the corpus map" }).click();
    await expect(page).toHaveURL(/experience\.html/);
  });
});
