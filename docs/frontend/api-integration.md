# API Integration Guide

This guide covers how the frontend communicates with the FastAPI backend, including REST API patterns, WebSocket integration, error handling, and best practices.

## API Architecture

```
┌─────────────────────────────────────────────────┐
│            React Components                      │
└───────────────┬─────────────────────────────────┘
                │
                ↓
┌─────────────────────────────────────────────────┐
│         TanStack Query Hooks                     │
│  (useQuery, useMutation)                        │
└───────────────┬─────────────────────────────────┘
                │
                ↓
┌─────────────────────────────────────────────────┐
│           API Client Layer                       │
│  (src/api/client.ts)                            │
└───────────────┬─────────────────────────────────┘
                │
                ↓
┌─────────────────────────────────────────────────┐
│            Fetch API / WebSocket                 │
└───────────────┬─────────────────────────────────┘
                │
                ↓
┌─────────────────────────────────────────────────┐
│        FastAPI Backend (Port 8000)               │
│  - REST endpoints (/api/*)                      │
│  - WebSocket endpoints (/ws/*)                  │
└─────────────────────────────────────────────────┘
```

## API Client

### Base Client Implementation

```typescript
// src/api/client.ts
const API_BASE = '/api';

interface ApiError {
  detail: string;
  status: number;
}

async function handleResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const error: ApiError = {
      detail: 'An error occurred',
      status: response.status,
    };
    try {
      const data = await response.json();
      error.detail = data.detail || data.message || error.detail;
    } catch {
      // Ignore JSON parse errors
    }
    throw error;
  }
  return response.json();
}

export const api = {
  get: async <T>(path: string): Promise<T> => {
    const response = await fetch(`${API_BASE}${path}`);
    return handleResponse<T>(response);
  },

  post: async <T>(path: string, data?: unknown): Promise<T> => {
    const response = await fetch(`${API_BASE}${path}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: data ? JSON.stringify(data) : undefined,
    });
    return handleResponse<T>(response);
  },

  put: async <T>(path: string, data: unknown): Promise<T> => {
    const response = await fetch(`${API_BASE}${path}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    return handleResponse<T>(response);
  },

  patch: async <T>(path: string, data: unknown): Promise<T> => {
    const response = await fetch(`${API_BASE}${path}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    return handleResponse<T>(response);
  },

  delete: async <T>(path: string): Promise<T> => {
    const response = await fetch(`${API_BASE}${path}`, {
      method: 'DELETE',
    });
    return handleResponse<T>(response);
  },
};
```

### File Upload

```typescript
// Simple upload
upload: async <T>(path: string, file: File): Promise<T> => {
  const formData = new FormData();
  formData.append('file', file);
  const response = await fetch(`${API_BASE}${path}`, {
    method: 'POST',
    body: formData,
  });
  return handleResponse<T>(response);
},

// Upload with progress tracking
uploadWithProgress: <T>(
  path: string,
  file: File,
  onProgress: (percent: number) => void
): Promise<T> => {
  return new Promise((resolve, reject) => {
    const xhr = new XMLHttpRequest();
    const formData = new FormData();
    formData.append('file', file);

    xhr.upload.addEventListener('progress', (event) => {
      if (event.lengthComputable) {
        const percent = Math.round((event.loaded / event.total) * 100);
        onProgress(percent);
      }
    });

    xhr.addEventListener('load', () => {
      if (xhr.status >= 200 && xhr.status < 300) {
        try {
          const data = JSON.parse(xhr.responseText);
          resolve(data as T);
        } catch {
          reject({ detail: 'Failed to parse response', status: xhr.status });
        }
      } else {
        try {
          const error = JSON.parse(xhr.responseText);
          reject({ detail: error.detail || 'Upload failed', status: xhr.status });
        } catch {
          reject({ detail: 'Upload failed', status: xhr.status });
        }
      }
    });

    xhr.addEventListener('error', () => {
      reject({ detail: 'Network error during upload', status: 0 });
    });

    xhr.open('POST', `${API_BASE}${path}`);
    xhr.send(formData);
  });
},
```

## REST API Patterns

### GET Requests

```typescript
// Fetch all documents
const { data, isLoading, error } = useQuery({
  queryKey: ['documents'],
  queryFn: () => api.get<Document[]>('/documents'),
});

