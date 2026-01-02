# Layout Components

Application layout and navigation components that structure the UI.

## Overview

Layout components provide the structural foundation for the application, including:
- Main application layout wrapper
- Header with theme switcher
- Sidebar navigation
- Responsive design
- Route-based active states

---

## Layout

Main application layout wrapper that combines Header and Sidebar.

### Props

| Prop | Type | Description |
|------|------|-------------|
| `children` | `ReactNode` | Page content to render |

### Usage Example

```tsx
import { Layout } from '@/components/layout/Layout';

function App() {
  return (
    <Layout>
      <YourPageContent />
    </Layout>
  );
}
```

### Structure

```tsx
<div className="flex h-screen bg-background">
  <Sidebar />
  <div className="flex flex-1 flex-col overflow-hidden">
    <Header />
    <main className="flex-1 overflow-auto p-6">
      {children}
    </main>
  </div>
</div>
```

### Features

**Full Height Layout**
- Uses `h-screen` for 100vh height
- Flexbox for structure
- Overflow handling for scrollable content

**Responsive**
- Sidebar collapses on mobile
- Header adapts to viewport
- Content area scrolls independently

**Theme Aware**
- Background color from theme
- All child components inherit theme

### Layout Sections

| Section | Width | Height | Scroll |
|---------|-------|--------|--------|
| Sidebar | 256px (16rem) | 100vh | Hidden |
| Header | Flex | 56px | No |
| Main Content | Flex | Flex | Yes |

### Notes
- **Single Wrapper**: Use once at app root
- **Scroll Container**: Main content area has `overflow-auto`
- **Padding**: Content has 24px padding by default

---

## Header

Top navigation bar with theme switcher and contextual actions.

### Props

No props required. Self-contained component.

### Usage Example

```tsx
import { Header } from '@/components/layout/Header';

// Used within Layout component
<Layout>
  {/* Header is included automatically */}
</Layout>

// Or standalone
<Header />
```

### Features

**Theme Switcher**
- Dropdown menu with three options
- Light, Dark, System modes
- Icon changes based on current theme
- Persists preference to localStorage

**Responsive Design**
- Fixed height (56px)
- Flexbox layout
- Border bottom for separation

**Extensible**
- Placeholder for breadcrumbs
- Space for additional controls
- Right-aligned action area

### Theme Icons

| Mode | Icon |
|------|------|
| Light | Sun |
| Dark | Moon |
| System | Monitor |

### Structure

```tsx
<header className="flex h-14 items-center justify-between border-b px-6">
  {/* Left: Breadcrumb/Title */}
  <div>
    {/* Future: Breadcrumb navigation */}
  </div>

  {/* Right: Theme switcher + actions */}
  <div className="flex items-center gap-2">
    <ThemeDropdown />
  </div>
</header>
```

### Theme Dropdown

Uses Radix UI Dropdown Menu:

```tsx
<DropdownMenu.Root>
  <DropdownMenu.Trigger asChild>
    <Button variant="ghost" size="icon">
      <ThemeIcon />
    </Button>
  </DropdownMenu.Trigger>
  <DropdownMenu.Content>
    <DropdownMenu.Item onClick={() => setTheme('light')}>
      <Sun /> Light
    </DropdownMenu.Item>
    <DropdownMenu.Item onClick={() => setTheme('dark')}>
      <Moon /> Dark
    </DropdownMenu.Item>
    <DropdownMenu.Item onClick={() => setTheme('system')}>
      <Monitor /> System
    </DropdownMenu.Item>
  </DropdownMenu.Content>
</DropdownMenu.Root>
```

### Theme Context

Uses `useTheme()` hook:

```tsx
const { theme, setTheme } = useTheme();

// theme: 'light' | 'dark' | 'system'
// setTheme: (theme) => void
```

### Accessibility
- Proper button labels
- Keyboard navigation (Tab, Enter, Arrow keys)
- ARIA labels for screen readers
- Focus visible indicators

### Notes
- **Height**: Fixed 56px (3.5rem)
- **Border**: Bottom border for visual separation
- **Z-Index**: Positioned above content for dropdowns

---

## Sidebar

Left navigation sidebar with routes and recent conversations.

### Props

No props required. Uses React Router for navigation state.

### Usage Example

```tsx
import { Sidebar } from '@/components/layout/Sidebar';

// Used within Layout component
<Layout>
  {/* Sidebar is included automatically */}
</Layout>
```

### Features

**Navigation Menu**
- Links to main application sections
- Active route highlighting
- Icon + label for each item
- Keyboard accessible

**New Chat Button**
- Creates new conversation
- Prominent placement at top
- Loading state during creation

**Recent Conversations**
- Shows last 5 conversations
- Quick access to recent chats
- Truncated titles for long names

**Brand Header**
- Logo/icon + app name
- Fixed at top
- Consistent branding

### Navigation Items

