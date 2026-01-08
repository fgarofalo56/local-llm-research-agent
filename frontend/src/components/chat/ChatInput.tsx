import { useState, type KeyboardEvent } from 'react';
import { Send, Loader2 } from 'lucide-react';
import { Button } from '@/components/ui/Button';
import { useChatStore } from '@/stores/chatStore';
import { cn } from '@/lib/utils';

interface ChatInputProps {
  onSend: (content: string) => void;
}

export function ChatInput({ onSend }: ChatInputProps) {
  const [input, setInput] = useState('');
  const { isStreaming } = useChatStore();

  const handleSubmit = () => {
    if (!input.trim() || isStreaming) return;
    onSend(input.trim());
    setInput('');
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  return (
    <div className="flex gap-2">
      <div className="relative flex-1">
        <textarea
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Ask about your data... (Enter to send, Shift+Enter for new line)"
          className={cn(
            'w-full resize-none rounded-lg border bg-background px-4 py-3 text-sm transition-all duration-200',
            'focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2',
            'placeholder:text-muted-foreground',
            isStreaming && 'opacity-60 cursor-not-allowed'
          )}
          rows={3}
          disabled={isStreaming}
          aria-label="Chat message input"
        />
        {isStreaming && (
          <div className="absolute bottom-3 right-3 flex items-center gap-2 text-xs text-muted-foreground animate-pulse">
            <Loader2 className="h-3 w-3 animate-spin" />
            <span>Generating response...</span>
          </div>
        )}
      </div>
      <Button
        onClick={handleSubmit}
        disabled={!input.trim() || isStreaming}
        size="icon"
        className="h-auto min-w-[44px] transition-all duration-200"
        aria-label={isStreaming ? 'Generating response' : 'Send message'}
      >
        {isStreaming ? (
          <Loader2 className="h-4 w-4 animate-spin" />
        ) : (
          <Send className="h-4 w-4" />
        )}
      </Button>
    </div>
  );
}
