# Styling Guide

This guide covers styling conventions, Tailwind CSS patterns, and theme customization for the Local LLM Research Agent frontend.

## Styling Philosophy

We use **Tailwind CSS** for all styling with these principles:

1. **Utility-first** - Compose styles from utility classes
2. **No custom CSS** - Use Tailwind utilities whenever possible
3. **Component-scoped** - Styles live with components
4. **Responsive by default** - Mobile-first approach
5. **Dark mode first** - Primary UI is dark themed

## Tailwind CSS Setup

### Configuration

```javascript
// tailwind.config.js
export default {
  darkMode: 'class', // Use .dark class for dark mode
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // HSL color system for theming
        border: "hsl(var(--border))",
        input: "hsl(var(--input))",
        ring: "hsl(var(--ring))",
        background: "hsl(var(--background))",
        foreground: "hsl(var(--foreground))",
        primary: {
          DEFAULT: "hsl(var(--primary))",
          foreground: "hsl(var(--primary-foreground))",
        },
        // ... more colors
      },
      borderRadius: {
        lg: "var(--radius)",
        md: "calc(var(--radius) - 2px)",
        sm: "calc(var(--radius) - 4px)",
      },
    },
  },
  plugins: [],
}
```

### CSS Variables

All theme colors are defined as CSS variables in `index.css`:

```css
:root {
  --background: 0 0% 100%;
  --foreground: 222.2 84% 4.9%;
  --primary: 222.2 47.4% 11.2%;
  --primary-foreground: 210 40% 98%;
  /* ... more variables */
}

.dark {
  --background: 222.2 84% 4.9%;
  --foreground: 210 40% 98%;
  --primary: 210 40% 98%;
  --primary-foreground: 222.2 47.4% 11.2%;
  /* ... more variables */
}
```

## Common Patterns

### Layout Patterns

#### Flex Container

```typescript
// Horizontal layout
<div className="flex items-center gap-2">
  <Icon />
  <span>Text</span>
</div>

// Vertical layout
<div className="flex flex-col gap-4">
  <Header />
  <Content />
</div>

// Centered content
<div className="flex items-center justify-center h-screen">
  <LoadingSpinner />
</div>

// Space between
<div className="flex items-center justify-between">
  <Title />
  <Actions />
</div>
```

#### Grid Layout

```typescript
// Auto-fit grid
<div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
  {items.map(item => <Card key={item.id} {...item} />)}
</div>

// Fixed columns
<div className="grid grid-cols-3 gap-4">
  <Column />
  <Column />
  <Column />
</div>
```

#### Full Height Layouts

```typescript
// App shell
<div className="flex h-screen flex-col">
  <Header />
  <div className="flex flex-1 overflow-hidden">
    <Sidebar />
    <main className="flex-1 overflow-auto">
      <Content />
    </main>
  </div>
</div>
```

### Component Patterns

#### Button

```typescript
// Primary button
<button className="bg-primary text-primary-foreground hover:bg-primary/90 px-4 py-2 rounded-md">
  Click me
</button>

// Secondary button
<button className="bg-secondary text-secondary-foreground hover:bg-secondary/80 px-4 py-2 rounded-md">
  Cancel
</button>

// Outline button
<button className="border border-input bg-background hover:bg-accent px-4 py-2 rounded-md">
  Outline
</button>

// Destructive button
<button className="bg-destructive text-destructive-foreground hover:bg-destructive/90 px-4 py-2 rounded-md">
  Delete
</button>
```

#### Card

```typescript
<div className="bg-card text-card-foreground rounded-lg border border-border p-6">
  <h3 className="text-lg font-semibold mb-2">Card Title</h3>
  <p className="text-muted-foreground">Card content goes here</p>
</div>
```

#### Input

```typescript
<input
  type="text"
  className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
  placeholder="Enter text..."
/>
```

#### Modal/Dialog

```typescript
<div className="fixed inset-0 z-50 bg-background/80 backdrop-blur-sm">
  <div className="fixed left-1/2 top-1/2 z-50 -translate-x-1/2 -translate-y-1/2 w-full max-w-lg">
    <div className="bg-card rounded-lg border border-border p-6 shadow-lg">
      <h2 className="text-lg font-semibold">Dialog Title</h2>
      <div className="mt-4">
        {/* Content */}
      </div>
    </div>
  </div>
</div>
```

