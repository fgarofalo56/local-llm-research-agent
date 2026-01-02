# State Management Guide

This guide explains when and how to use different state management solutions in the Local LLM Research Agent frontend.

## State Management Philosophy

We use a **layered approach** to state management, choosing the right tool for each type of state:

```
┌─────────────────────────────────────────────────┐
│  Local State (useState, useReducer)             │
│  - Form inputs, toggles, temporary UI state    │
└─────────────────────────────────────────────────┘
                   ↓
┌─────────────────────────────────────────────────┐
│  Zustand (Client State)                         │
│  - UI preferences, selections, edit modes       │
│  - Persisted to localStorage                    │
└─────────────────────────────────────────────────┘
                   ↓
┌─────────────────────────────────────────────────┐
│  TanStack Query (Server State)                  │
│  - API data, cached responses                   │
│  - Automatic refetching and invalidation        │
└─────────────────────────────────────────────────┘
                   ↓
┌─────────────────────────────────────────────────┐
│  React Context (Global Config)                  │
│  - Theme, rarely-changing settings              │
└─────────────────────────────────────────────────┘
```

## When to Use What

### Use Local State When

- State is only used in one component
- State doesn't need to persist
- Simple UI toggles (dropdown open/closed)
- Form input values before submission

**Example:**

```typescript
function SearchInput() {
  const [query, setQuery] = useState('');
  const [isOpen, setIsOpen] = useState(false);

  return (
    <input
      value={query}
      onChange={(e) => setQuery(e.target.value)}
      onFocus={() => setIsOpen(true)}
    />
  );
}
```

### Use Zustand When

- State needs to be shared across multiple components
- State should persist across component unmounts
- User preferences that should survive page reloads
- UI state like edit modes, selections, filters

**Example:**

```typescript
// Store definition
const useChatStore = create<ChatState>()(
  persist(
    (set) => ({
      selectedMCPServers: ['mssql'],
      toggleMCPServer: (serverId) =>
        set((state) => ({
          selectedMCPServers: state.selectedMCPServers.includes(serverId)
            ? state.selectedMCPServers.filter(id => id !== serverId)
            : [...state.selectedMCPServers, serverId],
        })),
    }),
    { name: 'chat-settings' }
  )
);

// Usage
function MCPSelector() {
  const selectedServers = useChatStore(s => s.selectedMCPServers);
  const toggleServer = useChatStore(s => s.toggleMCPServer);

  return (
    <div>
      {servers.map(server => (
        <Checkbox
          checked={selectedServers.includes(server.id)}
          onChange={() => toggleServer(server.id)}
        />
      ))}
    </div>
  );
}
```

### Use TanStack Query When

- Fetching data from the backend
- Need automatic caching and refetching
- Managing loading/error states for API calls
- Optimistic updates

**Example:**

```typescript
// Fetch documents
const { data, isLoading, error } = useQuery({
  queryKey: ['documents'],
  queryFn: () => api.get<Document[]>('/documents'),
});

// Create document
const mutation = useMutation({
  mutationFn: (file: File) => api.upload('/documents', file),
  onSuccess: () => {
    queryClient.invalidateQueries({ queryKey: ['documents'] });
  },
});
```

### Use React Context When

- Global configuration (theme, language)
- Values that rarely change
- Deeply nested component trees need same data
- Avoid prop drilling for static config

**Example:**

```typescript
const ThemeContext = createContext<ThemeContextType>(undefined);

export function ThemeProvider({ children }: Props) {
  const [mode, setMode] = useState<ThemeMode>('dark');

  return (
    <ThemeContext.Provider value={{ mode, setMode }}>
      {children}
    </ThemeContext.Provider>
  );
}

export function useTheme() {
  return useContext(ThemeContext);
}
```

## Zustand Patterns

### Store Structure

```typescript
import { create } from 'zustand';
import { persist } from 'zustand/middleware';

interface ChatState {
  // State
  messages: Message[];
  isStreaming: boolean;
  selectedModel: string;

  // Actions
  setMessages: (messages: Message[]) => void;
  addMessage: (message: Message) => void;
  setSelectedModel: (model: string) => void;
}

export const useChatStore = create<ChatState>()(
  persist(
    (set) => ({
      // Initial state
      messages: [],
      isStreaming: false,
      selectedModel: 'qwen3:30b',

      // Actions
      setMessages: (messages) => set({ messages }),
      addMessage: (message) =>
        set((state) => ({ messages: [...state.messages, message] })),
      setSelectedModel: (selectedModel) => set({ selectedModel }),
    }),
    {
      name: 'chat-settings',
      // Only persist certain fields
      partialize: (state) => ({
        selectedModel: state.selectedModel,
      }),
    }
  )
);
```

