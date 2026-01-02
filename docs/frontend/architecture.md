# Frontend Architecture

This document describes the architecture and design patterns used in the Local LLM Research Agent frontend.

## Architecture Overview

The application follows a modern React architecture with clear separation of concerns:

```
┌─────────────────────────────────────────────────────────┐
│                     Browser                              │
│  ┌───────────────────────────────────────────────────┐  │
│  │              React Application                     │  │
│  │  ┌─────────────────────────────────────────────┐  │  │
│  │  │           Pages (Routes)                     │  │  │
│  │  │  ┌────────┐ ┌────────┐ ┌────────┐           │  │  │
│  │  │  │  Chat  │ │Dashboard│ │Settings│  ...      │  │  │
│  │  │  └────────┘ └────────┘ └────────┘           │  │  │
│  │  └─────────────────────────────────────────────┘  │  │
│  │  ┌─────────────────────────────────────────────┐  │  │
│  │  │        Feature Components                    │  │  │
│  │  │  ┌─────────┐ ┌──────────┐ ┌──────────┐      │  │  │
│  │  │  │  Chat   │ │  Charts  │ │ Dashboard│ ...  │  │  │
│  │  │  └─────────┘ └──────────┘ └──────────┘      │  │  │
│  │  └─────────────────────────────────────────────┘  │  │
│  │  ┌─────────────────────────────────────────────┐  │  │
│  │  │           UI Primitives                      │  │  │
│  │  │  ┌──────┐ ┌──────┐ ┌──────┐                 │  │  │
│  │  │  │Button│ │ Card │ │Input │  ...            │  │  │
│  │  │  └──────┘ └──────┘ └──────┘                 │  │  │
│  │  └─────────────────────────────────────────────┘  │  │
│  └───────────────────────────────────────────────────┘  │
│                                                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │   Zustand    │  │TanStack Query│  │   Context    │  │
│  │  (UI State)  │  │(Server State)│  │   (Theme)    │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
│                                                          │
│  ┌───────────────────────────────────────────────────┐  │
│  │              API Client Layer                     │  │
│  │  ┌────────┐ ┌────────┐ ┌────────┐                │  │
│  │  │  REST  │ │  WS    │ │ Upload │                │  │
│  │  └────────┘ └────────┘ └────────┘                │  │
│  └───────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
                         ↓
                    HTTP/WebSocket
                         ↓
┌─────────────────────────────────────────────────────────┐
│              FastAPI Backend (Port 8000)                 │
└─────────────────────────────────────────────────────────┘
```

## Core Principles

### 1. Component Composition

Components are composed from smaller, reusable pieces following the atomic design methodology:

**Atoms** (UI Primitives)
- `Button`, `Input`, `Card`
- Single-purpose, highly reusable
- Located in `components/ui/`

**Molecules** (Feature Components)
- `ChatInput`, `MessageList`, `ChartRenderer`
- Combine multiple atoms
- Located in feature directories (`components/chat/`, `components/charts/`)

**Organisms** (Complex Components)
- `DashboardGrid`, `GlobalUploadProgress`
- Combine molecules and atoms
- Located in feature directories

**Pages** (Route Components)
- `ChatPage`, `DashboardsPage`, `DocumentsPage`
- Top-level route handlers
- Located in `pages/`

### 2. Single Responsibility

Each component has one clear purpose:

```typescript
// Good: ChatInput handles only input concerns
export function ChatInput({ onSubmit }: ChatInputProps) {
  // Input state, validation, submission
}

// Good: MessageList handles only message rendering
export function MessageList({ messages }: MessageListProps) {
  // Message rendering, scrolling
}
```

### 3. Props Over State

Prefer props for component configuration:

```typescript
// Good: Flexible, testable
function Chart({ data, type }: ChartProps) {
  return <ChartRenderer data={data} type={type} />;
}

// Avoid: Hard to test, inflexible
function Chart() {
  const data = useChatStore(s => s.chartData); // Tightly coupled
  return <ChartRenderer data={data} />;
}
```

