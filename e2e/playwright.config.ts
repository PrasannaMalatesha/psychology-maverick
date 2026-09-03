import { defineConfig, devices } from "@playwright/test";

// Real-browser tests for the Casebook prototypes. The webServer block serves
// design/prototype/ over HTTP so the landing page's embedded assistant iframe
// resolves. Swap baseURL to the Next.js dev server once the frontend is scaffolded.
export default defineConfig({
  testDir: "./tests",
  fullyParallel: true,
  reporter: [["list"], ["html", { open: "never" }]],
  use: {
    baseURL: "http://localhost:8752",
    trace: "on-first-retry",
    screenshot: "only-on-failure",
  },
  projects: [
    { name: "desktop-chromium", use: { ...devices["Desktop Chrome"] } },
    { name: "mobile-chromium", use: { ...devices["Pixel 7"] } },
  ],
  webServer: {
    command: "python3 -m http.server 8752 --directory ../design/prototype",
    url: "http://localhost:8752/landing.html",
    reuseExistingServer: true,
    timeout: 20000,
  },
});