### Selecting State

**Use selectors to prevent unnecessary re-renders:**

```typescript
// Bad: Re-renders on any state change
function Component() {
  const state = useChatStore();
  return <div>{state.selectedModel}</div>;
}

// Good: Only re-renders when selectedModel changes
function Component() {
  const selectedModel = useChatStore(s => s.selectedModel);
  return <div>{selectedModel}</div>;
}
```

### Computed Values

**Use selectors for derived state:**

```typescript
// Store
export const useChatStore = create<ChatState>((set, get) => ({
  messages: [],

  // Computed value
  messageCount: () => get().messages.length,
}));

// Usage
function MessageCounter() {
  const count = useChatStore(s => s.messageCount());
  return <span>{count} messages</span>;
}
```

### Async Actions

```typescript
export const useUploadStore = create<UploadState>((set, get) => ({
  uploads: [],
  isProcessing: false,

  processQueue: async () => {
    set({ isProcessing: true });

    const pendingUpload = get().uploads.find(u => u.status === 'pending');

    if (pendingUpload) {
      try {
        const result = await api.upload('/documents', pendingUpload.file);
        // Update state after async operation
        set((state) => ({
          uploads: state.uploads.map(u =>
            u.id === pendingUpload.id
              ? { ...u, status: 'completed', result }
              : u
          ),
        }));
      } catch (error) {
        set((state) => ({
          uploads: state.uploads.map(u =>
            u.id === pendingUpload.id
              ? { ...u, status: 'failed', error }
              : u
          ),
        }));
      }
    }

    set({ isProcessing: false });
  },
}));
```

### Multiple Stores

Organize by domain:

```typescript
// stores/chatStore.ts
export const useChatStore = create<ChatState>(/* ... */);

// stores/dashboardStore.ts
export const useDashboardStore = create<DashboardState>(/* ... */);

// stores/uploadStore.ts
export const useUploadStore = create<UploadState>(/* ... */);
```

### Store Best Practices

1. **Keep stores focused** - One store per feature domain
2. **Actions over direct mutations** - `addMessage()` not `set({ messages: [...] })`
3. **Use partialize for persistence** - Only persist what's needed
4. **Avoid deeply nested state** - Flatten when possible
5. **Use TypeScript** - Full type safety for state and actions

## TanStack Query Patterns

### Basic Query

```typescript
import { useQuery } from '@tanstack/react-query';
import { api } from '@/api/client';

function DocumentList() {
  const { data, isLoading, error } = useQuery({
    queryKey: ['documents'],
    queryFn: () => api.get<Document[]>('/documents'),
    staleTime: 1000 * 60, // 1 minute
    retry: 1,
  });

  if (isLoading) return <LoadingSpinner />;
  if (error) return <ErrorMessage error={error} />;

  return (
    <ul>
      {data?.map(doc => <DocumentItem key={doc.id} doc={doc} />)}
    </ul>
  );
}
```

### Query with Parameters

```typescript
function ConversationView({ conversationId }: Props) {
  const { data } = useQuery({
    queryKey: ['conversation', conversationId],
    queryFn: () => api.get(`/conversations/${conversationId}`),
    enabled: !!conversationId, // Only run if ID exists
  });

  return <div>{/* ... */}</div>;
}
```

### Mutations

```typescript
import { useMutation, useQueryClient } from '@tanstack/react-query';

function DocumentUpload() {
  const queryClient = useQueryClient();

  const mutation = useMutation({
    mutationFn: (file: File) => api.upload('/documents', file),
    onSuccess: () => {
      // Invalidate and refetch documents list
      queryClient.invalidateQueries({ queryKey: ['documents'] });
    },
    onError: (error) => {
      console.error('Upload failed:', error);
    },
  });

  const handleUpload = (file: File) => {
    mutation.mutate(file);
  };

  return (
    <div>
      <input type="file" onChange={(e) => handleUpload(e.target.files![0])} />
      {mutation.isPending && <LoadingSpinner />}
      {mutation.isError && <ErrorMessage error={mutation.error} />}
      {mutation.isSuccess && <SuccessMessage />}
    </div>
  );
}
```

### Optimistic Updates

