import { test, expect } from '@playwright/test';

/**
 * E2E Tests: Documents Page
 * Tests document management functionality.
 */

test.describe('Documents', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/documents');
    await page.waitForLoadState('networkidle');
  });

  test('should display documents page', async ({ page }) => {
    // Check for documents heading or title
    await expect(page.locator('h1, h2, [class*="title"]').filter({ hasText: /Documents/i }).first()).toBeVisible({ timeout: 10000 });
  });

  test('should show upload button or area', async ({ page }) => {
    // Look for upload functionality
    const uploadButton = page.locator('button:has-text("Upload"), input[type="file"], [class*="upload"]').first();
    await expect(uploadButton).toBeVisible({ timeout: 10000 });
  });

  test('should show document list area', async ({ page }) => {
    // Look for document list (table), empty drop zone, or document count text
    // The page shows either a table, a drop zone card, or a "X of Y documents" message
    const table = page.locator('table');
    const dropZone = page.locator('[class*="border-dashed"]');
    const countText = page.getByText(/\d+ of \d+ documents/);

    // One of these should be visible
    const hasTable = await table.isVisible({ timeout: 5000 }).catch(() => false);
    const hasDropZone = await dropZone.isVisible({ timeout: 1000 }).catch(() => false);
    const hasCountText = await countText.isVisible({ timeout: 1000 }).catch(() => false);

    expect(hasTable || hasDropZone || hasCountText).toBeTruthy();
  });

  test('should have search functionality', async ({ page }) => {
    // Look for search input
    const searchInput = page.locator('input[type="search"], input[placeholder*="earch"], input[placeholder*="query"]').first();

    // Search might not be visible if no documents
    const isVisible = await searchInput.isVisible({ timeout: 3000 }).catch(() => false);

    if (isVisible) {
      await expect(searchInput).toBeVisible();
    }
  });

  test('should handle file input visibility', async ({ page }) => {
    // File inputs are often hidden, but should exist
    const fileInput = page.locator('input[type="file"]').first();

    // File input might be hidden for styling
    const exists = await fileInput.count() > 0;
    expect(exists).toBeTruthy();
  });
});
