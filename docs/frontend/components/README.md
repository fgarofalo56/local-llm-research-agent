# React Component Reference

Comprehensive documentation for all React components in the Local LLM Research Analytics frontend.

## Component Categories

### Charts & Visualization
Data visualization components built on Recharts with theme support and accessibility features.

- [Chart Components](./charts.md) - Bar, Line, Area, Pie, Scatter charts, KPI cards, and data tables

### Chat Interface
Real-time chat components with markdown rendering, syntax highlighting, and message actions.

- [Chat Components](./chat.md) - Message list, chat input, MCP server selector

### Dashboard
Interactive dashboard system with drag-and-drop widgets and real-time data updates.

- [Dashboard Components](./dashboard.md) - Dashboard grid, widgets, layout management

### Layout & Navigation
Application layout, navigation, and structural components.

- [Layout Components](./layout.md) - Header, Sidebar, Layout wrapper

### UI Primitives
Reusable UI building blocks following consistent design patterns.

- [UI Components](./ui.md) - Button, Card, Input, Toast, LoadingPage

### Dialogs & Modals
Modal dialogs for user interactions and confirmations.

- [Dialog Components](./dialogs.md) - Pin to dashboard, Power BI export, keyboard shortcuts

### Specialized Components
Feature-specific components for advanced functionality.

- [Export Components](./export.md) - Multi-format export menu
- [Settings Components](./settings.md) - Theme selector with preset support
- [Superset Components](./superset.md) - Apache Superset dashboard embedding
- [Upload Components](./upload.md) - Global upload progress tracker
- [Onboarding Components](./onboarding.md) - User onboarding wizard

## Component Architecture

### Design Principles

1. **Composition Over Inheritance**
   - Components are built using composition patterns
   - Reusable primitives combined to create complex UIs

2. **Type Safety**
   - All components use TypeScript with strict type checking
   - Props interfaces clearly define component contracts

3. **Accessibility First**
   - ARIA labels and roles on interactive elements
   - Keyboard navigation support
   - Screen reader friendly markup

4. **Theme Awareness**
   - Components respect system/user theme preferences
   - CSS variables for consistent theming
   - Dark/light mode support built-in

5. **Performance**
   - React.memo for expensive renders
   - Lazy loading for heavy components
   - Optimistic UI updates

### Common Patterns

#### Using Theme Context
```tsx
import { useTheme } from '@/contexts/ThemeContext';

export function MyComponent() {
  const { resolvedTheme } = useTheme();
  const textColor = resolvedTheme === 'dark' ? '#a1a1aa' : '#52525b';

  return <div style={{ color: textColor }}>Themed content</div>;
}
```

#### State Management with Zustand
```tsx
import { useChatStore } from '@/stores/chatStore';

export function MyComponent() {
  const { messages, addMessage } = useChatStore();

  return (
    <button onClick={() => addMessage({ role: 'user', content: 'Hello' })}>
      Send ({messages.length})
    </button>
  );
}
```

#### API Queries with React Query
```tsx
import { useQuery } from '@tanstack/react-query';
import { api } from '@/api/client';

export function MyComponent() {
  const { data, isLoading, error } = useQuery({
    queryKey: ['my-data'],
    queryFn: () => api.get('/endpoint'),
  });

  if (isLoading) return <div>Loading...</div>;
  if (error) return <div>Error: {error.message}</div>;
  return <div>{data?.value}</div>;
}
```

#### Forwarding Refs
```tsx
import { forwardRef } from 'react';

interface MyProps {
  className?: string;
}

const MyComponent = forwardRef<HTMLDivElement, MyProps>(
  ({ className }, ref) => {
    return <div ref={ref} className={className}>Content</div>;
  }
);
MyComponent.displayName = 'MyComponent';

export { MyComponent };
```

## Styling

### Tailwind CSS
All components use Tailwind CSS for styling:

```tsx
<div className="flex items-center gap-2 rounded-md border bg-card px-3 py-2">
  <Icon className="h-4 w-4 text-muted-foreground" />
  <span className="text-sm">Label</span>
</div>
```

### CSS Variables (Theme Tokens)
Theme colors are defined as CSS variables:

