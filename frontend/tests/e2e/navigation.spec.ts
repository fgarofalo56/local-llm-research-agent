import { test, expect } from '@playwright/test';

/**
 * E2E Tests: Navigation
 * Tests basic navigation and page accessibility.
 */

test.describe('Navigation', () => {
  test('should load the home page', async ({ page }) => {
    await page.goto('/');

    // Check that the page loaded
    await expect(page).toHaveTitle(/Local LLM|Research/i);
  });

  test('should navigate to chat page', async ({ page }) => {
    await page.goto('/');

    // Look for chat-related UI elements
    const chatArea = page.locator('textarea, [placeholder*="ask"]').first();
    await expect(chatArea).toBeVisible({ timeout: 10000 });
  });

  test('should navigate to documents page', async ({ page }) => {
    await page.goto('/documents');

    // Check for documents page content
    await expect(page.locator('text=Documents').first()).toBeVisible({ timeout: 10000 });
  });

  test('should navigate to dashboards page', async ({ page }) => {
    await page.goto('/dashboards');

    // Check for dashboards page content
    await expect(page.locator('text=Dashboard').first()).toBeVisible({ timeout: 10000 });
  });

  test('should navigate to settings page', async ({ page }) => {
    await page.goto('/settings');

    // Check for settings page content
    await expect(page.locator('text=Settings').first()).toBeVisible({ timeout: 10000 });
  });

  test('sidebar navigation should work', async ({ page }) => {
    await page.goto('/');

    // Find sidebar
    const sidebar = page.locator('nav, aside, [role="navigation"]').first();

    if (await sidebar.isVisible()) {
      // Click documents link if visible
      const docsLink = page.locator('a[href="/documents"], button:has-text("Documents")').first();
      if (await docsLink.isVisible()) {
        await docsLink.click();
        await expect(page).toHaveURL(/\/documents/);
      }
    }
  });
});
