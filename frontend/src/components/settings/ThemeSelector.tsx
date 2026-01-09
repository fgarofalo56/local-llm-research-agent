/**
 * Theme Selector Component
 * Phase 2.5: Advanced Features & Polish
 *
 * Allows users to select from theme presets or use light/dark/system mode.
 */

import { useState } from 'react';
import { Check, Moon, Palette, Sun, Monitor, Trash2 } from 'lucide-react';
import { useTheme } from '../../contexts/ThemeContext';
import type { ThemePreset } from '../../lib/themes';
import {
  applyThemePreset,
  deleteCustomTheme,
  getAllThemes,
  getThemePreset,
  themePresets,
  saveCustomTheme,
} from '../../lib/themes';
import { Button } from '../ui/Button';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/Card';
import { CustomThemeBuilder } from './CustomThemeBuilder';

interface ThemeSelectorProps {
  showCustomBuilder?: boolean;
}

export function ThemeSelector({ showCustomBuilder = false }: ThemeSelectorProps) {
  const { theme, setTheme, resolvedTheme } = useTheme();
  const [selectedPreset, setSelectedPreset] = useState<string>(() => {
    return localStorage.getItem('themePreset') || 'default-dark';
  });
  const [customThemes, setCustomThemes] = useState(() => {
    try {
      const stored = localStorage.getItem('customThemes');
      return stored ? JSON.parse(stored) : [];
    } catch {
      return [];
    }
  });

  const handleModeChange = (mode: 'light' | 'dark' | 'system') => {
    setTheme(mode);

    // Apply appropriate preset based on mode
    if (mode === 'light') {
      const lightPreset = getThemePreset('default-light');
      if (lightPreset) {
        applyThemePreset(lightPreset);
        setSelectedPreset('default-light');
        localStorage.setItem('themePreset', 'default-light');
      }
    } else if (mode === 'dark') {
      const darkPreset = getThemePreset('default-dark');
      if (darkPreset) {
        applyThemePreset(darkPreset);
        setSelectedPreset('default-dark');
        localStorage.setItem('themePreset', 'default-dark');
      }
    }
    // System mode will use the appropriate default based on system preference
  };

  const handlePresetSelect = (preset: ThemePreset) => {
    applyThemePreset(preset);
    setSelectedPreset(preset.id);
    localStorage.setItem('themePreset', preset.id);

    // Also update the theme mode to match the preset
    setTheme(preset.isDark ? 'dark' : 'light');
  };

  const handleDeleteCustomTheme = (id: string) => {
    deleteCustomTheme(id);
    setCustomThemes(getAllThemes().filter((t: ThemePreset) => t.id.startsWith('custom-')));

    // If we deleted the currently selected theme, reset to default
    if (selectedPreset === id) {
      const defaultPreset = getThemePreset('default-dark');
      if (defaultPreset) {
        handlePresetSelect(defaultPreset);
      }
    }
  };

  const handleSaveCustomTheme = (theme: Omit<ThemePreset, 'id' | 'description'>) => {
    saveCustomTheme(theme.colors, theme.name);
    setCustomThemes(getAllThemes().filter((t: ThemePreset) => t.id.startsWith('custom-')));
  };

  const allThemes = [...themePresets, ...customThemes];
  const darkThemes = allThemes.filter((t) => t.isDark);
  const lightThemes = allThemes.filter((t) => !t.isDark);

  return (
    <div className="space-y-6">
      {/* Mode Toggle */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Palette className="h-5 w-5" />
            Appearance Mode
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex gap-2">
            <Button
              variant={theme === 'light' ? 'default' : 'outline'}
              onClick={() => handleModeChange('light')}
              className="flex-1"
            >
              <Sun className="h-4 w-4 mr-2" />
              Light
            </Button>
            <Button
              variant={theme === 'dark' ? 'default' : 'outline'}
              onClick={() => handleModeChange('dark')}
              className="flex-1"
            >
              <Moon className="h-4 w-4 mr-2" />
              Dark
            </Button>
            <Button
              variant={theme === 'system' ? 'default' : 'outline'}
              onClick={() => handleModeChange('system')}
              className="flex-1"
            >
              <Monitor className="h-4 w-4 mr-2" />
              System
            </Button>
          </div>
          {theme === 'system' && (
            <p className="text-sm text-muted-foreground mt-2">
              Currently using: {resolvedTheme === 'dark' ? 'Dark' : 'Light'} (based on system preference)
            </p>
          )}
        </CardContent>
      </Card>

      {/* Dark Theme Presets */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Moon className="h-5 w-5" />
            Dark Themes
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            {darkThemes.map((preset) => (
              <ThemePresetCard
                key={preset.id}
                preset={preset}
                isSelected={selectedPreset === preset.id}
                onSelect={() => handlePresetSelect(preset)}
                onDelete={preset.id.startsWith('custom-') ? () => handleDeleteCustomTheme(preset.id) : undefined}
              />
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Light Theme Presets */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Sun className="h-5 w-5" />
            Light Themes
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            {lightThemes.map((preset) => (
              <ThemePresetCard
                key={preset.id}
                preset={preset}
                isSelected={selectedPreset === preset.id}
                onSelect={() => handlePresetSelect(preset)}
                onDelete={preset.id.startsWith('custom-') ? () => handleDeleteCustomTheme(preset.id) : undefined}
              />
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Custom Theme Builder (optional) */}
      {showCustomBuilder && (
        <Card>
          <CardHeader>
            <CardTitle>Custom Theme Builder</CardTitle>
          </CardHeader>
          <CardContent>
            <CustomThemeBuilder onSave={handleSaveCustomTheme} />
          </CardContent>
        </Card>
      )}
    </div>
  );
}

interface ThemePresetCardProps {
  preset: ThemePreset;
  isSelected: boolean;
  onSelect: () => void;
  onDelete?: () => void;
}

function ThemePresetCard({ preset, isSelected, onSelect, onDelete }: ThemePresetCardProps) {
  // Parse HSL values for preview
  const bgParts = preset.colors.background.split(' ');
  const primaryParts = preset.colors.primary.split(' ');
  const accentParts = preset.colors.accent.split(' ');

  const bgColor = `hsl(${bgParts[0]}, ${bgParts[1]}, ${bgParts[2]})`;
  const primaryColor = `hsl(${primaryParts[0]}, ${primaryParts[1]}, ${primaryParts[2]})`;
  const accentColor = `hsl(${accentParts[0]}, ${accentParts[1]}, ${accentParts[2]})`;

  return (
    <button
      onClick={onSelect}
      className={`relative p-3 rounded-lg border-2 transition-all text-left ${
        isSelected ? 'border-primary ring-2 ring-primary/20' : 'border-border hover:border-primary/50'
      }`}
    >
      {/* Color Preview */}
      <div className="flex gap-1 mb-2">
        <div
          className="w-6 h-6 rounded-full border border-white/20"
          style={{ backgroundColor: bgColor }}
          title="Background"
        />
        <div
          className="w-6 h-6 rounded-full border border-white/20"
          style={{ backgroundColor: primaryColor }}
          title="Primary"
        />
        <div
          className="w-6 h-6 rounded-full border border-white/20"
          style={{ backgroundColor: accentColor }}
          title="Accent"
        />
      </div>

      {/* Name & Description */}
      <div className="font-medium text-sm">{preset.name}</div>
      <div className="text-xs text-muted-foreground truncate">{preset.description}</div>

      {/* Selected Indicator */}
      {isSelected && (
        <div className="absolute top-2 right-2 w-5 h-5 bg-primary rounded-full flex items-center justify-center">
          <Check className="h-3 w-3 text-primary-foreground" />
        </div>
      )}

      {/* Delete Button for Custom Themes */}
      {onDelete && (
        <button
          onClick={(e) => {
            e.stopPropagation();
            onDelete();
          }}
          className="absolute bottom-2 right-2 p-1 rounded hover:bg-destructive/20 text-muted-foreground hover:text-destructive"
          title="Delete custom theme"
        >
          <Trash2 className="h-3 w-3" />
        </button>
      )}
    </button>
  );
}

export default ThemeSelector;