// Fetch single document with ID
const { data: document } = useQuery({
  queryKey: ['document', documentId],
  queryFn: () => api.get<Document>(`/documents/${documentId}`),
  enabled: !!documentId,
});

// Fetch with query parameters
const { data } = useQuery({
  queryKey: ['documents', { tags, status }],
  queryFn: () => {
    const params = new URLSearchParams();
    if (tags.length) params.append('tags', tags.join(','));
    if (status) params.append('status', status);
    return api.get<Document[]>(`/documents?${params}`);
  },
});
```

### POST Requests

```typescript
// Create new conversation
const mutation = useMutation({
  mutationFn: (title: string) =>
    api.post<Conversation>('/conversations', { title }),
  onSuccess: (newConversation) => {
    queryClient.invalidateQueries({ queryKey: ['conversations'] });
    navigate(`/chat/${newConversation.id}`);
  },
});

// Usage
mutation.mutate('New conversation title');
```

### PUT Requests

```typescript
// Update conversation
const mutation = useMutation({
  mutationFn: ({ id, updates }: { id: number; updates: Partial<Conversation> }) =>
    api.put<Conversation>(`/conversations/${id}`, updates),
  onSuccess: (updated) => {
    queryClient.setQueryData(['conversation', updated.id], updated);
    queryClient.invalidateQueries({ queryKey: ['conversations'] });
  },
});

// Usage
mutation.mutate({ id: conversationId, updates: { title: 'New title' } });
```

### PATCH Requests

```typescript
// Partial update
const mutation = useMutation({
  mutationFn: (messageId: number) =>
    api.patch(`/messages/${messageId}/rating`, { rating: 'up' }),
  onSuccess: () => {
    queryClient.invalidateQueries({ queryKey: ['messages'] });
  },
});
```

### DELETE Requests

```typescript
// Delete document
const mutation = useMutation({
  mutationFn: (documentId: number) =>
    api.delete(`/documents/${documentId}`),
  onSuccess: () => {
    queryClient.invalidateQueries({ queryKey: ['documents'] });
  },
  onError: (error: ApiError) => {
    console.error('Delete failed:', error.detail);
  },
});

// Usage with confirmation
const handleDelete = (id: number) => {
  if (confirm('Are you sure?')) {
    mutation.mutate(id);
  }
};
```

## WebSocket Integration

### Basic WebSocket Connection

```typescript
import { useEffect, useState } from 'react';

function useWebSocket(url: string) {
  const [socket, setSocket] = useState<WebSocket | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const [error, setError] = useState<Error | null>(null);

  useEffect(() => {
    const ws = new WebSocket(url);

    ws.onopen = () => {
      setIsConnected(true);
      setError(null);
    };

    ws.onerror = (event) => {
      setError(new Error('WebSocket error'));
      console.error('WebSocket error:', event);
    };

    ws.onclose = () => {
      setIsConnected(false);
    };

    setSocket(ws);

    return () => {
      ws.close();
    };
  }, [url]);

  return { socket, isConnected, error };
}
```

### Chat WebSocket Pattern

```typescript
interface StreamMessage {
  type: 'stream' | 'complete' | 'error';
  content?: string;
  message?: Message;
  error?: string;
}