Exception: Use stores for truly global state that needs to persist across unmounts.

### 4. TypeScript Everywhere

All components, functions, and data structures are typed:

```typescript
interface Message {
  id: number;
  role: 'user' | 'assistant' | 'system';
  content: string;
  created_at: string;
}

interface MessageListProps {
  messages: Message[];
  onRate?: (messageId: number, rating: 'up' | 'down') => void;
}

export function MessageList({ messages, onRate }: MessageListProps) {
  // Implementation
}
```

## Data Flow

### State Management Layers

```
┌─────────────────────────────────────────────────────┐
│              Component Local State                   │
│  (useState, useReducer)                             │
│  - Form inputs                                      │
│  - UI toggles                                       │
│  - Temporary display state                         │
└─────────────────────────────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────────────┐
│                Zustand Stores                        │
│  - UI state that persists across unmounts          │
│  - User preferences                                 │
│  - Edit modes, selections                          │
└─────────────────────────────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────────────┐
│              TanStack Query                          │
│  - Server state (cached)                            │
│  - API data                                         │
│  - Automatic refetching                             │
└─────────────────────────────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────────────┐
│              React Context                           │
│  - Theme settings                                   │
│  - Global configurations                            │
│  - Rarely changing state                            │
└─────────────────────────────────────────────────────┘
```

### Request Flow

```
User Action
    ↓
Component Event Handler
    ↓
TanStack Query Hook (useMutation/useQuery)
    ↓
API Client Function
    ↓
Fetch API
    ↓
Backend API
    ↓
Response
    ↓
TanStack Query Cache Update
    ↓
Component Re-render
```

### WebSocket Flow

```
Component Mount
    ↓
Create WebSocket Connection
    ↓
Send Message via WS
    ↓
Backend Processing (Streaming)
    ↓
WS Message Events
    ↓
Update Component State
    ↓
Real-time UI Update
```

## File Organization

### Feature-Based Organization

Group related components by feature:

```
components/
├── chat/
│   ├── ChatInput.tsx         # Message input
│   ├── MessageList.tsx       # Message display
│   └── MCPServerSelector.tsx # Server selection
├── charts/
│   ├── ChartRenderer.tsx     # Chart type router
│   ├── LineChartComponent.tsx
│   ├── BarChartComponent.tsx
│   └── DataTable.tsx
└── dashboard/
    ├── DashboardGrid.tsx     # Grid layout
    └── DashboardWidget.tsx   # Widget wrapper
```

### Component File Structure

Each component file follows this pattern:

```typescript
// 1. Imports
import { useState } from 'react';
import { Button } from '@/components/ui/Button';
import type { Message } from '@/types';

// 2. Types and Interfaces
interface ComponentProps {
  data: Message[];
  onAction: () => void;
}

// 3. Helper functions or constants (if needed)
const formatDate = (date: string) => {
  return new Date(date).toLocaleDateString();
};

// 4. Main component
export function Component({ data, onAction }: ComponentProps) {
  // Hooks
  const [state, setState] = useState(false);

  // Derived state
  const count = data.length;

  // Event handlers
  const handleClick = () => {
    onAction();
    setState(true);
  };

  // Render
  return (
    <div>
      {/* JSX */}
    </div>
  );
}

// 5. Additional exports (if needed)
export type { ComponentProps };
```

## Routing Architecture

### Route Structure

```typescript
<Routes>
  <Route path="/" element={<Navigate to="/chat" replace />} />
  <Route path="/chat" element={<ChatPage />} />
  <Route path="/chat/:conversationId" element={<ChatPage />} />
  <Route path="/documents" element={<DocumentsPage />} />
  <Route path="/dashboards" element={<DashboardsPage />} />
  <Route path="/queries" element={<QueriesPage />} />
  <Route path="/mcp-servers" element={<MCPServersPage />} />
  <Route path="/superset" element={<SupersetPage />} />
  <Route path="/settings" element={<SettingsPage />} />
  <Route path="/settings/database" element={<DatabaseSettingsPage />} />
</Routes>
```