### Typography

```typescript
// Headings
<h1 className="scroll-m-20 text-4xl font-extrabold tracking-tight lg:text-5xl">
  Page Title
</h1>

<h2 className="scroll-m-20 border-b pb-2 text-3xl font-semibold tracking-tight">
  Section Title
</h2>

<h3 className="scroll-m-20 text-2xl font-semibold tracking-tight">
  Subsection
</h3>

// Body text
<p className="leading-7 [&:not(:first-child)]:mt-6">
  Regular paragraph text
</p>

// Muted text
<p className="text-sm text-muted-foreground">
  Secondary information
</p>

// Code
<code className="relative rounded bg-muted px-[0.3rem] py-[0.2rem] font-mono text-sm font-semibold">
  npm install
</code>
```

## Responsive Design

### Breakpoints

Tailwind's default breakpoints:

- `sm`: 640px
- `md`: 768px
- `lg`: 1024px
- `xl`: 1280px
- `2xl`: 1536px

### Mobile-First Patterns

```typescript
// Column on mobile, row on desktop
<div className="flex flex-col md:flex-row gap-4">
  <div>Column 1</div>
  <div>Column 2</div>
</div>

// Hide on mobile, show on desktop
<div className="hidden md:block">
  Desktop only content
</div>

// Different sizes
<div className="w-full md:w-1/2 lg:w-1/3">
  Responsive width
</div>

// Responsive padding
<div className="p-4 md:p-6 lg:p-8">
  Content
</div>
```

## Dark Mode

### Using Theme Colors

Always use theme colors instead of hardcoded values:

```typescript
// Good: Uses theme colors
<div className="bg-background text-foreground">
  <button className="bg-primary text-primary-foreground">Click</button>
</div>

// Bad: Hardcoded colors
<div className="bg-white text-black">
  <button className="bg-blue-500 text-white">Click</button>
</div>
```

### Dark Mode Variants

Use `dark:` prefix for dark-mode-specific styles:

```typescript
// Different colors in light/dark mode
<div className="bg-white dark:bg-gray-900 text-black dark:text-white">
  Content
</div>

// Different borders
<div className="border border-gray-200 dark:border-gray-800">
  Content
</div>
```

### Theme Switching

Implemented via `ThemeContext`:

```typescript
import { useTheme } from '@/contexts/ThemeContext';

function ThemeToggle() {
  const { mode, setMode, variant, setVariant } = useTheme();

  return (
    <div>
      {/* Mode selector */}
      <select value={mode} onChange={(e) => setMode(e.target.value)}>
        <option value="light">Light</option>
        <option value="dark">Dark</option>
        <option value="system">System</option>
      </select>

      {/* Variant selector */}
      <select value={variant} onChange={(e) => setVariant(e.target.value)}>
        <option value="default">Default</option>
        <option value="nord">Nord</option>
        <option value="dracula">Dracula</option>
        {/* ... */}
      </select>
    </div>
  );
}
```

## Theme Variants

### Available Themes

| Theme | Light | Dark | Description |
|-------|-------|------|-------------|
| Default | Yes | Yes | Classic slate gray |
| Nord | No | Yes | Arctic blue inspired |
| Dracula | No | Yes | Popular purple theme |
| Ocean | Yes | Yes | Blue/teal tones |
| Forest | Yes | Yes | Natural greens |
| Rose | Yes | Yes | Elegant pink |
| Amber | Yes | Yes | Warm orange |
| Violet | Yes | Yes | Deep purple |
| Midnight | No | Yes | Deep blue-black |

### Custom Theme Creation

Add a new theme variant in `index.css`:

```css
/* Light variant */
.light.theme-ocean {
  --background: 200 20% 98%;
  --foreground: 200 50% 10%;
  --primary: 200 80% 40%;
  --primary-foreground: 0 0% 100%;
  /* ... */
}

/* Dark variant */
.dark.theme-ocean {
  --background: 200 60% 5%;
  --foreground: 200 20% 95%;
  --primary: 200 70% 50%;
  --primary-foreground: 200 60% 5%;
  /* ... */
}
```

Update `ThemeContext.tsx`:

```typescript
export const THEMES: ThemeInfo[] = [
  // ... existing themes
  {
    id: 'ocean',
    name: 'Ocean',
    description: 'Deep sea blues and teals',
    supportedModes: ['light', 'dark'],
    previewColors: { bg: '#0c1929', primary: '#38bdf8', accent: '#2dd4bf' },
  },
];
```

## Utility Composition

### The `cn` Helper

Use the `cn` utility for conditional classes:

```typescript
import { cn } from '@/lib/utils';

function Button({ variant, className, ...props }: ButtonProps) {
  return (
    <button
      className={cn(
        // Base styles
        'px-4 py-2 rounded-md font-medium transition-colors',
        // Conditional styles
        variant === 'primary' && 'bg-primary text-primary-foreground',
        variant === 'secondary' && 'bg-secondary text-secondary-foreground',
        // User-provided classes
        className
      )}
      {...props}
    />
  );
}
```

### Class Organization

Order classes logically:

```typescript
<div className={cn(
  // Layout
  'flex items-center justify-between',
  // Spacing
  'p-4 gap-2',
  // Sizing
  'w-full h-10',
  // Typography
  'text-sm font-medium',
  // Colors
  'bg-card text-card-foreground',
  // Borders
  'border border-border rounded-md',
  // Effects
  'shadow-sm hover:shadow-md',
  // Transitions
  'transition-all duration-200',
  // Responsive
  'md:p-6 lg:p-8',
  // States
  'hover:bg-accent focus:ring-2',
  // Dark mode
  'dark:bg-gray-800'
)}>
  Content
</div>
```

## Component Style Variants

### Using Variants

Create reusable component styles with variants:

```typescript
// components/ui/Button.tsx
type ButtonVariant = 'primary' | 'secondary' | 'outline' | 'ghost' | 'destructive';
type ButtonSize = 'sm' | 'md' | 'lg';

interface ButtonProps {
  variant?: ButtonVariant;
  size?: ButtonSize;
  className?: string;
}

export function Button({
  variant = 'primary',
  size = 'md',
  className,
  ...props
}: ButtonProps) {
  return (
    <button
      className={cn(
        // Base
        'inline-flex items-center justify-center rounded-md font-medium',
        'transition-colors focus-visible:outline-none focus-visible:ring-2',
        'disabled:pointer-events-none disabled:opacity-50',

        // Variants
        variant === 'primary' &&
          'bg-primary text-primary-foreground hover:bg-primary/90',
        variant === 'secondary' &&
          'bg-secondary text-secondary-foreground hover:bg-secondary/80',
        variant === 'outline' &&
          'border border-input bg-background hover:bg-accent',
        variant === 'ghost' &&
          'hover:bg-accent hover:text-accent-foreground',
        variant === 'destructive' &&
          'bg-destructive text-destructive-foreground hover:bg-destructive/90',

        // Sizes
        size === 'sm' && 'h-9 px-3 text-sm',
        size === 'md' && 'h-10 px-4 py-2',
        size === 'lg' && 'h-11 px-8 text-lg',

        className
      )}
      {...props}
    />
  );
}
```

## Icons

### Lucide React

```typescript
import { Search, Upload, Trash2, Settings } from 'lucide-react';

function Toolbar() {
  return (
    <div className="flex gap-2">
      <button>
        <Search className="h-4 w-4" />
      </button>
      <button>
        <Upload className="h-5 w-5 text-primary" />
      </button>
      <button>
        <Trash2 className="h-4 w-4 text-destructive" />
      </button>
    </div>
  );
}
```

### Icon Sizing

Standard icon sizes:

- `h-3 w-3` - Extra small (12px)
- `h-4 w-4` - Small (16px)
- `h-5 w-5` - Medium (20px)
- `h-6 w-6` - Large (24px)
- `h-8 w-8` - Extra large (32px)

## Animations & Transitions

### Hover Effects

```typescript
// Background change
<button className="bg-primary hover:bg-primary/90 transition-colors">
  Hover me
</button>

// Scale
<div className="transform hover:scale-105 transition-transform">
  Card
</div>

// Shadow
<div className="shadow hover:shadow-lg transition-shadow">
  Card
</div>
```

### Loading States