function ChatPage() {
  const { conversationId } = useParams();
  const [messages, setMessages] = useState<Message[]>([]);
  const [streamingContent, setStreamingContent] = useState('');
  const [isStreaming, setIsStreaming] = useState(false);

  useEffect(() => {
    if (!conversationId) return;

    const ws = new WebSocket(
      `ws://localhost:8000/ws/agent/${conversationId}`
    );

    ws.onmessage = (event) => {
      const data: StreamMessage = JSON.parse(event.data);

      if (data.type === 'stream') {
        setIsStreaming(true);
        setStreamingContent(prev => prev + data.content);
      } else if (data.type === 'complete') {
        setIsStreaming(false);
        setMessages(prev => [...prev, data.message!]);
        setStreamingContent('');
      } else if (data.type === 'error') {
        setIsStreaming(false);
        console.error('Stream error:', data.error);
      }
    };

    return () => ws.close();
  }, [conversationId]);

  const sendMessage = (content: string) => {
    if (!socket || !socket.OPEN) return;

    socket.send(JSON.stringify({
      content,
      model: selectedModel,
      mcp_servers: selectedMCPServers,
    }));
  };

  return (
    <div>
      <MessageList messages={messages} />
      {isStreaming && <StreamingMessage content={streamingContent} />}
      <ChatInput onSubmit={sendMessage} disabled={isStreaming} />
    </div>
  );
}
```

### WebSocket Reconnection

```typescript
function useReconnectingWebSocket(url: string, maxRetries = 5) {
  const [socket, setSocket] = useState<WebSocket | null>(null);
  const [retries, setRetries] = useState(0);

  useEffect(() => {
    let ws: WebSocket;
    let reconnectTimeout: NodeJS.Timeout;

    const connect = () => {
      ws = new WebSocket(url);

      ws.onopen = () => {
        setSocket(ws);
        setRetries(0);
      };

      ws.onclose = () => {
        setSocket(null);
        if (retries < maxRetries) {
          reconnectTimeout = setTimeout(() => {
            setRetries(r => r + 1);
            connect();
          }, Math.min(1000 * Math.pow(2, retries), 10000));
        }
      };
    };

    connect();

    return () => {
      clearTimeout(reconnectTimeout);
      ws?.close();
    };
  }, [url, retries, maxRetries]);

  return { socket, retries };
}
```

## Error Handling

### API Error Types

```typescript
interface ApiError {
  detail: string;
  status: number;
}

interface ValidationError extends ApiError {
  detail: string;
  validation_errors?: {
    field: string;
    message: string;
  }[];
}
```

### Component-Level Error Handling

```typescript
function DocumentList() {
  const { data, isLoading, error, isError } = useQuery({
    queryKey: ['documents'],
    queryFn: () => api.get<Document[]>('/documents'),
  });

  if (isLoading) {
    return <LoadingSpinner />;
  }

  if (isError) {
    return (
      <ErrorMessage>
        {error.detail || 'Failed to load documents'}
      </ErrorMessage>
    );
  }

  return (
    <ul>
      {data?.map(doc => <DocumentItem key={doc.id} doc={doc} />)}
    </ul>
  );
}
```

### Mutation Error Handling

```typescript
const mutation = useMutation({
  mutationFn: (file: File) => api.upload('/documents', file),
  onError: (error: ApiError) => {
    if (error.status === 413) {
      toast.error('File too large. Maximum size is 50MB.');
    } else if (error.status === 415) {
      toast.error('Unsupported file type.');
    } else {
      toast.error(error.detail || 'Upload failed');
    }
  },
  onSuccess: () => {
    toast.success('File uploaded successfully');
  },
});
```

### Global Error Handling

```typescript
// App.tsx
import { QueryCache, QueryClient } from '@tanstack/react-query';

const queryClient = new QueryClient({
  queryCache: new QueryCache({
    onError: (error) => {
      console.error('Global query error:', error);
      // Show global error notification
    },
  }),
  defaultOptions: {
    queries: {
      retry: (failureCount, error: ApiError) => {
        // Don't retry on 4xx errors
        if (error.status >= 400 && error.status < 500) {
          return false;
        }
        return failureCount < 3;
      },
    },
  },
});
```

## Loading States

### Query Loading States

```typescript
function DocumentList() {
  const { data, isLoading, isFetching, isRefetching } = useQuery({
    queryKey: ['documents'],
    queryFn: () => api.get<Document[]>('/documents'),
  });

  // Initial load
  if (isLoading) {
    return <LoadingSpinner />;
  }

  return (
    <div>
      {/* Show indicator when refetching in background */}
      {isFetching && !isLoading && (
        <div className="text-sm text-muted-foreground">Updating...</div>
      )}
      <DocumentGrid documents={data ?? []} />
    </div>
  );
}
```

### Mutation Loading States

```typescript
function UploadButton() {
  const mutation = useMutation({
    mutationFn: (file: File) => api.upload('/documents', file),
  });

  return (
    <button
      onClick={() => mutation.mutate(selectedFile)}
      disabled={mutation.isPending}
    >
      {mutation.isPending ? (
        <>
          <Spinner className="mr-2" />
          Uploading...
        </>
      ) : (
        'Upload'
      )}
    </button>
  );
}
```

### Skeleton Loading

```typescript
function DocumentList() {
  const { data, isLoading } = useQuery({
    queryKey: ['documents'],
    queryFn: () => api.get<Document[]>('/documents'),
  });

  if (isLoading) {
    return (
      <div className="space-y-4">
        {Array.from({ length: 5 }).map((_, i) => (
          <div key={i} className="flex gap-4">
            <div className="h-20 w-20 bg-muted animate-pulse rounded" />
            <div className="flex-1 space-y-2">
              <div className="h-4 bg-muted animate-pulse rounded w-3/4" />
              <div className="h-3 bg-muted animate-pulse rounded w-1/2" />
            </div>
          </div>
        ))}
      </div>
    );
  }

  return <DocumentGrid documents={data ?? []} />;
}
```

## Request Cancellation

### Abort Controller

```typescript
function SearchResults({ query }: Props) {
  const { data } = useQuery({
    queryKey: ['search', query],
    queryFn: async ({ signal }) => {
      const response = await fetch(`/api/search?q=${query}`, { signal });
      if (!response.ok) throw new Error('Search failed');
      return response.json();
    },
    enabled: query.length > 2,
  });

  return <ResultsList results={data ?? []} />;
}
```

TanStack Query automatically cancels previous requests when the query key changes.

## Caching Strategies

### Cache Configuration

```typescript
// Global defaults
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 1000 * 60, // 1 minute
      cacheTime: 1000 * 60 * 5, // 5 minutes
      refetchOnWindowFocus: true,
      refetchOnReconnect: true,
      retry: 1,
    },
  },
});

