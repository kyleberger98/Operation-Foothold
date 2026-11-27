// Playwright settings for the Gridline Command test suite. Run with `npm test` from the repository root.
// GAME=/path/to/gridline-command.html runs the suite against another copy of the game.
const { defineConfig } = require('@playwright/test');

module.exports = defineConfig({
  testDir: __dirname,
  testMatch: '*.spec.js',
  outputDir: '../test-results',
  timeout: 90_000,
  expect: { timeout: 15_000 },
  fullyParallel: true,
  workers: process.env.TEST_WORKERS ? +process.env.TEST_WORKERS : 2,
  retries: process.env.CI ? 1 : 0,   // a retried test still shows up as flaky in the report
  forbidOnly: !!process.env.CI,
  reporter: process.env.CI ? [['list'], ['github']] : 'list',
  use: {
    browserName: 'chromium',
    headless: true,
    launchOptions: { args: ['--use-gl=swiftshader', '--enable-webgl', '--ignore-gpu-blocklist'] },
    trace: 'retain-on-failure',
    screenshot: 'only-on-failure',
  },
});