- `--background` - Page background
- `--foreground` - Default text color
- `--primary` - Primary brand color
- `--secondary` - Secondary color
- `--accent` - Accent/hover color
- `--muted` - Muted backgrounds
- `--border` - Border color
- `--destructive` - Error/danger color

### Utility Function
Use the `cn()` helper to merge class names:

```tsx
import { cn } from '@/lib/utils';

<div className={cn(
  'base-classes',
  condition && 'conditional-classes',
  className // Allow prop override
)} />
```

## Component Testing

### Example Test
```tsx
import { render, screen, fireEvent } from '@testing-library/react';
import { Button } from '@/components/ui/Button';

describe('Button', () => {
  it('renders and handles clicks', () => {
    const handleClick = vi.fn();
    render(<Button onClick={handleClick}>Click me</Button>);

    const button = screen.getByRole('button', { name: /click me/i });
    fireEvent.click(button);

    expect(handleClick).toHaveBeenCalledOnce();
  });
});
```

## File Organization

```
frontend/src/components/
├── charts/              # Data visualization
│   ├── AreaChartComponent.tsx
│   ├── BarChartComponent.tsx
│   ├── ChartRenderer.tsx
│   ├── ChartWrapper.tsx
│   ├── DataTable.tsx
│   ├── KPICard.tsx
│   ├── LineChartComponent.tsx
│   ├── PieChartComponent.tsx
│   ├── ScatterChartComponent.tsx
│   ├── QueryResultPanel.tsx
│   └── index.ts
│
├── chat/                # Chat interface
│   ├── ChatInput.tsx
│   ├── MessageList.tsx
│   └── MCPServerSelector.tsx
│
├── dashboard/           # Dashboard system
│   ├── DashboardGrid.tsx
│   ├── DashboardWidget.tsx
│   ├── ShareDashboardDialog.tsx
│   └── index.ts
│
├── dialogs/             # Modal dialogs
│   ├── PinToDashboardDialog.tsx
│   ├── PowerBIExportDialog.tsx
│   ├── KeyboardShortcutsDialog.tsx
│   └── index.ts
│
├── export/              # Export functionality
│   ├── ExportMenu.tsx
│   └── index.ts
│
├── layout/              # Layout components
│   ├── Header.tsx
│   ├── Layout.tsx
│   └── Sidebar.tsx
│
├── settings/            # Settings UI
│   ├── ThemeSelector.tsx
│   └── index.ts
│
├── superset/            # Superset integration
│   ├── SupersetEmbed.tsx
│   └── index.ts
│
├── ui/                  # UI primitives
│   ├── Button.tsx
│   ├── Card.tsx
│   ├── Input.tsx
│   ├── Toast.tsx
│   ├── LoadingPage.tsx
│   └── index.ts
│
├── upload/              # Upload progress
│   ├── GlobalUploadProgress.tsx
│   └── index.ts
│
└── onboarding/          # Onboarding wizard
    ├── OnboardingWizard.tsx
    └── index.ts
```

## Dependencies

### Core Libraries
- **React 19** - UI library
- **React Router** - Client-side routing
- **TypeScript** - Type safety
- **Tailwind CSS** - Utility-first styling

### UI Libraries
- **Radix UI** - Accessible primitives (Dialog, Dropdown, Switch)
- **Recharts** - Chart components
- **Lucide React** - Icon library
- **React Markdown** - Markdown rendering
- **React Syntax Highlighter** - Code syntax highlighting

### State & Data
- **Zustand** - Client state management
- **TanStack Query** - Server state & caching
- **React Hook Form** - Form handling (where used)

### Utilities
- **clsx** - Class name merging
- **date-fns** - Date formatting

## Next Steps

Explore component categories:

1. [Chart Components](./charts.md) - Data visualization
2. [Chat Components](./chat.md) - Chat interface
3. [Dashboard Components](./dashboard.md) - Dashboard system
4. [Layout Components](./layout.md) - Application layout
5. [UI Components](./ui.md) - Reusable primitives
6. [Dialog Components](./dialogs.md) - Modal dialogs
7. [Specialized Components](./export.md) - Export, Settings, Superset, Upload, Onboarding