// Per-query configuration
useQuery({
  queryKey: ['user-profile'],
  queryFn: () => api.get('/user/profile'),
  staleTime: 1000 * 60 * 5, // 5 minutes (rarely changes)
  cacheTime: Infinity, // Keep in cache forever
});

useQuery({
  queryKey: ['notifications'],
  queryFn: () => api.get('/notifications'),
  staleTime: 0, // Always stale, refetch on mount
  refetchInterval: 30000, // Poll every 30 seconds
});
```

### Cache Invalidation

```typescript
// Invalidate specific query
queryClient.invalidateQueries({ queryKey: ['documents'] });

// Invalidate all queries with prefix
queryClient.invalidateQueries({ queryKey: ['documents'] }); // Matches ['documents'], ['documents', id], etc.

// Invalidate exact match only
queryClient.invalidateQueries({
  queryKey: ['document', documentId],
  exact: true,
});

// Refetch immediately
queryClient.invalidateQueries({
  queryKey: ['documents'],
  refetchType: 'active', // Only refetch active queries
});
```

### Manual Cache Updates

```typescript
// Update cache after mutation
const mutation = useMutation({
  mutationFn: (newDoc: Document) => api.post('/documents', newDoc),
  onSuccess: (createdDoc) => {
    // Add to list cache
    queryClient.setQueryData<Document[]>(['documents'], (old) => [
      createdDoc,
      ...(old ?? []),
    ]);

    // Set individual item cache
    queryClient.setQueryData(['document', createdDoc.id], createdDoc);
  },
});
```

## Prefetching

### Hover Prefetch

```typescript
function DocumentLink({ documentId }: Props) {
  const queryClient = useQueryClient();

  const prefetchDocument = () => {
    queryClient.prefetchQuery({
      queryKey: ['document', documentId],
      queryFn: () => api.get(`/documents/${documentId}`),
    });
  };

  return (
    <Link
      to={`/documents/${documentId}`}
      onMouseEnter={prefetchDocument}
    >
      View Document
    </Link>
  );
}
```

### Route Prefetch

```typescript
function Navigation() {
  const queryClient = useQueryClient();

  useEffect(() => {
    // Prefetch likely next routes
    queryClient.prefetchQuery({
      queryKey: ['documents'],
      queryFn: () => api.get('/documents'),
    });
  }, [queryClient]);

  return <nav>{/* ... */}</nav>;
}
```

## Type Safety

### API Response Types

```typescript
// types/index.ts
export interface Document {
  id: number;
  filename: string;
  file_size: number;
  processing_status: 'pending' | 'processing' | 'completed' | 'failed';
  created_at: string;
}

export interface Message {
  id: number;
  conversation_id: number;
  role: 'user' | 'assistant' | 'system';
  content: string;
  created_at: string;
}

