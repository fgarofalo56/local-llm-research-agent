/**
 * Keyboard Shortcuts Dialog
 * Phase 2.5: Advanced Features & Polish
 *
 * Displays all available keyboard shortcuts.
 */

import { Keyboard, X } from 'lucide-react';
import { Button } from '../ui/Button';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/Card';
import type { KeyboardShortcut } from '../../hooks/useKeyboardShortcuts';

interface KeyboardShortcutsDialogProps {
  shortcuts: KeyboardShortcut[];
  onClose: () => void;
}

export function KeyboardShortcutsDialog({ shortcuts, onClose }: KeyboardShortcutsDialogProps) {
  const categories = ['Navigation', 'Actions', 'Dialog'] as const;

  const formatKey = (shortcut: KeyboardShortcut) => {
    const parts: string[] = [];

    if (shortcut.modifier) {
      switch (shortcut.modifier) {
        case 'ctrl':
          parts.push(navigator.platform.includes('Mac') ? '⌘' : 'Ctrl');
          break;
        case 'alt':
          parts.push(navigator.platform.includes('Mac') ? '⌥' : 'Alt');
          break;
        case 'shift':
          parts.push('⇧');
          break;
        case 'meta':
          parts.push('⌘');
          break;
      }
    }

    // Format special keys
    let keyDisplay = shortcut.key;
    switch (shortcut.key.toLowerCase()) {
      case 'escape':
        keyDisplay = 'Esc';
        break;
      case 'enter':
        keyDisplay = '↵';
        break;
      case 'arrowup':
        keyDisplay = '↑';
        break;
      case 'arrowdown':
        keyDisplay = '↓';
        break;
      case 'arrowleft':
        keyDisplay = '←';
        break;
      case 'arrowright':
        keyDisplay = '→';
        break;
      default:
        keyDisplay = shortcut.key.toUpperCase();
    }

    parts.push(keyDisplay);
    return parts;
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <Card className="w-full max-w-lg max-h-[80vh] overflow-y-auto">
        <CardHeader className="flex flex-row items-center justify-between sticky top-0 bg-card z-10">
          <CardTitle className="flex items-center gap-2">
            <Keyboard className="h-5 w-5" />
            Keyboard Shortcuts
          </CardTitle>
          <Button variant="ghost" size="icon" onClick={onClose}>
            <X className="h-4 w-4" />
          </Button>
        </CardHeader>

        <CardContent className="space-y-6">
          {categories.map((category) => {
            const categoryShortcuts = shortcuts.filter((s) => s.category === category);
            if (categoryShortcuts.length === 0) return null;

            return (
              <div key={category}>
                <h3 className="text-sm font-semibold text-muted-foreground mb-3">
                  {category}
                </h3>
                <div className="space-y-2">
                  {categoryShortcuts.map((shortcut, index) => (
                    <div
                      key={index}
                      className="flex items-center justify-between py-2 border-b border-border last:border-0"
                    >
                      <span className="text-sm">{shortcut.description}</span>
                      <div className="flex gap-1">
                        {formatKey(shortcut).map((key, i) => (
                          <kbd
                            key={i}
                            className="px-2 py-1 rounded bg-muted text-muted-foreground font-mono text-xs min-w-[28px] text-center"
                          >
                            {key}
                          </kbd>
                        ))}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            );
          })}

          <div className="text-center pt-4 text-sm text-muted-foreground">
            Press <kbd className="px-1.5 py-0.5 rounded bg-muted font-mono text-xs">?</kbd> anytime to show this dialog
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

export default KeyboardShortcutsDialog;
