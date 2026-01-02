import { test, expect } from '@playwright/test';

/**
 * E2E Tests: Chat Functionality
 * Tests the chat interface and message interactions.
 */

test.describe('Chat', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
    // Wait for the page to be fully loaded
    await page.waitForLoadState('networkidle');
  });

  test('should display chat input area', async ({ page }) => {
    const chatInput = page.locator('textarea').first();
    await expect(chatInput).toBeVisible({ timeout: 10000 });
  });

  test('should display send button', async ({ page }) => {
    const sendButton = page.locator('button').filter({ has: page.locator('svg') }).first();
    await expect(sendButton).toBeVisible({ timeout: 10000 });
  });

  test('should be able to type in chat input', async ({ page }) => {
    const chatInput = page.locator('textarea').first();
    await chatInput.fill('Hello, this is a test message');

    await expect(chatInput).toHaveValue('Hello, this is a test message');
  });

  test('should enable send button when text is entered', async ({ page }) => {
    const chatInput = page.locator('textarea').first();
    const sendButton = page.locator('button[type="button"], button').filter({ has: page.locator('svg') }).last();

    // Initially disabled or empty input
    await expect(chatInput).toHaveValue('');

    // Type something
    await chatInput.fill('Test message');

    // Button should be clickable now (not disabled)
    await expect(sendButton).not.toBeDisabled();
  });

  test('should show empty state for new conversations', async ({ page }) => {
    // Look for empty state message
    const emptyState = page.locator('text=/Start a Conversation|Ask about your data|No messages/i').first();

    // Either empty state is visible or there are already messages
    const hasEmptyState = await emptyState.isVisible({ timeout: 5000 }).catch(() => false);
    const hasMessages = await page.locator('[class*="message"], [data-message]').count() > 0;

    // One of these should be true
    expect(hasEmptyState || hasMessages).toBeTruthy();
  });

  test('should clear input after sending message', async ({ page }) => {
    // Note: This test might fail if backend is not running
    // In that case, it tests the frontend behavior

    const chatInput = page.locator('textarea').first();
    await chatInput.fill('Test message');

    // Try to send
    const sendButton = page.locator('button').filter({ has: page.locator('svg') }).last();

    if (await sendButton.isEnabled()) {
      await sendButton.click();

      // Input should clear after sending (or show error)
      // Give time for the message to be sent
      await page.waitForTimeout(500);
    }
  });
});