```typescript
const mutation = useMutation({
  mutationFn: (newMessage: Message) => api.post('/messages', newMessage),
  onMutate: async (newMessage) => {
    // Cancel any outgoing refetches
    await queryClient.cancelQueries({ queryKey: ['messages'] });

    // Snapshot previous value
    const previous = queryClient.getQueryData(['messages']);

    // Optimistically update
    queryClient.setQueryData(['messages'], (old: Message[]) => [
      ...old,
      { ...newMessage, id: -1, created_at: new Date().toISOString() },
    ]);

    return { previous };
  },
  onError: (err, newMessage, context) => {
    // Rollback on error
    queryClient.setQueryData(['messages'], context?.previous);
  },
  onSettled: () => {
    // Always refetch after error or success
    queryClient.invalidateQueries({ queryKey: ['messages'] });
  },
});
```

### Polling

```typescript
const { data } = useQuery({
  queryKey: ['documents'],
  queryFn: () => api.get('/documents'),
  refetchInterval: 5000, // Poll every 5 seconds
  refetchIntervalInBackground: true,
});
```

### Dependent Queries

```typescript
function DocumentDetails({ documentId }: Props) {
  // First query
  const { data: document } = useQuery({
    queryKey: ['document', documentId],
    queryFn: () => api.get(`/documents/${documentId}`),
  });

  // Second query depends on first
  const { data: chunks } = useQuery({
    queryKey: ['chunks', documentId],
    queryFn: () => api.get(`/documents/${documentId}/chunks`),
    enabled: !!document, // Only run after document is loaded
  });

  return <div>{/* ... */}</div>;
}
```

### Pagination

```typescript
function DocumentList() {
  const [page, setPage] = useState(1);

  const { data, isLoading } = useQuery({
    queryKey: ['documents', page],
    queryFn: () => api.get(`/documents?page=${page}`),
    keepPreviousData: true, // Keep old data while fetching new page
  });

  return (
    <div>
      {data?.items.map(doc => <DocumentItem key={doc.id} doc={doc} />)}
      <Pagination
        page={page}
        onPageChange={setPage}
        hasMore={data?.has_next}
      />
    </div>
  );
}
```

### Infinite Queries

```typescript
import { useInfiniteQuery } from '@tanstack/react-query';

function MessageList() {
  const {
    data,
    fetchNextPage,
    hasNextPage,
    isFetchingNextPage,
  } = useInfiniteQuery({
    queryKey: ['messages'],
    queryFn: ({ pageParam = 1 }) =>
      api.get(`/messages?page=${pageParam}`),
    getNextPageParam: (lastPage) =>
      lastPage.has_next ? lastPage.page + 1 : undefined,
  });

  return (
    <div>
      {data?.pages.map((page) =>
        page.items.map((msg) => <Message key={msg.id} {...msg} />)
      )}
      {hasNextPage && (
        <button onClick={() => fetchNextPage()}>
          {isFetchingNextPage ? 'Loading...' : 'Load More'}
        </button>
      )}
    </div>
  );
}
```

### Query Invalidation Strategies

```typescript
const queryClient = useQueryClient();

// Invalidate specific query
queryClient.invalidateQueries({ queryKey: ['documents'] });

// Invalidate all queries matching a prefix
queryClient.invalidateQueries({ queryKey: ['documents'] });

// Invalidate all queries
queryClient.invalidateQueries();

// Remove query from cache
queryClient.removeQueries({ queryKey: ['documents', docId] });

// Set query data manually
queryClient.setQueryData(['document', docId], newDocument);
```

### TanStack Query Best Practices

1. **Use consistent query keys** - `['resource', id]` pattern
2. **Enable queries conditionally** - `enabled: !!id`
3. **Set appropriate stale times** - Balance freshness vs requests
4. **Handle loading and error states** - Always show user feedback
5. **Invalidate on mutations** - Keep data fresh after changes
6. **Use optimistic updates** - Better UX for fast interactions
7. **Leverage query prefetching** - Preload data on hover

## Combining Zustand and TanStack Query

Use both together for best results:

```typescript
function ChatPage() {
  // Zustand: UI state
  const selectedModel = useChatStore(s => s.selectedModel);
  const setSelectedModel = useChatStore(s => s.setSelectedModel);

  // TanStack Query: Server data
  const { data: messages } = useQuery({
    queryKey: ['messages', selectedModel],
    queryFn: () => api.get(`/messages?model=${selectedModel}`),
  });

  return (
    <div>
      <ModelSelector
        value={selectedModel}
        onChange={setSelectedModel}
      />
      <MessageList messages={messages ?? []} />
    </div>
  );
}
```

## React Context Patterns

### Context Setup

