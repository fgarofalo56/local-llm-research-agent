/**
 * Theme Presets & Configuration
 * Phase 2.5: Advanced Features & Polish
 *
 * Provides themed color presets beyond basic light/dark mode.
 */

export interface ThemeColors {
  background: string;
  foreground: string;
  card: string;
  cardForeground: string;
  primary: string;
  primaryForeground: string;
  secondary: string;
  secondaryForeground: string;
  muted: string;
  mutedForeground: string;
  accent: string;
  accentForeground: string;
  destructive: string;
  destructiveForeground: string;
  border: string;
  input: string;
  ring: string;
}

export interface ThemePreset {
  id: string;
  name: string;
  description: string;
  isDark: boolean;
  colors: ThemeColors;
}

// HSL values for CSS custom properties (without hsl() wrapper)
export const themePresets: ThemePreset[] = [
  {
    id: 'default-light',
    name: 'Light',
    description: 'Clean, bright interface',
    isDark: false,
    colors: {
      background: '0 0% 100%',
      foreground: '222.2 84% 4.9%',
      card: '0 0% 100%',
      cardForeground: '222.2 84% 4.9%',
      primary: '222.2 47.4% 11.2%',
      primaryForeground: '210 40% 98%',
      secondary: '210 40% 96.1%',
      secondaryForeground: '222.2 47.4% 11.2%',
      muted: '210 40% 96.1%',
      mutedForeground: '215.4 16.3% 46.9%',
      accent: '210 40% 96.1%',
      accentForeground: '222.2 47.4% 11.2%',
      destructive: '0 84.2% 60.2%',
      destructiveForeground: '210 40% 98%',
      border: '214.3 31.8% 91.4%',
      input: '214.3 31.8% 91.4%',
      ring: '222.2 84% 4.9%',
    },
  },
  {
    id: 'default-dark',
    name: 'Dark',
    description: 'Easy on the eyes',
    isDark: true,
    colors: {
      background: '222.2 84% 4.9%',
      foreground: '210 40% 98%',
      card: '222.2 84% 4.9%',
      cardForeground: '210 40% 98%',
      primary: '210 40% 98%',
      primaryForeground: '222.2 47.4% 11.2%',
      secondary: '217.2 32.6% 17.5%',
      secondaryForeground: '210 40% 98%',
      muted: '217.2 32.6% 17.5%',
      mutedForeground: '215 20.2% 65.1%',
      accent: '217.2 32.6% 17.5%',
      accentForeground: '210 40% 98%',
      destructive: '0 62.8% 30.6%',
      destructiveForeground: '210 40% 98%',
      border: '217.2 32.6% 17.5%',
      input: '217.2 32.6% 17.5%',
      ring: '212.7 26.8% 83.9%',
    },
  },
  {
    id: 'ocean',
    name: 'Ocean',
    description: 'Deep blue hues',
    isDark: true,
    colors: {
      background: '210 50% 10%',
      foreground: '200 30% 95%',
      card: '210 45% 12%',
      cardForeground: '200 30% 95%',
      primary: '200 80% 50%',
      primaryForeground: '210 50% 10%',
      secondary: '210 40% 20%',
      secondaryForeground: '200 30% 90%',
      muted: '210 35% 18%',
      mutedForeground: '200 20% 60%',
      accent: '185 70% 45%',
      accentForeground: '210 50% 10%',
      destructive: '0 70% 50%',
      destructiveForeground: '200 30% 95%',
      border: '210 35% 22%',
      input: '210 35% 18%',
      ring: '200 80% 50%',
    },
  },
  {
    id: 'forest',
    name: 'Forest',
    description: 'Natural greens',
    isDark: true,
    colors: {
      background: '150 30% 8%',
      foreground: '140 20% 92%',
      card: '150 28% 11%',
      cardForeground: '140 20% 92%',
      primary: '142 70% 45%',
      primaryForeground: '150 30% 8%',
      secondary: '150 25% 18%',
      secondaryForeground: '140 20% 88%',
      muted: '150 22% 15%',
      mutedForeground: '140 15% 55%',
      accent: '160 60% 40%',
      accentForeground: '150 30% 8%',
      destructive: '0 65% 45%',
      destructiveForeground: '140 20% 92%',
      border: '150 22% 20%',
      input: '150 22% 15%',
      ring: '142 70% 45%',
    },
  },
  {
    id: 'sunset',
    name: 'Sunset',
    description: 'Warm orange tones',
    isDark: true,
    colors: {
      background: '20 40% 8%',
      foreground: '30 30% 92%',
      card: '20 35% 11%',
      cardForeground: '30 30% 92%',
      primary: '25 90% 55%',
      primaryForeground: '20 40% 8%',
      secondary: '20 30% 18%',
      secondaryForeground: '30 30% 88%',
      muted: '20 25% 15%',
      mutedForeground: '25 20% 55%',
      accent: '35 85% 50%',
      accentForeground: '20 40% 8%',
      destructive: '0 70% 50%',
      destructiveForeground: '30 30% 92%',
      border: '20 25% 20%',
      input: '20 25% 15%',
      ring: '25 90% 55%',
    },
  },
  {
    id: 'lavender',
    name: 'Lavender',
    description: 'Soft purple aesthetic',
    isDark: false,
    colors: {
      background: '270 30% 98%',
      foreground: '270 50% 15%',
      card: '270 35% 96%',
      cardForeground: '270 50% 15%',
      primary: '270 60% 50%',
      primaryForeground: '270 30% 98%',
      secondary: '270 25% 92%',
      secondaryForeground: '270 45% 20%',
      muted: '270 20% 94%',
      mutedForeground: '270 20% 45%',
      accent: '280 55% 55%',
      accentForeground: '270 30% 98%',
      destructive: '0 75% 55%',
      destructiveForeground: '270 30% 98%',
      border: '270 25% 88%',
      input: '270 25% 90%',
      ring: '270 60% 50%',
    },
  },
  {
    id: 'midnight',
    name: 'Midnight',
    description: 'Deep purple night',
    isDark: true,
    colors: {
      background: '260 50% 6%',
      foreground: '260 20% 92%',
      card: '260 45% 9%',
      cardForeground: '260 20% 92%',
      primary: '260 70% 60%',
      primaryForeground: '260 50% 6%',
      secondary: '260 35% 16%',
      secondaryForeground: '260 20% 88%',
      muted: '260 30% 13%',
      mutedForeground: '260 15% 55%',
      accent: '280 60% 55%',
      accentForeground: '260 50% 6%',
      destructive: '0 60% 45%',
      destructiveForeground: '260 20% 92%',
      border: '260 30% 18%',
      input: '260 30% 13%',
      ring: '260 70% 60%',
    },
  },
  {
    id: 'rose',
    name: 'Rose',
    description: 'Elegant pink tones',
    isDark: false,
    colors: {
      background: '350 30% 98%',
      foreground: '350 50% 15%',
      card: '350 35% 96%',
      cardForeground: '350 50% 15%',
      primary: '350 70% 55%',
      primaryForeground: '350 30% 98%',
      secondary: '350 25% 92%',
      secondaryForeground: '350 45% 20%',
      muted: '350 20% 94%',
      mutedForeground: '350 20% 45%',
      accent: '340 65% 50%',
      accentForeground: '350 30% 98%',
      destructive: '0 75% 55%',
      destructiveForeground: '350 30% 98%',
      border: '350 25% 88%',
      input: '350 25% 90%',
      ring: '350 70% 55%',
    },
  },
];

