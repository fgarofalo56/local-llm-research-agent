/* eslint-disable react-refresh/only-export-components */
import { createContext, useContext, useEffect, useState, type ReactNode } from 'react';

type ThemeMode = 'dark' | 'light' | 'system';

// Theme variants available
export type ThemeVariant =
  | 'default'   // Default slate theme
  | 'nord'      // Arctic blue (dark only)
  | 'dracula'   // Popular dark theme (dark only)
  | 'ocean'     // Blue/teal tones
  | 'forest'    // Green tones
  | 'rose'      // Pink/rose tones
  | 'amber'     // Warm orange tones
  | 'violet'    // Purple tones
  | 'midnight'; // Deep blue-black (dark only)

export interface ThemeInfo {
  id: ThemeVariant;
  name: string;
  description: string;
  supportedModes: ('light' | 'dark')[];
  previewColors: {
    bg: string;
    primary: string;
    accent: string;
  };
}

// Available themes with metadata
export const THEMES: ThemeInfo[] = [
  {
    id: 'default',
    name: 'Default',
    description: 'Classic slate gray theme',
    supportedModes: ['light', 'dark'],
    previewColors: { bg: '#0f172a', primary: '#f8fafc', accent: '#1e293b' },
  },
  {
    id: 'nord',
    name: 'Nord',
    description: 'Arctic blue inspired palette',
    supportedModes: ['dark'],
    previewColors: { bg: '#2e3440', primary: '#88c0d0', accent: '#5e81ac' },
  },
  {
    id: 'dracula',
    name: 'Dracula',
    description: 'Popular dark purple theme',
    supportedModes: ['dark'],
    previewColors: { bg: '#282a36', primary: '#bd93f9', accent: '#50fa7b' },
  },
  {
    id: 'ocean',
    name: 'Ocean',
    description: 'Deep sea blues and teals',
    supportedModes: ['light', 'dark'],
    previewColors: { bg: '#0c1929', primary: '#38bdf8', accent: '#2dd4bf' },
  },
  {
    id: 'forest',
    name: 'Forest',
    description: 'Natural forest greens',
    supportedModes: ['light', 'dark'],
    previewColors: { bg: '#0f1f14', primary: '#4ade80', accent: '#34d399' },
  },
  {
    id: 'rose',
    name: 'Rose',
    description: 'Elegant pink and rose',
    supportedModes: ['light', 'dark'],
    previewColors: { bg: '#1f0c14', primary: '#f43f5e', accent: '#ec4899' },
  },
  {
    id: 'amber',
    name: 'Amber',
    description: 'Warm orange and amber',
    supportedModes: ['light', 'dark'],
    previewColors: { bg: '#1a1006', primary: '#f59e0b', accent: '#eab308' },
  },
  {
    id: 'violet',
    name: 'Violet',
    description: 'Deep purple vibes',
    supportedModes: ['light', 'dark'],
    previewColors: { bg: '#150c1f', primary: '#a78bfa', accent: '#c084fc' },
  },
  {
    id: 'midnight',
    name: 'Midnight',
    description: 'Deep blue-black',
    supportedModes: ['dark'],
    previewColors: { bg: '#0a0d14', primary: '#3b82f6', accent: '#60a5fa' },
  },
];

interface ThemeContextType {
  mode: ThemeMode;
  setMode: (mode: ThemeMode) => void;
  variant: ThemeVariant;
  setVariant: (variant: ThemeVariant) => void;
  resolvedMode: 'dark' | 'light';
  // Legacy compatibility
  theme: ThemeMode;
  setTheme: (theme: ThemeMode) => void;
  resolvedTheme: 'dark' | 'light';
}

const ThemeContext = createContext<ThemeContextType | undefined>(undefined);

export function ThemeProvider({ children }: { children: ReactNode }) {
  const [mode, setMode] = useState<ThemeMode>(() => {
    const stored = localStorage.getItem('theme-mode');
    return (stored as ThemeMode) || 'dark';
  });

  const [variant, setVariant] = useState<ThemeVariant>(() => {
    const stored = localStorage.getItem('theme-variant');
    return (stored as ThemeVariant) || 'default';
  });

  const [resolvedMode, setResolvedMode] = useState<'dark' | 'light'>('dark');

  useEffect(() => {
    const root = window.document.documentElement;

    const updateTheme = () => {
      let resolved: 'dark' | 'light';

      if (mode === 'system') {
        resolved = window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
      } else {
        resolved = mode;
      }

      // Remove all mode and variant classes
      root.classList.remove('light', 'dark');
      THEMES.forEach(t => root.classList.remove(`theme-${t.id}`));

      // Add the resolved mode
      root.classList.add(resolved);

      // Add variant class if not default
      if (variant !== 'default') {
        // Check if variant supports current mode
        const themeInfo = THEMES.find(t => t.id === variant);
        if (themeInfo?.supportedModes.includes(resolved)) {
          root.classList.add(`theme-${variant}`);
        }
      }

      setResolvedMode(resolved);
    };

    updateTheme();
    localStorage.setItem('theme-mode', mode);
    localStorage.setItem('theme-variant', variant);

    // Listen for system theme changes
    const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
    const handler = () => mode === 'system' && updateTheme();
    mediaQuery.addEventListener('change', handler);

    return () => mediaQuery.removeEventListener('change', handler);
  }, [mode, variant]);

  // Legacy compatibility - map theme to mode
  const setTheme = (theme: ThemeMode) => setMode(theme);

  return (
    <ThemeContext.Provider
      value={{
        mode,
        setMode,
        variant,
        setVariant,
        resolvedMode,
        // Legacy compatibility
        theme: mode,
        setTheme,
        resolvedTheme: resolvedMode,
      }}
    >
      {children}
    </ThemeContext.Provider>
  );
}

export function useTheme() {
  const context = useContext(ThemeContext);
  if (!context) {
    throw new Error('useTheme must be used within ThemeProvider');
  }
  return context;
}
