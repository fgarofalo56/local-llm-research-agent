/**
 * Keyboard Shortcuts Hook
 * Phase 2.5: Advanced Features & Polish
 *
 * Global keyboard shortcuts for power users.
 */

import { useEffect, useCallback, useState } from 'react';
import { useNavigate } from 'react-router-dom';

export interface KeyboardShortcut {
  key: string;
  modifier?: 'ctrl' | 'alt' | 'shift' | 'meta';
  description: string;
  action: () => void;
  category: 'Navigation' | 'Actions' | 'Dialog';
}

export function useKeyboardShortcuts() {
  const navigate = useNavigate();
  const [showShortcutsDialog, setShowShortcutsDialog] = useState(false);

  const shortcuts: KeyboardShortcut[] = [
    // Navigation
    {
      key: 'h',
      modifier: 'alt',
      description: 'Go to Chat (Home)',
      action: () => navigate('/chat'),
      category: 'Navigation',
    },
    {
      key: 'd',
      modifier: 'alt',
      description: 'Go to Documents',
      action: () => navigate('/documents'),
      category: 'Navigation',
    },
    {
      key: 'b',
      modifier: 'alt',
      description: 'Go to Dashboards',
      action: () => navigate('/dashboards'),
      category: 'Navigation',
    },
    {
      key: 'q',
      modifier: 'alt',
      description: 'Go to Query History',
      action: () => navigate('/queries'),
      category: 'Navigation',
    },
    {
      key: 'm',
      modifier: 'alt',
      description: 'Go to MCP Servers',
      action: () => navigate('/mcp-servers'),
      category: 'Navigation',
    },
    {
      key: 's',
      modifier: 'alt',
      description: 'Go to Settings',
      action: () => navigate('/settings'),
      category: 'Navigation',
    },
    // Actions
    {
      key: 'n',
      modifier: 'ctrl',
      description: 'New Conversation',
      action: () => navigate('/chat'),
      category: 'Actions',
    },
    {
      key: '/',
      description: 'Focus Chat Input',
      action: () => {
        const input = document.querySelector('[data-chat-input]') as HTMLTextAreaElement;
        input?.focus();
      },
      category: 'Actions',
    },
    {
      key: 'Escape',
      description: 'Close Dialog / Deselect',
      action: () => {
        // Close any open dialogs
        document.dispatchEvent(new CustomEvent('closeDialogs'));
      },
      category: 'Actions',
    },
    // Dialog
    {
      key: '?',
      description: 'Show Keyboard Shortcuts',
      action: () => setShowShortcutsDialog(true),
      category: 'Dialog',
    },
  ];

  const handleKeyDown = useCallback(
    (event: KeyboardEvent) => {
      // Don't trigger shortcuts when typing in inputs
      const target = event.target as HTMLElement;
      const isInput = target.tagName === 'INPUT' ||
                     target.tagName === 'TEXTAREA' ||
                     target.isContentEditable;

      // Allow certain shortcuts even in inputs
      const allowInInput = ['Escape', '?'];
      if (isInput && !allowInInput.includes(event.key)) {
        return;
      }

      for (const shortcut of shortcuts) {
        const keyMatches = event.key.toLowerCase() === shortcut.key.toLowerCase() ||
                          event.key === shortcut.key;

        let modifierMatches = true;
        if (shortcut.modifier) {
          switch (shortcut.modifier) {
            case 'ctrl':
              modifierMatches = event.ctrlKey || event.metaKey;
              break;
            case 'alt':
              modifierMatches = event.altKey;
              break;
            case 'shift':
              modifierMatches = event.shiftKey;
              break;
            case 'meta':
              modifierMatches = event.metaKey;
              break;
          }
        } else {
          // If no modifier specified, ensure none are pressed (except shift for special chars like ?)
          modifierMatches = !event.ctrlKey && !event.altKey && !event.metaKey;
        }

        if (keyMatches && modifierMatches) {
          event.preventDefault();
          shortcut.action();
          break;
        }
      }
    },
    [shortcuts]
  );

  useEffect(() => {
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [handleKeyDown]);

  return {
    shortcuts,
    showShortcutsDialog,
    setShowShortcutsDialog,
    openShortcutsDialog: () => setShowShortcutsDialog(true),
    closeShortcutsDialog: () => setShowShortcutsDialog(false),
  };
}

export default useKeyboardShortcuts;