### Page Component Pattern

Pages are thin wrappers that:

1. Handle route parameters
2. Fetch data with TanStack Query
3. Delegate rendering to feature components

```typescript
export function ChatPage() {
  const { conversationId } = useParams();
  const navigate = useNavigate();

  // Fetch data
  const { data: conversation } = useQuery({
    queryKey: ['conversation', conversationId],
    queryFn: () => api.get(`/conversations/${conversationId}`),
    enabled: !!conversationId,
  });

  // Render
  return (
    <div className="flex flex-col h-full">
      <MessageList messages={conversation?.messages ?? []} />
      <ChatInput onSubmit={handleSubmit} />
    </div>
  );
}
```

## Layout System

### App Layout

```
┌────────────────────────────────────────────────────┐
│                    Header                           │
│  [Logo] [Nav] [Theme] [Settings]                   │
├────────┬───────────────────────────────────────────┤
│        │                                            │
│ Side   │          Page Content                     │
│ bar    │                                            │
│        │                                            │
│ [Nav]  │        <Outlet />                          │
│ [List] │                                            │
│        │                                            │
├────────┴───────────────────────────────────────────┤
│              Global Components                      │
│  - Toast Notifications                             │
│  - Upload Progress                                 │
│  - Dialogs/Modals                                  │
└────────────────────────────────────────────────────┘
```

### Layout Implementation

```typescript
export function Layout({ children }: { children: ReactNode }) {
  return (
    <div className="flex h-screen flex-col">
      <Header />
      <div className="flex flex-1 overflow-hidden">
        <Sidebar />
        <main className="flex-1 overflow-auto">
          {children}
        </main>
      </div>
    </div>
  );
}
```

## Component Patterns

### 1. Compound Components

For complex UI with shared state:

```typescript
// DashboardGrid manages layout state
export function DashboardGrid({ children }: Props) {
  const [layout, setLayout] = useState<Layout[]>([]);

  return (
    <GridContext.Provider value={{ layout, setLayout }}>
      <ReactGridLayout>
        {children}
      </ReactGridLayout>
    </GridContext.Provider>
  );
}

// DashboardWidget consumes context
export function DashboardWidget({ id, children }: Props) {
  const { layout } = useGridContext();
  // ...
}
```

### 2. Render Props

For flexible rendering:

```typescript
interface ChartWrapperProps {
  title: string;
  children: (data: ChartData) => ReactNode;
}

export function ChartWrapper({ title, children }: ChartWrapperProps) {
  const data = useChartData();

  return (
    <Card>
      <h3>{title}</h3>
      {children(data)}
    </Card>
  );
}

// Usage
<ChartWrapper title="Sales">
  {(data) => <LineChart data={data} />}
</ChartWrapper>
```

### 3. Custom Hooks

Extract reusable logic:

```typescript
// useWebSocket.ts
export function useWebSocket(url: string) {
  const [socket, setSocket] = useState<WebSocket | null>(null);
  const [messages, setMessages] = useState<string[]>([]);

  useEffect(() => {
    const ws = new WebSocket(url);
    ws.onmessage = (event) => {
      setMessages(prev => [...prev, event.data]);
    };
    setSocket(ws);
    return () => ws.close();
  }, [url]);

  return { socket, messages };
}

// Usage in component
function ChatPage() {
  const { messages } = useWebSocket('/ws/chat');
  return <MessageList messages={messages} />;
}
```

### 4. Higher-Order Components (Rarely Used)

Modern pattern: Use hooks instead of HOCs

```typescript
// Old pattern (avoid)
const withAuth = (Component) => {
  return (props) => {
    const isAuth = useAuth();
    return isAuth ? <Component {...props} /> : <Login />;
  };
};

// Modern pattern (preferred)
function ProtectedRoute({ children }) {
  const isAuth = useAuth();
  return isAuth ? children : <Navigate to="/login" />;
}
```