export interface Conversation {
  id: number;
  title: string | null;
  created_at: string;
  updated_at: string;
  is_archived: boolean;
}
```

### Typed API Calls

```typescript
// Always specify return type
const { data } = useQuery({
  queryKey: ['documents'],
  queryFn: () => api.get<Document[]>('/documents'),
  //                          ^^^^^^^^^^^ Type parameter
});

// data is now typed as Document[] | undefined

// With transformation
const { data } = useQuery({
  queryKey: ['documents'],
  queryFn: async () => {
    const docs = await api.get<Document[]>('/documents');
    return docs.filter(d => d.processing_status === 'completed');
  },
});
// data is still Document[] | undefined
```

## Best Practices

### 1. Use Consistent Query Keys

```typescript
// Good: Hierarchical structure
['documents']
['documents', documentId]
['documents', documentId, 'chunks']

// Good: Include filters
['documents', { status: 'completed', tags: ['ml'] }]

// Bad: Inconsistent
['docs']
['allDocuments']
['fetchDocuments']
```

### 2. Handle Loading and Error States

```typescript
// Always handle all states
function Component() {
  const { data, isLoading, error, isError } = useQuery({...});

  if (isLoading) return <LoadingState />;
  if (isError) return <ErrorState error={error} />;

  return <SuccessState data={data} />;
}
```

### 3. Debounce Search Queries

```typescript
import { useDeferredValue } from 'react';

function SearchResults({ query }: Props) {
  const deferredQuery = useDeferredValue(query);

  const { data } = useQuery({
    queryKey: ['search', deferredQuery],
    queryFn: () => api.get(`/search?q=${deferredQuery}`),
    enabled: deferredQuery.length > 2,
  });

  return <ResultsList results={data ?? []} />;
}
```

### 4. Optimistic Updates for Better UX

```typescript
const mutation = useMutation({
  mutationFn: (updates: Partial<Document>) =>
    api.patch(`/documents/${id}`, updates),
  onMutate: async (updates) => {
    await queryClient.cancelQueries({ queryKey: ['document', id] });
    const previous = queryClient.getQueryData(['document', id]);
    queryClient.setQueryData(['document', id], (old: Document) => ({
      ...old,
      ...updates,
    }));
    return { previous };
  },
  onError: (err, variables, context) => {
    queryClient.setQueryData(['document', id], context?.previous);
  },
});
```

### 5. Use Enabled for Conditional Fetching

```typescript
// Only fetch when ID is available
const { data } = useQuery({
  queryKey: ['document', documentId],
  queryFn: () => api.get(`/documents/${documentId}`),
  enabled: !!documentId,
});

// Only fetch when user is authenticated
const { data } = useQuery({
  queryKey: ['user-data'],
  queryFn: () => api.get('/user/data'),
  enabled: isAuthenticated,
});
```

### 6. Proper Error Messages

```typescript
// Convert API errors to user-friendly messages
const getErrorMessage = (error: ApiError): string => {
  if (error.status === 404) return 'Resource not found';
  if (error.status === 403) return 'You do not have permission';
  if (error.status >= 500) return 'Server error. Please try again later.';
  return error.detail || 'An error occurred';
};

function Component() {
  const { error } = useQuery({...});

  if (error) {
    return <ErrorMessage>{getErrorMessage(error)}</ErrorMessage>;
  }
}
```

## Testing API Integration

### Mock API Calls

```typescript
import { vi } from 'vitest';
import { api } from '@/api/client';

vi.mock('@/api/client', () => ({
  api: {
    get: vi.fn(),
    post: vi.fn(),
    put: vi.fn(),
    delete: vi.fn(),
  },
}));

describe('DocumentList', () => {
  it('renders documents', async () => {
    vi.mocked(api.get).mockResolvedValue([
      { id: 1, filename: 'test.pdf' },
    ]);

    render(<DocumentList />);

    expect(await screen.findByText('test.pdf')).toBeInTheDocument();
  });
});
```

## Resources

- [TanStack Query Docs](https://tanstack.com/query/latest)
- [Fetch API MDN](https://developer.mozilla.org/en-US/docs/Web/API/Fetch_API)
- [WebSocket API MDN](https://developer.mozilla.org/en-US/docs/Web/API/WebSocket)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)

## Next Steps

- Review [State Management](./state-management.md) for Zustand and React Query patterns
- Check [Architecture](./architecture.md) for component structure
- See [Styling Guide](./styling-guide.md) for UI patterns
