import { defineConfig } from "@playwright/test";
import { resolve } from "node:path";
export default defineConfig({
  testDir: "tests/e2e",
  timeout: 60000,
  use: {
    baseURL: "http://127.0.0.1:3000",
    headless: true,
    screenshot: "only-on-failure",
  },
  webServer: {
    command: "npm start",
    url: "http://127.0.0.1:3000/health",
    reuseExistingServer: false,
    env: { ARENA_DATA_DIR: resolve("evidence/e2e-data"), ENABLE_INTERNAL_TEST_MODE: "false" },
    timeout: 60000,
  },
  reporter: [["list"], ["json", { outputFile: "evidence/playwright.json" }]],
});
