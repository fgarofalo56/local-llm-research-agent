import { test, expect } from '@playwright/test';

/**
 * E2E Tests: Settings Page
 * Tests settings and configuration functionality.
 */

test.describe('Settings', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/settings');
    await page.waitForLoadState('networkidle');
  });

  test('should display settings page', async ({ page }) => {
    // Check for settings heading
    const pageContent = page.locator('h1, h2, [class*="title"]').filter({ hasText: /Settings/i }).first();
    await expect(pageContent).toBeVisible({ timeout: 10000 });
  });

  test('should show theme options', async ({ page }) => {
    // Look for theme-related UI
    const themeSection = page.locator('text=/Theme|Appearance|Dark|Light/i').first();
    await expect(themeSection).toBeVisible({ timeout: 10000 });
  });

  test('should have provider configuration section', async ({ page }) => {
    // Look for provider/model settings
    const providerSection = page.locator('text=/Provider|Model|Ollama|LLM/i').first();
    await expect(providerSection).toBeVisible({ timeout: 10000 });
  });

  test('should have MCP server configuration', async ({ page }) => {
    // Look for MCP settings
    const mcpSection = page.locator('text=/MCP|Server|Database/i').first();
    await expect(mcpSection).toBeVisible({ timeout: 10000 });
  });

  test('theme toggle should be functional', async ({ page }) => {
    // Find theme toggle button (in header)
    const themeButton = page.locator('header button').first();

    if (await themeButton.isVisible()) {
      await themeButton.click();

      // Should show theme options
      const themeOptions = page.locator('text=/Light|Dark|System/i').first();
      await expect(themeOptions).toBeVisible({ timeout: 5000 });
    }
  });
});
