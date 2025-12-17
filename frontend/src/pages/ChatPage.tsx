import { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import {
  FileText,
  Download,
  Settings,
  ChevronDown,
  ChevronUp,
  Sliders,
  BookOpen,
  Database,
  Bot,
  Hash,
  Wifi,
  WifiOff,
} from 'lucide-react';
import { MessageList } from '@/components/chat/MessageList';
import { ChatInput } from '@/components/chat/ChatInput';
import { MCPServerSelector } from '@/components/chat/MCPServerSelector';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Card, CardContent } from '@/components/ui/Card';
import { useMessages, useCreateConversation, useConversation } from '@/hooks/useConversations';
import { useAgentWebSocket } from '@/hooks/useWebSocket';
import { useChatStore } from '@/stores/chatStore';
import { api } from '@/api/client';
import { exportChatToMarkdown, exportChatToPdf } from '@/lib/exports/chatExport';
import * as Switch from '@radix-ui/react-switch';
import * as Slider from '@radix-ui/react-slider';

interface ModelInfo {
  name: string;
  size: string | null;
  family: string | null;
  parameter_size: string | null;
}

interface ProviderModelsResponse {
  provider: string;
  models: ModelInfo[];
  error: string | null;
}

// Token counter component
function TokenCounter() {
  const { tokenCount } = useChatStore();

  const remaining = tokenCount.contextWindowSize - tokenCount.total;
  const usagePercent = (tokenCount.total / tokenCount.contextWindowSize) * 100;

  return (
    <div className="flex items-center gap-3 rounded-lg border bg-card px-3 py-2 text-xs">
      <Hash className="h-4 w-4 text-muted-foreground" />
      <div className="flex gap-4">
        <div>
          <span className="text-muted-foreground">Prompt:</span>
          <span className="ml-1 font-mono">{tokenCount.prompt.toLocaleString()}</span>
        </div>
        <div>
          <span className="text-muted-foreground">Completion:</span>
          <span className="ml-1 font-mono">{tokenCount.completion.toLocaleString()}</span>
        </div>
        <div>
          <span className="text-muted-foreground">Total:</span>
          <span className="ml-1 font-mono font-medium">{tokenCount.total.toLocaleString()}</span>
        </div>
        <div className="border-l pl-4">
          <span className="text-muted-foreground">Remaining:</span>
          <span
            className={`ml-1 font-mono ${remaining < 1000 ? 'text-red-500' : 'text-green-500'}`}
          >
            {remaining.toLocaleString()}
          </span>
          <span className="ml-1 text-muted-foreground">({usagePercent.toFixed(1)}%)</span>
        </div>
      </div>
    </div>
  );
}

