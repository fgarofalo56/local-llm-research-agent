# Chat Components

Real-time chat interface components with markdown rendering, syntax highlighting, and interactive features.

## Overview

Chat components provide a modern chat interface for interacting with the AI research agent. Features include:

- Real-time streaming responses
- Rich markdown formatting
- Syntax-highlighted code blocks
- Message rating and feedback
- Source citations
- Copy to clipboard
- MCP server selection

---

## ChatInput

Text input component for composing and sending chat messages.

### Props

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `onSend` | `(content: string) => void` | Required | Callback when message is sent |

### Usage Example

```tsx
import { ChatInput } from '@/components/chat/ChatInput';

function ChatPage() {
  const handleSend = (content: string) => {
    console.log('Sending:', content);
    // Send to API
  };

  return <ChatInput onSend={handleSend} />;
}
```

### Features

**Auto-expanding Textarea**
- Starts at 3 rows
- Supports multi-line input

**Keyboard Shortcuts**
- `Enter` - Send message
- `Shift + Enter` - New line

**State Management**
- Integrates with `useChatStore()` for streaming state
- Disabled during streaming responses
- Auto-clears after sending

### Accessibility
- Proper textarea label (via placeholder)
- Disabled state when streaming
- Focus management

### Notes
- **Trim Whitespace**: Messages trimmed before sending
- **Empty Prevention**: Cannot send empty messages
- **Stream Awareness**: Input disabled during AI response

---

## MessageList

Displays chat message history with rich formatting and interactive features.

### Props

No props required. Uses Zustand store for state management.

### Usage Example

```tsx
import { MessageList } from '@/components/chat/MessageList';

function ChatPage() {
  return (
    <div className="flex-1 overflow-auto">
      <MessageList />
    </div>
  );
}
```

### Features

**Rich Markdown Rendering**
- GitHub Flavored Markdown (GFM) support
- Syntax-highlighted code blocks
- Tables with enhanced styling
- Lists, blockquotes, headings
- External links open in new tabs

**Message Actions** (Assistant messages only)
- Copy to clipboard
- Thumbs up/down rating
- Actions appear on hover

**Source Citations**
- Displays document sources used for responses
- Clickable links to source documents
- Visual indicators for different source types

**Auto-scroll**
- Automatically scrolls to latest message
- Smooth scrolling behavior

**Empty State**
- Shows helpful prompt when no messages
- Icon and description for new conversations

### Message Structure

```typescript
interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  metadata?: {
    sources?: Array<{
      name: string;
      url?: string;
      type: string;
    }>;
  };
}
```

### Code Syntax Highlighting

Supports all major languages:
- JavaScript/TypeScript
- Python
- SQL
- JSON
- Markdown
- And more...

```tsx
// Example code block in message
const code = `
\`\`\`python
def hello_world():
    print("Hello, World!")
\`\`\`
`;
```

### Theme Support

All styles automatically adapt to light/dark theme:
- Syntax highlighting theme (oneDark)
- Code block backgrounds
- Link colors
- Border colors

### Accessibility

**Keyboard Navigation**
- Tab through action buttons
- Space/Enter to activate buttons

**ARIA Labels**
- Proper button labels
- Screen reader friendly
- Semantic HTML structure

**Visual Indicators**
- Icons for user vs assistant messages
- Color coding for ratings
- Clear visual hierarchy

### Notes
- **Performance**: Uses React Markdown with memoization
- **Security**: External links use `noopener noreferrer`
- **Copy Feedback**: Shows checkmark for 2 seconds after copy
- **Rating Persistence**: Ratings stored in Zustand store

---

## MCPServerSelector

Toggle switches for enabling/disabling MCP servers for the current chat session.

### Props

No props required. Fetches server list via React Query.

### Usage Example

```tsx
import { MCPServerSelector } from '@/components/chat/MCPServerSelector';

function ChatSidebar() {
  return (
    <div className="space-y-4">
      <MCPServerSelector />
      {/* Other sidebar content */}
    </div>
  );
}
```

### Features

**Server Management**
- Toggle servers on/off per conversation
- Visual icons for different server types
- Shows only enabled servers
- State persisted in chat store

**Server Icons**

| Server Type | Icon |
|-------------|------|
| MSSQL | Database |
| Microsoft Learn | Globe |
| Power BI Modeling | BarChart |
| Default | Database |

**Interactive Switches**
- Radix UI Switch component
- Accessible keyboard control
- Visual feedback on toggle

### Server Interface

```typescript
interface MCPServerListItem {
  id: string;
  name: string;
  enabled: boolean;
}