```typescript
const navItems = [
  { path: '/chat', icon: MessageSquare, label: 'Chat' },
  { path: '/documents', icon: FileText, label: 'Documents' },
  { path: '/dashboards', icon: LayoutDashboard, label: 'Dashboards' },
  { path: '/queries', icon: History, label: 'Query History' },
  { path: '/mcp-servers', icon: Database, label: 'MCP Servers' },
  { path: '/superset', icon: BarChart3, label: 'Superset Reports' },
  { path: '/settings', icon: Settings, label: 'Settings' },
];
```

### Structure

```tsx
<aside className="flex w-64 flex-col border-r bg-card">
  {/* Brand Header */}
  <div className="flex h-14 items-center border-b px-4">
    <Database className="mr-2 h-6 w-6 text-primary" />
    <span className="font-semibold">Research Analytics</span>
  </div>

  {/* New Chat Button */}
  <div className="p-4">
    <Button onClick={handleNewChat}>
      <Plus className="mr-2 h-4 w-4" />
      New Chat
    </Button>
  </div>

  {/* Navigation Links */}
  <nav className="flex-1 space-y-1 px-2">
    {navItems.map(item => (
      <NavLink key={item.path} to={item.path}>
        <item.icon />
        {item.label}
      </NavLink>
    ))}
  </nav>

  {/* Recent Conversations */}
  <div className="border-t p-4">
    <h3>Recent Chats</h3>
    {recentConversations.map(conv => (
      <Link to={`/chat/${conv.id}`}>
        {conv.title}
      </Link>
    ))}
  </div>
</aside>
```

### Active Route Styling

```tsx
<Link
  to={item.path}
  className={cn(
    'flex items-center rounded-md px-3 py-2 text-sm font-medium',
    location.pathname === item.path
      ? 'bg-accent text-accent-foreground'  // Active
      : 'text-muted-foreground hover:bg-accent hover:text-accent-foreground'  // Inactive
  )}
>
  <item.icon className="mr-3 h-4 w-4" />
  {item.label}
</Link>
```

### New Chat Handler

```tsx
import { useCreateConversation } from '@/hooks/useConversations';
import { useChatStore } from '@/stores/chatStore';

const createConversation = useCreateConversation();
const { setCurrentConversation } = useChatStore();

const handleNewChat = async () => {
  const conversation = await createConversation.mutateAsync(undefined);
  setCurrentConversation(conversation.id);
  // Navigate to /chat/{conversation.id}
};
```

### Recent Conversations

Fetched via React Query:

```tsx
const { data: conversationsData } = useConversations();

// Display first 5
const recentConversations = conversationsData?.conversations.slice(0, 5) || [];
```

### Responsive Behavior

**Desktop** (> 768px)
- Fixed 256px width
- Always visible
- Scrollable content

**Mobile** (< 768px)
- Overlay on top of content
- Toggleable via hamburger menu
- Slides in/out with animation

### Accessibility

**Keyboard Navigation**
- Tab through navigation items
- Enter/Space to activate links
- Escape to close (mobile)

**ARIA Labels**
- `nav` role for navigation section
- `aria-current="page"` on active route
- Proper heading hierarchy

**Screen Readers**
- Descriptive link text
- Icon labels for icon-only buttons
- Landmark regions

### Styling

**Width**: 256px (16rem)
**Background**: Card color from theme
**Border**: Right border for separation
**Scrolling**: Overflow auto when content exceeds height

### Notes
- **Fixed Width**: Sidebar does not resize
- **Scroll**: Navigation area scrolls if many items
- **Z-Index**: Positioned above content on mobile

---

## Responsive Breakpoints

```typescript
const breakpoints = {
  sm: '640px',   // Sidebar collapses
  md: '768px',   // Sidebar shows
  lg: '1024px',  // Desktop layout
  xl: '1280px',  // Wide desktop
  '2xl': '1536px' // Ultra-wide
};
```

### Mobile Layout

```tsx
// Mobile: Sidebar as drawer
<div className="lg:flex">
  {/* Overlay */}
  {sidebarOpen && (
    <div
      className="fixed inset-0 z-40 bg-black/50 lg:hidden"
      onClick={closeSidebar}
    />
  )}

  {/* Sidebar drawer */}
  <Sidebar
    className={cn(
      'fixed inset-y-0 left-0 z-50 lg:static lg:z-0',
      sidebarOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'
    )}
  />

  {/* Main content */}
  <div className="flex-1">
    {/* Header with hamburger */}
    <Header onMenuClick={toggleSidebar} />
    <main>{children}</main>
  </div>
</div>
```

---

## Layout Patterns

### Full-Width Content

```tsx
<Layout>
  <div className="max-w-full">
    {/* Content spans full width */}
  </div>
</Layout>
```

### Centered Content

```tsx
<Layout>
  <div className="mx-auto max-w-7xl">
    {/* Content centered with max width */}
  </div>
</Layout>
```