```typescript
// Spinner
<div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary" />

// Pulse
<div className="animate-pulse bg-muted h-4 w-48 rounded" />

// Bounce
<div className="animate-bounce">
  <ArrowDown />
</div>
```

### Custom Animations

Add to `tailwind.config.js`:

```javascript
theme: {
  extend: {
    animation: {
      'slide-in': 'slideIn 0.3s ease-out',
      'fade-in': 'fadeIn 0.2s ease-in',
    },
    keyframes: {
      slideIn: {
        '0%': { transform: 'translateX(-100%)' },
        '100%': { transform: 'translateX(0)' },
      },
      fadeIn: {
        '0%': { opacity: '0' },
        '100%': { opacity: '1' },
      },
    },
  },
}
```

## Accessibility

### Focus States

```typescript
// Visible focus ring
<button className="focus:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2">
  Click me
</button>

// Custom focus styles
<input className="focus:border-primary focus:ring-2 focus:ring-primary/20" />
```

### Screen Reader Only

```typescript
// Hide visually but keep for screen readers
<span className="sr-only">Close</span>
```

### Color Contrast

Ensure sufficient contrast ratios:

```typescript
// Good: High contrast
<div className="bg-background text-foreground">
  Text is readable
</div>

// Check: Use browser tools to verify contrast
<div className="bg-primary text-primary-foreground">
  Ensure 4.5:1 contrast ratio
</div>
```

## Best Practices

### 1. Use Semantic Color Names

```typescript
// Good: Semantic
<div className="bg-destructive text-destructive-foreground">
  Error message
</div>

// Bad: Non-semantic
<div className="bg-red-500 text-white">
  Error message
</div>
```

### 2. Avoid Magic Numbers

```typescript
// Good: Named spacing
<div className="gap-4 p-6">

// Bad: Arbitrary values
<div className="gap-[17px] p-[23px]">
```

### 3. Use Consistent Spacing Scale

Stick to Tailwind's spacing scale (4px increments):

- `gap-1` (4px)
- `gap-2` (8px)
- `gap-4` (16px)
- `gap-6` (24px)
- `gap-8` (32px)

### 4. Mobile-First

Start with mobile styles, add larger breakpoints:

```typescript
<div className="text-sm md:text-base lg:text-lg">
  Responsive text
</div>
```

### 5. Extract Repeated Patterns

```typescript
// Create reusable components
const Card = ({ children }: Props) => (
  <div className="bg-card text-card-foreground rounded-lg border border-border p-6">
    {children}
  </div>
);
```

### 6. Avoid Over-Nesting

```typescript
// Good: Flat structure
<div className="flex gap-4">
  <Button />
  <Button />
</div>

// Bad: Unnecessary nesting
<div className="flex">
  <div className="gap-4">
    <div><Button /></div>
    <div><Button /></div>
  </div>
</div>
```

### 7. Use Proper HTML Semantics

```typescript
// Good: Semantic HTML
<nav className="flex gap-4">
  <a href="/">Home</a>
</nav>

// Bad: Divs everywhere
<div className="flex gap-4">
  <div onClick={navigate}>Home</div>
</div>
```

## Debugging Styles

### Browser DevTools

1. Inspect element
2. Check computed styles
3. Toggle Tailwind classes
4. Verify CSS variable values

### Common Issues

**Class not applying:**
- Check class name spelling
- Ensure content path in `tailwind.config.js` includes file
- Verify no CSS conflicts

**Dark mode not working:**
- Ensure `.dark` class on `<html>` element
- Check theme colors use CSS variables
- Verify dark mode variants are correct

**Responsive not working:**
- Mobile-first: start with base, add `md:`, `lg:`
- Check viewport meta tag in HTML
- Test actual mobile devices, not just browser resize

## Resources

- [Tailwind CSS Documentation](https://tailwindcss.com/docs)
- [Tailwind UI Components](https://tailwindui.com/)
- [shadcn/ui](https://ui.shadcn.com/) - Inspiration for component patterns
- [Radix Colors](https://www.radix-ui.com/colors) - Color system inspiration
- [Lucide Icons](https://lucide.dev/) - Icon library

## Next Steps

- Review [API Integration](./api-integration.md) for backend communication
- Check [Architecture](./architecture.md) for component structure
- See [State Management](./state-management.md) for data flow