interface MCPServersResponse {
  servers: MCPServerListItem[];
  total: number;
}
```

### State Management

Uses `useChatStore()`:

```typescript
const {
  selectedMCPServers,  // string[] of active server IDs
  toggleMCPServer,     // (id: string) => void
} = useChatStore();
```

### API Integration

Fetches server list from `/mcp-servers` endpoint:

```tsx
const { data } = useQuery({
  queryKey: ['mcp-servers'],
  queryFn: () => api.get<MCPServersResponse>('/mcp-servers'),
});
```

### Accessibility
- Proper labels for switches
- Keyboard accessible (Space/Enter to toggle)
- ARIA states for checked/unchecked
- Focus visible indicators

### Notes
- **Filtering**: Only shows servers where `enabled !== false`
- **Persistence**: Selection persisted per conversation
- **Real-time**: Updates reflected immediately in agent context

---

## MessageItem (Internal Component)

Individual message bubble with hover actions.

### Features

**User Messages**
- Right-aligned
- Primary background color
- User icon on right

**Assistant Messages**
- Left-aligned
- Muted background
- Bot icon on left
- Action buttons on hover

**Hover State**
- Shows action buttons
- Smooth opacity transition

### Code Example

```tsx
function MessageItem({ message }: { message: Message }) {
  const [isHovered, setIsHovered] = useState(false);

  return (
    <div
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
    >
      {/* Message content */}
      <MessageActions message={message} isHovered={isHovered} />
    </div>
  );
}
```

---

## MessageActions (Internal Component)

Action buttons for assistant messages.

### Features

**Copy Button**
- Copies message content to clipboard
- Shows checkmark on success
- 2-second timeout before reverting

**Rating Buttons**
- Thumbs up (helpful)
- Thumbs down (not helpful)
- Toggle behavior (click again to remove rating)
- Visual feedback with color change

### State Management

```tsx
const { messageRatings, rateMessage } = useChatStore();

const rating = messageRatings[message.id]; // 'up' | 'down' | null

const handleRate = (newRating: 'up' | 'down') => {
  if (rating === newRating) {
    rateMessage(message.id, null); // Toggle off
  } else {
    rateMessage(message.id, newRating);
  }
};
```

### Accessibility
- Proper ARIA labels
- Keyboard accessible
- Visual focus indicators
- Title attributes for tooltips

---

## SourceCitation (Internal Component)

Displays a clickable source citation badge.

### Props

| Prop | Type | Description |
|------|------|-------------|
| `source` | `{ name: string; url?: string; type: string }` | Source metadata |

### Usage Example

```tsx
function SourceCitation({ source }) {
  return (
    <a
      href={source.url || '#'}
      target="_blank"
      rel="noopener noreferrer"
      className="inline-flex items-center gap-1 rounded border bg-muted/50 px-2 py-0.5 text-xs"
    >
      <FileText className="h-3 w-3" />
      {source.name}
      {source.url && <ExternalLink className="h-3 w-3" />}
    </a>
  );
}
```

### Features
- File icon indicator
- External link icon when URL present
- Hover state
- Opens in new tab

---

## Integration Example

Complete chat interface setup:

```tsx
import { ChatInput } from '@/components/chat/ChatInput';
import { MessageList } from '@/components/chat/MessageList';
import { MCPServerSelector } from '@/components/chat/MCPServerSelector';
import { useChatStore } from '@/stores/chatStore';

function ChatPage() {
  const { sendMessage } = useChatStore();

  return (
    <div className="flex h-screen">
      {/* Sidebar */}
      <aside className="w-64 border-r p-4">
        <MCPServerSelector />
      </aside>

      {/* Main chat area */}
      <main className="flex flex-1 flex-col">
        {/* Message list */}
        <div className="flex-1 overflow-auto">
          <MessageList />
        </div>

        {/* Input */}
        <div className="border-t p-4">
          <ChatInput onSend={sendMessage} />
        </div>
      </main>
    </div>
  );
}
```

---

## WebSocket Integration

The chat system uses WebSocket for real-time streaming:

```typescript
// In useChatStore()
const ws = new WebSocket(`ws://localhost:8000/ws/agent/${conversationId}`);

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);

  if (data.type === 'stream') {
    setStreamingContent(prev => prev + data.content);
  } else if (data.type === 'complete') {
    addMessage({
      id: data.message_id,
      role: 'assistant',
      content: data.content,
      timestamp: new Date(),
    });
    setIsStreaming(false);
  }
};
```

### Message Flow

1. User types message in `ChatInput`
2. `onSend` callback triggered
3. Message sent via WebSocket
4. `MessageList` shows streaming indicator
5. Chunks received and displayed in real-time
6. Final message added to history
7. Auto-scroll to latest message

---

## Store Integration

All chat components use the Zustand `chatStore`:

```typescript
interface ChatStore {
  messages: Message[];
  isStreaming: boolean;
  streamingContent: string;
  messageRatings: Record<string, 'up' | 'down' | null>;
  selectedMCPServers: string[];

