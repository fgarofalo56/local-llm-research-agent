import { useState } from 'react';
import { type ThemePreset, type ThemeColors, applyThemePreset, getThemePreset } from '../../lib/themes';
import { Button } from '../ui/Button';
import { Input } from '../ui/Input';
import { cn } from '../../lib/utils';

interface CustomThemeBuilderProps {
  onSave: (theme: Omit<ThemePreset, 'id' | 'description'>) => void;
  initialTheme?: ThemePreset;
}

const colorFields: (keyof ThemeColors)[] = [
  'background',
  'foreground',
  'primary',
  'secondary',
  'accent',
  'muted',
  'border',
];

export function CustomThemeBuilder({ onSave, initialTheme }: CustomThemeBuilderProps) {
  const [name, setName] = useState(initialTheme?.name || '');
  const [isDark, setIsDark] = useState(initialTheme?.isDark ?? true);
  const [colors, setColors] = useState<Partial<ThemeColors>>(
    initialTheme?.colors || {}
  );

  const handleColorChange = (key: keyof ThemeColors, value: string) => {
    setColors((prev) => ({ ...prev, [key]: value }));
  };

  const handlePreview = () => {
    const theme: ThemePreset = {
      id: 'custom-preview',
      name: name || 'Custom Preview',
      description: 'A temporary preview',
      isDark,
      colors: {
        ...getDefaultColors(isDark),
        ...colors,
      } as ThemeColors,
    };
    applyThemePreset(theme);
  };

  const handleSave = () => {
    onSave({
      name: name || 'Custom Theme',
      isDark,
      colors: {
        ...getDefaultColors(isDark),
        ...colors,
      } as ThemeColors,
    });
  };

  function getDefaultColors(isDark: boolean): ThemeColors {
    const preset = getThemePreset(isDark ? 'default-dark' : 'default-light');
    return preset!.colors;
  }

  function hexToHSL(hex: string): string {
    const r = parseInt(hex.slice(1, 3), 16) / 255;
    const g = parseInt(hex.slice(3, 5), 16) / 255;
    const b = parseInt(hex.slice(5, 7), 16) / 255;

    const max = Math.max(r, g, b);
    const min = Math.min(r, g, b);
    let h = 0;
    let s = 0;
    const l = (max + min) / 2;

    if (max !== min) {
      const d = max - min;
      s = l > 0.5 ? d / (2 - max - min) : d / (max + min);

      switch (max) {
        case r:
          h = ((g - b) / d + (g < b ? 6 : 0)) / 6;
          break;
        case g:
          h = ((b - r) / d + 2) / 6;
          break;
        case b:
          h = ((r - g) / d + 4) / 6;
          break;
      }
    }

    return `${Math.round(h * 360)} ${Math.round(s * 100)}% ${Math.round(l * 100)}%`;
  }

  return (
    <div className="space-y-6">
      <div>
        <label className="mb-1 block text-sm font-medium">Theme Name</label>
        <Input
          value={name}
          onChange={(e) => setName(e.target.value)}
          placeholder="My Custom Theme"
        />
      </div>

      <div className="flex items-center gap-4">
        <label className="text-sm font-medium">Base Mode:</label>
        <button
          onClick={() => setIsDark(true)}
          className={cn(
            'rounded-md px-3 py-1 text-sm',
            isDark ? 'bg-primary text-primary-foreground' : 'bg-muted'
          )}
        >
          Dark
        </button>
        <button
          onClick={() => setIsDark(false)}
          className={cn(
            'rounded-md px-3 py-1 text-sm',
            !isDark ? 'bg-primary text-primary-foreground' : 'bg-muted'
          )}
        >
          Light
        </button>
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        {colorFields.map((field) => (
          <div key={field}>
            <label className="mb-1 block text-sm font-medium capitalize">
              {field.replace(/([A-Z])/g, ' $1')}
            </label>
            <div className="flex gap-2">
              <Input
                value={colors[field] || ''}
                onChange={(e) => handleColorChange(field, e.target.value)}
                placeholder="e.g., 210 40% 98%"
              />
              <input
                type="color"
                onChange={(e) => {
                  const hsl = hexToHSL(e.target.value);
                  handleColorChange(field, hsl);
                }}
                className="h-10 w-10 cursor-pointer rounded border"
              />
            </div>
          </div>
        ))}
      </div>

      <div className="flex gap-2">
        <Button variant="outline" onClick={handlePreview}>
          Preview
        </Button>
        <Button onClick={handleSave}>Save Theme</Button>
      </div>
    </div>
  );
}
