import { useRef, useEffect, useState } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { oneDark } from 'react-syntax-highlighter/dist/esm/styles/prism';
import { User, Bot, ThumbsUp, ThumbsDown, Copy, Check, FileText, ExternalLink } from 'lucide-react';
import { useChatStore } from '@/stores/chatStore';
import { cn } from '@/lib/utils';
import type { Message } from '@/types';

// Source citation component
function SourceCitation({ source }: { source: { name: string; url?: string; type: string } }) {
  return (
    <a
      href={source.url || '#'}
      target="_blank"
      rel="noopener noreferrer"
      className="inline-flex items-center gap-1 rounded border bg-muted/50 px-2 py-0.5 text-xs hover:bg-muted"
    >
      <FileText className="h-3 w-3" />
      {source.name}
      {source.url && <ExternalLink className="h-3 w-3" />}
    </a>
  );
}

// Message actions component
function MessageActions({
  message,
  isHovered,
}: {
  message: Message;
  isHovered: boolean;
}) {
  const { messageRatings, rateMessage } = useChatStore();
  const [copied, setCopied] = useState(false);

  const rating = messageRatings[message.id];

  const handleCopy = async () => {
    await navigator.clipboard.writeText(message.content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleRate = (newRating: 'up' | 'down') => {
    // Toggle off if same rating clicked
    if (rating === newRating) {
      rateMessage(message.id, null);
    } else {
      rateMessage(message.id, newRating);
    }
  };

  if (message.role === 'user') return null;

  return (
    <div
      className={cn(
        'mt-2 flex items-center gap-2 transition-opacity',
        isHovered ? 'opacity-100' : 'opacity-0'
      )}
    >
      {/* Copy button */}
      <button
        onClick={handleCopy}
        className="rounded p-1 text-muted-foreground hover:bg-muted hover:text-foreground"
        title="Copy to clipboard"
      >
        {copied ? <Check className="h-4 w-4 text-green-500" /> : <Copy className="h-4 w-4" />}
      </button>

      {/* Rate up */}
      <button
        onClick={() => handleRate('up')}
        className={cn(
          'rounded p-1 hover:bg-muted',
          rating === 'up' ? 'text-green-500' : 'text-muted-foreground hover:text-foreground'
        )}
        title="Helpful"
      >
        <ThumbsUp className="h-4 w-4" />
      </button>

      {/* Rate down */}
      <button
        onClick={() => handleRate('down')}
        className={cn(
          'rounded p-1 hover:bg-muted',
          rating === 'down' ? 'text-red-500' : 'text-muted-foreground hover:text-foreground'
        )}
        title="Not helpful"
      >
        <ThumbsDown className="h-4 w-4" />
      </button>
    </div>
  );
}

// Single message component with hover state
function MessageItem({ message }: { message: Message }) {
  const [isHovered, setIsHovered] = useState(false);

  // Extract sources from message metadata if available
  const sources = message.metadata?.sources as Array<{ name: string; url?: string; type: string }> | undefined;

  return (
    <div
      className={cn(
        'flex gap-3',
        message.role === 'user' ? 'justify-end' : 'justify-start'
      )}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
    >
      {message.role === 'assistant' && (
        <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-primary">
          <Bot className="h-4 w-4 text-primary-foreground" />
        </div>
      )}

      <div
        className={cn(
          'max-w-[80%] rounded-lg px-4 py-2',
          message.role === 'user'
            ? 'bg-primary text-primary-foreground'
            : 'bg-muted'
        )}
      >
        {/* Message content with rich markdown */}
        <div className="prose prose-sm dark:prose-invert max-w-none">
          <ReactMarkdown
            remarkPlugins={[remarkGfm]}
            components={{
              code(props) {
                const { children, className, ...rest } = props;
                const match = /language-(\w+)/.exec(className || '');
                const isInline = !match;
                return !isInline && match ? (
                  <SyntaxHighlighter
                    style={oneDark}
                    language={match[1]}
                    PreTag="div"
                    customStyle={{
                      margin: '0.5rem 0',
                      borderRadius: '0.5rem',
                      fontSize: '0.875rem',
                    }}
                  >
                    {String(children).replace(/\n$/, '')}
                  </SyntaxHighlighter>
                ) : (
                  <code
                    className={cn(
                      'rounded bg-black/10 dark:bg-white/10 px-1 py-0.5 text-sm',
                      className
                    )}
                    {...rest}
                  >
                    {children}
                  </code>
                );
              },
              // Enhanced table styling
              table({ children }) {
                return (
                  <div className="my-2 overflow-x-auto">
                    <table className="min-w-full border-collapse rounded border">
                      {children}
                    </table>
                  </div>
                );
              },
              th({ children }) {
                return (
                  <th className="border bg-muted/50 px-3 py-1 text-left font-medium">
                    {children}
                  </th>
                );
              },
              td({ children }) {
                return <td className="border px-3 py-1">{children}</td>;
              },
              // Enhanced list styling
              ul({ children }) {
                return <ul className="my-1 ml-4 list-disc">{children}</ul>;
              },
              ol({ children }) {
                return <ol className="my-1 ml-4 list-decimal">{children}</ol>;
              },
              // Enhanced blockquote
              blockquote({ children }) {
                return (
                  <blockquote className="my-2 border-l-4 border-primary/50 pl-4 italic text-muted-foreground">
                    {children}
                  </blockquote>
                );
              },
              // Headings
              h1({ children }) {
                return <h1 className="mb-2 mt-4 text-xl font-bold">{children}</h1>;
              },
              h2({ children }) {
                return <h2 className="mb-2 mt-3 text-lg font-bold">{children}</h2>;
              },
              h3({ children }) {
                return <h3 className="mb-1 mt-2 text-base font-semibold">{children}</h3>;
              },
              // Links
              a({ children, href }) {
                return (
                  <a
                    href={href}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-primary hover:underline"
                  >
                    {children}
                  </a>
                );
              },
            }}
          >
            {message.content}
          </ReactMarkdown>
        </div>

        {/* Source citations */}
        {sources && sources.length > 0 && (
          <div className="mt-3 flex flex-wrap gap-2 border-t pt-2">
            <span className="text-xs text-muted-foreground">Sources:</span>
            {sources.map((source, idx) => (
              <SourceCitation key={idx} source={source} />
            ))}
          </div>
        )}

        {/* Message actions (copy, rate) */}
        <MessageActions message={message} isHovered={isHovered} />
      </div>

      {message.role === 'user' && (
        <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-secondary">
          <User className="h-4 w-4 text-secondary-foreground" />
        </div>
      )}
    </div>
  );
}

export function MessageList() {
  const { messages, isStreaming, streamingContent } = useChatStore();
  const bottomRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, streamingContent]);

  return (
    <div className="space-y-4 p-4">
      {/* Empty state for new conversations */}
      {messages.length === 0 && !isStreaming && (
        <div className="flex h-[50vh] flex-col items-center justify-center text-center">
          <Bot className="mb-4 h-12 w-12 text-muted-foreground" />
          <h3 className="mb-2 text-lg font-semibold">Start a Conversation</h3>
          <p className="max-w-md text-sm text-muted-foreground">
            Ask a question about your SQL Server data, upload documents for RAG context,
            or explore your database schema using the research agent.
          </p>
        </div>
      )}

      {messages.map((message) => (
        <MessageItem key={message.id} message={message} />
      ))}

      {/* Streaming response */}
      {isStreaming && (
        <div className="flex gap-3">
          <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-primary">
            <Bot className="h-4 w-4 text-primary-foreground" />
          </div>
          <div className="max-w-[80%] rounded-lg bg-muted px-4 py-2">
            <div className="prose prose-sm dark:prose-invert max-w-none">
              <ReactMarkdown remarkPlugins={[remarkGfm]}>
                {streamingContent || '...'}
              </ReactMarkdown>
            </div>
          </div>
        </div>
      )}

      <div ref={bottomRef} />
    </div>
  );
}