  addMessage: (message: Message) => void;
  clearMessages: () => void;
  rateMessage: (id: string, rating: 'up' | 'down' | null) => void;
  toggleMCPServer: (serverId: string) => void;
  setIsStreaming: (streaming: boolean) => void;
  setStreamingContent: (content: string) => void;
}
```

---

## Markdown Rendering

### Supported Syntax

**Headings**
```markdown
# H1
## H2
### H3
```

**Emphasis**
```markdown
**bold**
*italic*
~~strikethrough~~
```

**Lists**
```markdown
- Bullet item
- Another item

1. Numbered item
2. Another item
```

**Code**
```markdown
Inline `code` here

\`\`\`python
# Code block
def hello():
    print("Hello")
\`\`\`
```

**Tables**
```markdown
| Header 1 | Header 2 |
|----------|----------|
| Cell 1   | Cell 2   |
```

**Links**
```markdown
[Link text](https://example.com)
```

**Blockquotes**
```markdown
> Quote text
```

### Custom Styling

Components use custom renderers for enhanced styling:

```tsx
<ReactMarkdown
  remarkPlugins={[remarkGfm]}
  components={{
    code: CustomCodeBlock,
    table: CustomTable,
    th: CustomTableHeader,
    td: CustomTableCell,
    // ... more custom components
  }}
>
  {message.content}
</ReactMarkdown>
```

---

## Styling

### Message Layout

```tsx
// User message (right-aligned)
<div className="flex gap-3 justify-end">
  <div className="max-w-[80%] rounded-lg bg-primary text-primary-foreground px-4 py-2">
    {content}
  </div>
  <UserIcon />
</div>

// Assistant message (left-aligned)
<div className="flex gap-3 justify-start">
  <BotIcon />
  <div className="max-w-[80%] rounded-lg bg-muted px-4 py-2">
    {content}
  </div>
</div>
```

### Responsive Design

- **Desktop**: 80% max-width for messages
- **Mobile**: Adjusts to smaller screens
- **Overflow**: Long code blocks scroll horizontally

---

## Performance Optimization

**Virtualization** (Future Enhancement)
For very long conversations, consider react-virtual:

```tsx
import { useVirtualizer } from '@tanstack/react-virtual';

// Only render visible messages
const virtualizer = useVirtualizer({
  count: messages.length,
  getScrollElement: () => scrollRef.current,
  estimateSize: () => 100,
});
```

**Memoization**
Prevent unnecessary re-renders:

```tsx
const MessageItem = React.memo(({ message }) => {
  // Component logic
});
```

**Debounced Streaming**
For high-frequency updates:

```tsx
const debouncedContent = useDebounce(streamingContent, 50);
```

---

## Accessibility Best Practices

1. **Keyboard Navigation**: All actions accessible via keyboard
2. **ARIA Labels**: Proper labels on all interactive elements
3. **Focus Management**: Focus moved to new messages
4. **Screen Readers**: Content announced as messages arrive
5. **Color Contrast**: WCAG AA compliant colors
6. **Semantic HTML**: Proper heading hierarchy

---

## Error Handling

### WebSocket Errors

```typescript
ws.onerror = (error) => {
  console.error('WebSocket error:', error);
  showToast({
    title: 'Connection Error',
    description: 'Failed to connect to chat server',
    variant: 'destructive',
  });
};

ws.onclose = () => {
  // Attempt reconnection
  setTimeout(connectWebSocket, 5000);
};
```

### Message Send Failures

```typescript
try {
  await sendMessage(content);
} catch (error) {
  showToast({
    title: 'Failed to Send',
    description: error.message,
    variant: 'destructive',
  });
}
```

---

## Testing

### Example Tests

```tsx
import { render, screen, fireEvent } from '@testing-library/react';
import { ChatInput } from '@/components/chat/ChatInput';

describe('ChatInput', () => {
  it('sends message on Enter key', () => {
    const onSend = vi.fn();
    render(<ChatInput onSend={onSend} />);

    const input = screen.getByPlaceholderText(/ask about your data/i);
    fireEvent.change(input, { target: { value: 'Hello' } });
    fireEvent.keyDown(input, { key: 'Enter' });

    expect(onSend).toHaveBeenCalledWith('Hello');
  });

  it('adds new line on Shift+Enter', () => {
    const onSend = vi.fn();
    render(<ChatInput onSend={onSend} />);

    const input = screen.getByRole('textbox');
    fireEvent.keyDown(input, { key: 'Enter', shiftKey: true });

    expect(onSend).not.toHaveBeenCalled();
  });
});
```

---

## Related Documentation

- [Layout Components](./layout.md) - Chat page layout
- [UI Components](./ui.md) - Button and Card primitives
- [Dashboard Components](./dashboard.md) - Pinning query results
