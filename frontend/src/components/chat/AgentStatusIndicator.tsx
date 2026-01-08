/**
 * Agent Status Indicator Component
 *
 * Shows dynamic status while the agent is working:
 * - Animated cycling messages (Thinking..., Analyzing..., Processing...)
 * - Real-time tool status (Calling list_tables tool, Querying database)
 */

import { useEffect, useState, useMemo } from 'react';
import { Loader2, Database, Search, FileText, Wrench, type LucideIcon } from 'lucide-react';
import { useChatStore } from '@/stores/chatStore';

// Animated messages that cycle while thinking
const THINKING_MESSAGES = [
  'Thinking...',
  'Analyzing...',
  'Processing...',
  'Pondering...',
  'Reasoning...',
  'Considering...',
  'Evaluating...',
];

// Messages for different tool types
const TOOL_MESSAGES: Record<string, string> = {
  list_tables: 'Discovering database tables...',
  describe_table: 'Analyzing table schema...',
  read_data: 'Querying data...',
  insert_data: 'Inserting records...',
  update_data: 'Updating records...',
  create_table: 'Creating table...',
  drop_table: 'Dropping table...',
  create_index: 'Creating index...',
  microsoft_docs_search: 'Searching Microsoft docs...',
  microsoft_code_sample_search: 'Finding code samples...',
  microsoft_docs_fetch: 'Fetching documentation...',
};

// Get icon for tool type
function getToolIcon(toolName: string | null): LucideIcon {
  if (!toolName) return Wrench;

  if (toolName.includes('table') || toolName.includes('data') || toolName.includes('index')) {
    return Database;
  }
  if (toolName.includes('search') || toolName.includes('find')) {
    return Search;
  }
  if (toolName.includes('doc') || toolName.includes('fetch')) {
    return FileText;
  }

  return Wrench;
}

// Tool status display component (extracted to avoid creating during render)
function ToolStatusDisplay({
  toolName,
  toolMessage,
  toolArgsDisplay,
}: {
  toolName: string | null;
  toolMessage: string | null;
  toolArgsDisplay: string | null;
}) {
  // Memoize Icon to avoid recreation on every render
  const Icon = useMemo(() => getToolIcon(toolName), [toolName]);
  
  return (
    <div className="flex items-center gap-1.5 text-xs animate-in slide-in-from-left duration-200">
      <Icon className="h-3 w-3" />
      <span>{toolMessage}</span>
      {toolArgsDisplay && (
        <span className="text-muted-foreground/60 truncate max-w-[200px]">
          ({toolArgsDisplay})
        </span>
      )}
    </div>
  );
}

export function AgentStatusIndicator() {
  const { agentStatus, isStreaming } = useChatStore();
  const [messageIndex, setMessageIndex] = useState(0);

  // Safety check for agentStatus (may be undefined from old localStorage)
  const safeAgentStatus = agentStatus ?? {
    isActive: false,
    currentPhase: 'idle' as const,
    toolName: null,
    toolArgs: null,
    animatedMessage: '',
  };

  const isToolCalling = safeAgentStatus.currentPhase === 'tool_calling' && safeAgentStatus.toolName;

  // Cycle through thinking messages
  useEffect(() => {
    if (!safeAgentStatus.isActive) {
      return;
    }

    const interval = setInterval(() => {
      setMessageIndex((prev) => (prev + 1) % THINKING_MESSAGES.length);
    }, 2000);

    return () => {
      clearInterval(interval);
      // Reset index when effect cleans up (agent becomes inactive)
      setMessageIndex(0);
    };
  }, [safeAgentStatus.isActive]);

  // Don't show anything if agent is idle
  if (!safeAgentStatus.isActive && !isStreaming) {
    return null;
  }

  // Get tool-specific message
  const toolMessage = safeAgentStatus.toolName
    ? TOOL_MESSAGES[safeAgentStatus.toolName] || `Calling ${safeAgentStatus.toolName}...`
    : null;

  // Get tool args summary
  const getToolArgsDisplay = () => {
    if (!safeAgentStatus.toolArgs || Object.keys(safeAgentStatus.toolArgs).length === 0) {
      return null;
    }

    const args = safeAgentStatus.toolArgs;
    const entries = Object.entries(args).slice(0, 2); // Show max 2 args

    return entries.map(([key, value]) => {
      const displayValue = typeof value === 'string'
        ? value.length > 30 ? value.slice(0, 30) + '...' : value
        : JSON.stringify(value).slice(0, 30);
      return `${key}: ${displayValue}`;
    }).join(', ');
  };

  return (
    <div className="flex items-center gap-3 py-2 px-3 text-sm text-muted-foreground animate-in fade-in duration-300">
      {/* Animated spinner */}
      <Loader2 className="h-4 w-4 animate-spin text-primary" />

      {/* Main status area */}
      <div className="flex flex-col gap-0.5">
        {/* Animated thinking message */}
        <div className="flex items-center gap-2">
          <span className="font-medium text-foreground/80 transition-opacity duration-300">
            {THINKING_MESSAGES[messageIndex]}
          </span>

          {/* Animated dots */}
          <span className="inline-flex">
            <span className="animate-bounce" style={{ animationDelay: '0ms' }}>.</span>
            <span className="animate-bounce" style={{ animationDelay: '150ms' }}>.</span>
            <span className="animate-bounce" style={{ animationDelay: '300ms' }}>.</span>
          </span>
        </div>

        {/* Tool status (when calling a tool) */}
        {isToolCalling && (
          <ToolStatusDisplay 
            toolName={safeAgentStatus.toolName}
            toolMessage={toolMessage}
            toolArgsDisplay={getToolArgsDisplay()}
          />
        )}

        {/* Generating phase */}
        {safeAgentStatus.currentPhase === 'generating' && (
          <div className="flex items-center gap-1.5 text-xs animate-in slide-in-from-left duration-200">
            <FileText className="h-3 w-3" />
            <span>Generating response...</span>
          </div>
        )}
      </div>
    </div>
  );
}
