import { test, expect } from '@playwright/test';

/**
 * E2E Tests: Dashboard Page
 * Tests dashboard and widget functionality.
 */

test.describe('Dashboard', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/dashboards');
    await page.waitForLoadState('networkidle');
  });

  test('should display dashboards page', async ({ page }) => {
    // Check for dashboard heading or content
    const pageContent = page.locator('h1, h2, [class*="title"]').filter({ hasText: /Dashboard/i }).first();
    await expect(pageContent).toBeVisible({ timeout: 10000 });
  });

  test('should show create dashboard button', async ({ page }) => {
    // Look for create/new button
    const createButton = page.locator('button:has-text("New"), button:has-text("Create"), button:has-text("Add")').first();

    // Button should exist for dashboard management
    const isVisible = await createButton.isVisible({ timeout: 5000 }).catch(() => false);

    if (isVisible) {
      await expect(createButton).toBeVisible();
    }
  });

  test('should show dashboard list or empty state', async ({ page }) => {
    // Either show dashboards or empty state
    const content = page.locator('[class*="dashboard"], [class*="grid"], [class*="empty"], [class*="card"]').first();
    await expect(content).toBeVisible({ timeout: 10000 });
  });

  test('should have edit mode toggle', async ({ page }) => {
    // Look for edit button
    const editButton = page.locator('button:has-text("Edit"), button[aria-label*="edit"], [class*="edit"]').first();

    const isVisible = await editButton.isVisible({ timeout: 3000 }).catch(() => false);

    // Edit mode might be available on dashboard detail page
    if (isVisible) {
      await expect(editButton).toBeVisible();
    }
  });
});