// Model selector in chat header
function ChatModelSelector() {
  const { selectedProvider, selectedModel, setSelectedModel } = useChatStore();
  const [isOpen, setIsOpen] = useState(false);

  const { data: modelsData } = useQuery({
    queryKey: ['models', selectedProvider],
    queryFn: () => api.get<ProviderModelsResponse>(`/settings/providers/${selectedProvider}/models`),
    enabled: !!selectedProvider,
  });

  const models = modelsData?.models || [];

  return (
    <div className="relative">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center gap-2 rounded-lg border bg-card px-3 py-2 text-sm hover:bg-muted"
      >
        <Bot className="h-4 w-4" />
        <span className="max-w-[150px] truncate">{selectedModel || 'Select model'}</span>
        <ChevronDown className={`h-4 w-4 transition-transform ${isOpen ? 'rotate-180' : ''}`} />
      </button>

      {isOpen && models.length > 0 && (
        <div className="absolute right-0 z-50 mt-1 max-h-60 w-64 overflow-auto rounded-lg border bg-popover shadow-lg">
          {models.map((model) => (
            <button
              key={model.name}
              onClick={() => {
                setSelectedModel(model.name);
                setIsOpen(false);
              }}
              className={`flex w-full flex-col px-3 py-2 text-left text-sm hover:bg-muted ${
                model.name === selectedModel ? 'bg-muted' : ''
              }`}
            >
              <span className="font-medium">{model.name}</span>
              {model.size && (
                <span className="text-xs text-muted-foreground">{model.size}</span>
              )}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}

// Model parameters panel
function ModelParametersPanel() {
  const { modelParameters, setModelParameters } = useChatStore();

  return (
    <div className="space-y-4">
      <h4 className="flex items-center gap-2 text-sm font-medium">
        <Sliders className="h-4 w-4" />
        Model Parameters
      </h4>

      {/* Temperature */}
      <div className="space-y-2">
        <div className="flex items-center justify-between">
          <label className="text-sm text-muted-foreground">Temperature</label>
          <span className="font-mono text-sm">{modelParameters.temperature.toFixed(1)}</span>
        </div>
        <Slider.Root
          className="relative flex h-5 w-full touch-none items-center"
          value={[modelParameters.temperature]}
          onValueChange={([value]) => setModelParameters({ temperature: value })}
          min={0}
          max={2}
          step={0.1}
        >
          <Slider.Track className="relative h-1 w-full grow rounded-full bg-muted">
            <Slider.Range className="absolute h-full rounded-full bg-primary" />
          </Slider.Track>
          <Slider.Thumb className="block h-4 w-4 rounded-full bg-primary shadow" />
        </Slider.Root>
        <p className="text-xs text-muted-foreground">
          Higher = more creative, Lower = more focused
        </p>
      </div>

      {/* Top P */}
      <div className="space-y-2">
        <div className="flex items-center justify-between">
          <label className="text-sm text-muted-foreground">Top P</label>
          <span className="font-mono text-sm">{modelParameters.topP.toFixed(2)}</span>
        </div>
        <Slider.Root
          className="relative flex h-5 w-full touch-none items-center"
          value={[modelParameters.topP]}
          onValueChange={([value]) => setModelParameters({ topP: value })}
          min={0}
          max={1}
          step={0.05}
        >
          <Slider.Track className="relative h-1 w-full grow rounded-full bg-muted">
            <Slider.Range className="absolute h-full rounded-full bg-primary" />
          </Slider.Track>
          <Slider.Thumb className="block h-4 w-4 rounded-full bg-primary shadow" />
        </Slider.Root>
        <p className="text-xs text-muted-foreground">Nucleus sampling threshold</p>
      </div>

      {/* Max Tokens */}
      <div className="space-y-2">
        <div className="flex items-center justify-between">
          <label className="text-sm text-muted-foreground">Max Tokens</label>
          <span className="font-mono text-sm">{modelParameters.maxTokens}</span>
        </div>
        <Input
          type="number"
          value={modelParameters.maxTokens}
          onChange={(e) => setModelParameters({ maxTokens: parseInt(e.target.value) || 2048 })}
          min={1}
          max={32768}
          className="h-8"
        />
        <p className="text-xs text-muted-foreground">Maximum response length</p>
      </div>
    </div>
  );
}

// System prompt configuration
function SystemPromptConfig() {
  const { systemPrompt, setSystemPrompt } = useChatStore();

  return (
    <div className="space-y-2">
      <h4 className="flex items-center gap-2 text-sm font-medium">
        <BookOpen className="h-4 w-4" />
        System Prompt
      </h4>
      <textarea
        value={systemPrompt}
        onChange={(e) => setSystemPrompt(e.target.value)}
        className="h-24 w-full rounded-lg border bg-background p-2 text-sm"
        placeholder="Enter custom system prompt..."
      />
      <p className="text-xs text-muted-foreground">
        Customize the agent's behavior and personality
      </p>
    </div>
  );
}

// RAG settings component
function RAGSettings() {
  const { ragSettings, setRAGSettings, toggleRAG, toggleHybridSearch } = useChatStore();

  return (
    <div className="space-y-3">
      <h4 className="flex items-center gap-2 text-sm font-medium">
        <Database className="h-4 w-4" />
        RAG Settings
      </h4>

      {/* Enable RAG */}
      <div className="flex items-center justify-between">
        <div>
          <label className="text-sm">Enable RAG</label>
          <p className="text-xs text-muted-foreground">Use knowledge base for context</p>
        </div>
        <Switch.Root
          checked={ragSettings.enabled}
          onCheckedChange={toggleRAG}
          className="relative h-5 w-9 rounded-full bg-muted data-[state=checked]:bg-primary"
        >
          <Switch.Thumb className="block h-4 w-4 translate-x-0.5 rounded-full bg-white transition-transform data-[state=checked]:translate-x-4" />
        </Switch.Root>
      </div>

      {/* Hybrid Search */}
      {ragSettings.enabled && (
        <>
          <div className="flex items-center justify-between">
            <div>
              <label className="text-sm">Hybrid Search</label>
              <p className="text-xs text-muted-foreground">Combine semantic + keyword search</p>
            </div>
            <Switch.Root
              checked={ragSettings.hybridSearch}
              onCheckedChange={toggleHybridSearch}
              className="relative h-5 w-9 rounded-full bg-muted data-[state=checked]:bg-primary"
            >
              <Switch.Thumb className="block h-4 w-4 translate-x-0.5 rounded-full bg-white transition-transform data-[state=checked]:translate-x-4" />
            </Switch.Root>
          </div>

          {/* Top K */}
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <label className="text-sm text-muted-foreground">Top K Results</label>
              <span className="font-mono text-sm">{ragSettings.topK}</span>
            </div>
            <Slider.Root
              className="relative flex h-5 w-full touch-none items-center"
              value={[ragSettings.topK]}
              onValueChange={([value]) => setRAGSettings({ topK: value })}
              min={1}
              max={20}
              step={1}
            >
              <Slider.Track className="relative h-1 w-full grow rounded-full bg-muted">
                <Slider.Range className="absolute h-full rounded-full bg-primary" />
              </Slider.Track>
              <Slider.Thumb className="block h-4 w-4 rounded-full bg-primary shadow" />
            </Slider.Root>
          </div>
        </>
      )}
    </div>
  );
}

export function ChatPage() {
  const { conversationId } = useParams<{ conversationId: string }>();
  const { currentConversationId, setCurrentConversation, setMessages, addMessage, loadSavedSettings } = useChatStore();
  const createConversation = useCreateConversation();
  const [showSettings, setShowSettings] = useState(false);

  // Parse conversation ID
  const parsedId = conversationId ? parseInt(conversationId, 10) : null;

  // Load saved settings on mount
  useEffect(() => {
    loadSavedSettings();
  }, [loadSavedSettings]);

  // Set current conversation
  useEffect(() => {
    if (parsedId) {
      setCurrentConversation(parsedId);
    }
  }, [parsedId, setCurrentConversation]);

  // Fetch conversation details
  const { data: conversation } = useConversation(currentConversationId);

  // Fetch messages
  const { data: messagesData } = useMessages(currentConversationId);

  // Update messages in store
  useEffect(() => {
    if (messagesData?.messages) {
      setMessages(messagesData.messages);
    }
  }, [messagesData, setMessages]);

  // WebSocket connection
  const { sendMessage, isConnected, reconnect } = useAgentWebSocket(currentConversationId);

  const handleSendMessage = async (content: string) => {
    try {
      // Add user message to UI immediately for instant feedback
      const userMessage = {
        id: Date.now(), // Temporary ID until server assigns real one
        conversation_id: currentConversationId || 0,
        role: 'user' as const,
        content,
        created_at: new Date().toISOString(),
      };
      addMessage(userMessage);

      // Create conversation if needed
      if (!currentConversationId) {
        const conversation = await createConversation.mutateAsync(content.slice(0, 50));
        setCurrentConversation(conversation.id);
        // Queue the message - it will be sent when WebSocket connects
        // The hook will automatically connect when conversationId changes
        // Give it a moment to trigger the useEffect, then queue the message
        await new Promise(resolve => setTimeout(resolve, 50));
        await sendMessage(content);
      } else {
        await sendMessage(content);
      }
    } catch (error) {
      console.error('Failed to send message:', error);
      // Could show an error toast here
    }
  };

  const handleExportMarkdown = () => {
    if (conversation && messagesData?.messages) {
      exportChatToMarkdown(conversation, messagesData.messages);
    }
  };

  const handleExportPdf = () => {
    if (conversation && messagesData?.messages) {
      exportChatToPdf(conversation, messagesData.messages);
    }
  };

  return (
    <div className="flex h-full flex-col">
      {/* Header with controls */}
      <div className="border-b p-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <MCPServerSelector />
            <ChatModelSelector />
            {/* Connection status indicator */}
            <div
              className={`flex items-center gap-1.5 rounded-lg border px-2 py-1.5 text-xs ${
                isConnected
                  ? 'border-green-500/30 bg-green-500/10 text-green-600 dark:text-green-400'
                  : 'border-yellow-500/30 bg-yellow-500/10 text-yellow-600 dark:text-yellow-400'
              }`}
              title={isConnected ? 'WebSocket connected' : 'WebSocket connecting...'}
            >
              {isConnected ? (
                <Wifi className="h-3.5 w-3.5" />
              ) : (
                <WifiOff className="h-3.5 w-3.5" />
              )}
              <span>{isConnected ? 'Connected' : 'Connecting'}</span>
            </div>
          </div>

          <div className="flex items-center gap-2">
            {/* Token counter */}
            <TokenCounter />

            {/* Settings toggle */}
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setShowSettings(!showSettings)}
            >
              <Settings className="mr-2 h-4 w-4" />
              {showSettings ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
            </Button>

            {/* Export buttons */}
            {currentConversationId && messagesData?.messages && messagesData.messages.length > 0 && (
              <>
                <Button variant="ghost" size="sm" onClick={handleExportMarkdown}>
                  <FileText className="mr-2 h-4 w-4" />
                  MD
                </Button>
                <Button variant="ghost" size="sm" onClick={handleExportPdf}>
                  <Download className="mr-2 h-4 w-4" />
                  PDF
                </Button>
              </>
            )}
          </div>
        </div>

        {/* Expandable settings panel */}
        {showSettings && (
          <Card className="mt-4">
            <CardContent className="grid gap-6 p-4 md:grid-cols-3">
              <ModelParametersPanel />
              <SystemPromptConfig />
              <RAGSettings />
            </CardContent>
          </Card>
        )}
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-auto">
        <MessageList />
      </div>

      {/* Input */}
      <div className="border-t p-4">
        <ChatInput onSend={handleSendMessage} />
      </div>
    </div>
  );
}