## Error Handling

### Error Boundaries

```typescript
// components/ui/ErrorBoundary.tsx
export class ErrorBoundary extends Component<Props, State> {
  state = { hasError: false };

  static getDerivedStateFromError(error: Error) {
    return { hasError: true };
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    console.error('Error caught:', error, info);
  }

  render() {
    if (this.state.hasError) {
      return <ErrorFallback />;
    }
    return this.props.children;
  }
}
```

### API Error Handling

```typescript
// TanStack Query automatically handles errors
const { data, error, isError } = useQuery({
  queryKey: ['documents'],
  queryFn: () => api.get('/documents'),
});

if (isError) {
  return <ErrorMessage error={error} />;
}
```

## Performance Optimization

### 1. Lazy Loading

```typescript
const DashboardsPage = lazy(() =>
  import('@/pages/DashboardsPage').then(m => ({ default: m.DashboardsPage }))
);
```

### 2. Memoization

```typescript
// Expensive computation
const processedData = useMemo(() => {
  return heavyComputation(data);
}, [data]);

// Prevent unnecessary re-renders
const MemoizedChart = memo(Chart);
```

### 3. Virtualization

For long lists (not yet implemented):

```typescript
import { useVirtualizer } from '@tanstack/react-virtual';

function MessageList({ messages }: Props) {
  const virtualizer = useVirtualizer({
    count: messages.length,
    getScrollElement: () => parentRef.current,
    estimateSize: () => 100,
  });
  // ...
}
```

### 4. Code Splitting

Vendor chunks are split in `vite.config.ts`:

```typescript
manualChunks: {
  'vendor-react': ['react', 'react-dom', 'react-router-dom'],
  'vendor-ui': ['@radix-ui/...', 'lucide-react'],
  'vendor-charts': ['recharts'],
  // ...
}
```

## Testing Architecture

### Component Testing Strategy

```typescript
// Component to test
export function Button({ onClick, children }: Props) {
  return <button onClick={onClick}>{children}</button>;
}

// Test (future implementation)
describe('Button', () => {
  it('renders children', () => {
    render(<Button>Click me</Button>);
    expect(screen.getByText('Click me')).toBeInTheDocument();
  });

  it('calls onClick when clicked', () => {
    const onClick = vi.fn();
    render(<Button onClick={onClick}>Click</Button>);
    fireEvent.click(screen.getByText('Click'));
    expect(onClick).toHaveBeenCalled();
  });
});
```

## Accessibility

### ARIA Patterns

Using Radix UI ensures accessible primitives:

```typescript
import * as Dialog from '@radix-ui/react-dialog';

export function Modal({ children }: Props) {
  return (
    <Dialog.Root>
      <Dialog.Trigger>Open</Dialog.Trigger>
      <Dialog.Portal>
        <Dialog.Overlay />
        <Dialog.Content>
          {children}
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  );
}
```

### Keyboard Navigation

Ensure all interactive elements are keyboard accessible:

```typescript
function ChatInput() {
  const handleKeyDown = (e: KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  return <textarea onKeyDown={handleKeyDown} />;
}
```

## Best Practices

1. **Keep components small** - Under 200 lines when possible
2. **Use TypeScript** - Type everything, avoid `any`
3. **Prefer composition** - Small, composable pieces
4. **Extract logic to hooks** - Reusable, testable logic
5. **Use semantic HTML** - `<button>`, `<nav>`, `<main>`
6. **Handle loading states** - Show spinners or skeletons
7. **Handle error states** - User-friendly error messages
8. **Optimize images** - Use appropriate formats and sizes
9. **Lazy load routes** - Reduce initial bundle size
10. **Document complex logic** - Comments for non-obvious code

## Next Steps

- [State Management Guide](./state-management.md) - Learn Zustand and TanStack Query patterns
- [Styling Guide](./styling-guide.md) - Tailwind CSS conventions
- [API Integration](./api-integration.md) - Backend communication patterns