/**
 * Apply a theme preset to the document
 */
export function applyThemePreset(preset: ThemePreset): void {
  const root = document.documentElement;

  // Set CSS custom properties
  root.style.setProperty('--background', preset.colors.background);
  root.style.setProperty('--foreground', preset.colors.foreground);
  root.style.setProperty('--card', preset.colors.card);
  root.style.setProperty('--card-foreground', preset.colors.cardForeground);
  root.style.setProperty('--primary', preset.colors.primary);
  root.style.setProperty('--primary-foreground', preset.colors.primaryForeground);
  root.style.setProperty('--secondary', preset.colors.secondary);
  root.style.setProperty('--secondary-foreground', preset.colors.secondaryForeground);
  root.style.setProperty('--muted', preset.colors.muted);
  root.style.setProperty('--muted-foreground', preset.colors.mutedForeground);
  root.style.setProperty('--accent', preset.colors.accent);
  root.style.setProperty('--accent-foreground', preset.colors.accentForeground);
  root.style.setProperty('--destructive', preset.colors.destructive);
  root.style.setProperty('--destructive-foreground', preset.colors.destructiveForeground);
  root.style.setProperty('--border', preset.colors.border);
  root.style.setProperty('--input', preset.colors.input);
  root.style.setProperty('--ring', preset.colors.ring);

  // Update dark/light class
  root.classList.remove('light', 'dark');
  root.classList.add(preset.isDark ? 'dark' : 'light');
}

/**
 * Get a theme preset by ID
 */
export function getThemePreset(id: string): ThemePreset | undefined {
  return themePresets.find((preset) => preset.id === id);
}

/**
 * Save custom theme colors to localStorage
 */
export function saveCustomTheme(colors: ThemeColors, name: string): void {
  const customThemes = getCustomThemes();
  const id = `custom-${Date.now()}`;
  customThemes.push({
    id,
    name,
    description: 'Custom theme',
    isDark: isColorDark(colors.background),
    colors,
  });
  localStorage.setItem('customThemes', JSON.stringify(customThemes));
}

/**
 * Get saved custom themes from localStorage
 */
export function getCustomThemes(): ThemePreset[] {
  try {
    const stored = localStorage.getItem('customThemes');
    return stored ? JSON.parse(stored) : [];
  } catch {
    return [];
  }
}

/**
 * Delete a custom theme
 */
export function deleteCustomTheme(id: string): void {
  const customThemes = getCustomThemes().filter((t) => t.id !== id);
  localStorage.setItem('customThemes', JSON.stringify(customThemes));
}

/**
 * Check if an HSL color string represents a dark color
 */
function isColorDark(hslString: string): boolean {
  const parts = hslString.split(' ');
  if (parts.length >= 3) {
    const lightness = parseFloat(parts[2].replace('%', ''));
    return lightness < 50;
  }
  return true;
}

/**
 * Get all available themes (presets + custom)
 */
export function getAllThemes(): ThemePreset[] {
  return [...themePresets, ...getCustomThemes()];
}