### Split View

```tsx
<Layout>
  <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
    <div>{/* Left panel */}</div>
    <div>{/* Right panel */}</div>
  </div>
</Layout>
```

### Dashboard Layout

```tsx
<Layout>
  <div className="space-y-6">
    <div className="flex items-center justify-between">
      <h1>Dashboard</h1>
      <Button>Actions</Button>
    </div>
    <DashboardGrid />
  </div>
</Layout>
```

---

## Theme Integration

All layout components use the theme context:

```tsx
import { useTheme } from '@/contexts/ThemeContext';

function MyLayoutComponent() {
  const { resolvedTheme } = useTheme();

  return (
    <div className={cn(
      'layout-base-styles',
      resolvedTheme === 'dark' && 'dark-specific-styles'
    )}>
      {/* Content */}
    </div>
  );
}
```

### Theme Provider Setup

```tsx
import { ThemeProvider } from '@/contexts/ThemeContext';

function App() {
  return (
    <ThemeProvider defaultTheme="system" storageKey="ui-theme">
      <Layout>
        <Routes />
      </Layout>
    </ThemeProvider>
  );
}
```

---

## Performance Optimization

### Code Splitting

```tsx
import { lazy, Suspense } from 'react';
import { LoadingPage } from '@/components/ui/LoadingPage';

const Sidebar = lazy(() => import('./Sidebar'));

function Layout({ children }) {
  return (
    <div className="flex">
      <Suspense fallback={<div className="w-64" />}>
        <Sidebar />
      </Suspense>
      <main>{children}</main>
    </div>
  );
}
```

### Memoization

```tsx
import { memo } from 'react';

export const Header = memo(() => {
  // Header component
});

export const Sidebar = memo(() => {
  // Sidebar component
});
```

---

## Testing

### Example Tests

```tsx
import { render, screen } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { Sidebar } from '@/components/layout/Sidebar';

describe('Sidebar', () => {
  it('renders navigation items', () => {
    render(
      <BrowserRouter>
        <Sidebar />
      </BrowserRouter>
    );

    expect(screen.getByText('Chat')).toBeInTheDocument();
    expect(screen.getByText('Documents')).toBeInTheDocument();
    expect(screen.getByText('Dashboards')).toBeInTheDocument();
  });

  it('highlights active route', () => {
    window.history.pushState({}, '', '/chat');

    render(
      <BrowserRouter>
        <Sidebar />
      </BrowserRouter>
    );

    const chatLink = screen.getByText('Chat').closest('a');
    expect(chatLink).toHaveClass('bg-accent');
  });

  it('shows recent conversations', () => {
    const mockConversations = [
      { id: '1', title: 'Chat 1' },
      { id: '2', title: 'Chat 2' },
    ];

    render(
      <BrowserRouter>
        <Sidebar conversations={mockConversations} />
      </BrowserRouter>
    );

    expect(screen.getByText('Chat 1')).toBeInTheDocument();
    expect(screen.getByText('Chat 2')).toBeInTheDocument();
  });
});
```

---

## Accessibility

### Landmark Regions

```tsx
<div>
  <header role="banner">
    {/* Header content */}
  </header>

  <nav role="navigation" aria-label="Main navigation">
    {/* Sidebar navigation */}
  </nav>

  <main role="main">
    {/* Page content */}
  </main>
</div>
```

### Skip Links

Add skip link for keyboard users:

```tsx
<a
  href="#main-content"
  className="sr-only focus:not-sr-only focus:absolute focus:top-4 focus:left-4 focus:z-50"
>
  Skip to main content
</a>

<Layout>
  <main id="main-content">
    {/* Content */}
  </main>
</Layout>
```

### Focus Management

```tsx
// Focus main content on route change
useEffect(() => {
  document.getElementById('main-content')?.focus();
}, [location.pathname]);
```

---

## Customization

### Custom Sidebar Width

```tsx
// tailwind.config.js
module.exports = {
  theme: {
    extend: {
      spacing: {
        sidebar: '280px', // Custom sidebar width
      },
    },
  },
};

// Component
<aside className="w-sidebar">
  {/* Sidebar content */}
</aside>
```

### Custom Header Height

```tsx
<header className="h-16"> {/* 64px instead of default 56px */}
  {/* Header content */}
</header>
```

### Collapsible Sidebar

```tsx
const [collapsed, setCollapsed] = useState(false);

<aside className={cn(
  'transition-all duration-300',
  collapsed ? 'w-16' : 'w-64'
)}>
  {/* Show icons only when collapsed */}
</aside>
```

---

## Related Documentation

- [UI Components](./ui.md) - Button, Card primitives
- [Chat Components](./chat.md) - Chat page content
- [Dashboard Components](./dashboard.md) - Dashboard page content
- [React Router](https://reactrouter.com/) - Navigation library