```typescript
// contexts/ThemeContext.tsx
import { createContext, useContext, useState, ReactNode } from 'react';

type ThemeMode = 'dark' | 'light' | 'system';

interface ThemeContextType {
  mode: ThemeMode;
  setMode: (mode: ThemeMode) => void;
  resolvedMode: 'dark' | 'light';
}

const ThemeContext = createContext<ThemeContextType | undefined>(undefined);

export function ThemeProvider({ children }: { children: ReactNode }) {
  const [mode, setMode] = useState<ThemeMode>('dark');

  const resolvedMode = mode === 'system'
    ? window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'
    : mode;

  return (
    <ThemeContext.Provider value={{ mode, setMode, resolvedMode }}>
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
```

### Context Usage

```typescript
function ThemeToggle() {
  const { mode, setMode } = useTheme();

  return (
    <button onClick={() => setMode(mode === 'dark' ? 'light' : 'dark')}>
      Toggle Theme
    </button>
  );
}
```

### Context Best Practices

1. **Create custom hook** - `useTheme()` instead of `useContext(ThemeContext)`
2. **Throw error if used outside provider** - Catch mistakes early
3. **Split contexts by concern** - Don't put everything in one context
4. **Memoize values** - Prevent unnecessary re-renders
5. **Consider alternatives** - Zustand might be simpler

## WebSocket State Management

For real-time features like streaming chat:

```typescript
function ChatPage() {
  const [socket, setSocket] = useState<WebSocket | null>(null);
  const [streamingContent, setStreamingContent] = useState('');
  const addMessage = useChatStore(s => s.addMessage);

  useEffect(() => {
    const ws = new WebSocket(`ws://localhost:8000/ws/chat/${conversationId}`);

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);

      if (data.type === 'stream') {
        // Append streaming content
        setStreamingContent(prev => prev + data.content);
      } else if (data.type === 'complete') {
        // Save complete message to store
        addMessage(data.message);
        setStreamingContent('');
      }
    };

    setSocket(ws);
    return () => ws.close();
  }, [conversationId, addMessage]);

  return (
    <div>
      <MessageList />
      {streamingContent && <StreamingMessage content={streamingContent} />}
    </div>
  );
}
```

## State Synchronization

Sync Zustand with TanStack Query when needed:

```typescript
function DocumentsPage() {
  const { data: documents } = useQuery({
    queryKey: ['documents'],
    queryFn: () => api.get('/documents'),
  });

  const uploads = useUploadStore(s => s.uploads);
  const updateUploadStatus = useUploadStore(s => s.updateUploadStatus);

  // Sync processing status from API to upload store
  useEffect(() => {
    if (documents) {
      uploads.forEach(upload => {
        if (upload.status === 'processing' && upload.documentId) {
          const doc = documents.find(d => d.id === upload.documentId);
          if (doc?.processing_status === 'completed') {
            updateUploadStatus(upload.id, { status: 'completed' });
          }
        }
      });
    }
  }, [documents, uploads, updateUploadStatus]);

  return <div>{/* ... */}</div>;
}
```

## Performance Considerations

### Selector Optimization

```typescript
// Bad: New object on every render causes re-renders
const state = useChatStore(s => ({ model: s.selectedModel, temp: s.temperature }));

// Good: Only re-render when values actually change
const selectedModel = useChatStore(s => s.selectedModel);
const temperature = useChatStore(s => s.temperature);

// Or use shallow equality
import { shallow } from 'zustand/shallow';
const { selectedModel, temperature } = useChatStore(
  s => ({ selectedModel: s.selectedModel, temperature: s.temperature }),
  shallow
);
```

### Query Caching

```typescript
// Configure cache times
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 1000 * 60, // 1 minute
      cacheTime: 1000 * 60 * 5, // 5 minutes
      retry: 1,
    },
  },
});
```

## Debugging

### Zustand DevTools

```typescript
import { devtools } from 'zustand/middleware';

export const useChatStore = create<ChatState>()(
  devtools(
    persist(
      (set) => ({ /* ... */ }),
      { name: 'chat-settings' }
    ),
    { name: 'ChatStore' }
  )
);
```

### TanStack Query DevTools

```typescript
import { ReactQueryDevtools } from '@tanstack/react-query-devtools';

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <App />
      <ReactQueryDevtools initialIsOpen={false} />
    </QueryClientProvider>
  );
}
```

## Summary

| State Type | Tool | Use Case |
|------------|------|----------|
| Component-local | useState | Temporary UI state |
| Shared UI state | Zustand | Selections, preferences, edit modes |
| Server data | TanStack Query | API responses, caching |
| Global config | React Context | Theme, rarely-changing settings |
| Real-time data | WebSocket + useState | Streaming responses |

**General Rule:** Start with local state, move to Zustand for shared state, use TanStack Query for all server data.
