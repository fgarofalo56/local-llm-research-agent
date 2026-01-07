/**
 * Chat Toolbar Component
 *
 * Provides quick access to chat options above the input area:
 * - Thinking mode toggle
 * - Attach Files
 * - View Active MCP Servers
 * - Search Web toggle
 * - Provider/Model selector
 */

import { useState } from 'react';
import {
  Brain,
  Paperclip,
  Server,
  Globe,
  ChevronDown,
  X,
  Check,
} from 'lucide-react';
import { Button } from '@/components/ui/Button';
import { useChatStore } from '@/stores/chatStore';
import { useQuery } from '@tanstack/react-query';
import { api } from '@/api/client';

interface MCPServer {
  id: string;
  name: string;
  description: string;
  enabled: boolean;
  type: string;
}

interface ProviderInfo {
  id: string;
  name: string;
  display_name: string;
  icon: string;
  available: boolean;
  error: string | null;
  version: string | null;
}

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

export function ChatToolbar() {
  const {
    toolbarSettings,
    toggleThinking,
    toggleWebSearch,
    toggleMCPPanel,
    selectedMCPServers,
    toggleMCPServer,
    selectedProvider,
    selectedModel,
    setSelectedProvider,
    setSelectedModel,
    setMessages,
    setCurrentConversation,
  } = useChatStore();

  // Safety check for toolbarSettings (may be undefined from old localStorage)
  const safeToolbarSettings = toolbarSettings ?? {
    thinkingEnabled: false,
    webSearchEnabled: false,
    showMCPPanel: false,
  };

  const [showProviderDropdown, setShowProviderDropdown] = useState(false);
  const [showModelDropdown, setShowModelDropdown] = useState(false);

  // Fetch MCP servers - with defensive error handling
  const { data: mcpServers = [] } = useQuery<MCPServer[]>({
    queryKey: ['mcp-servers'],
    queryFn: async () => {
      try {
        const response = await api.get<{ servers: MCPServer[]; total: number }>('/mcp');
        return Array.isArray(response?.servers) ? response.servers : [];
      } catch (error) {
        console.error('Failed to fetch MCP servers:', error);
        return [];
      }
    },
    staleTime: 30000,
  });

  // Fetch providers list - with defensive error handling
  const { data: providersList = [] } = useQuery<ProviderInfo[]>({
    queryKey: ['providers'],
    queryFn: async () => {
      try {
        const response = await api.get<ProviderInfo[]>('/settings/providers');
        return Array.isArray(response) ? response : [];
      } catch (error) {
        console.error('Failed to fetch providers:', error);
        return [];
      }
    },
    staleTime: 30000,
  });

  // Fetch models for selected provider - with defensive error handling
  const { data: modelsData } = useQuery<ProviderModelsResponse>({
    queryKey: ['provider-models', selectedProvider],
    queryFn: async () => {
      try {
        const response = await api.get<ProviderModelsResponse>(`/settings/providers/${selectedProvider}/models`);
        return response ?? { provider: selectedProvider, models: [], error: null };
      } catch (error) {
        console.error('Failed to fetch models:', error);
        return { provider: selectedProvider, models: [], error: 'Failed to fetch' };
      }
    },
    staleTime: 30000,
    enabled: !!selectedProvider,
  });

  // Get provider availability
  const getProviderAvailable = (providerId: string): boolean => {
    if (!providersList || !Array.isArray(providersList)) return false;
    const provider = providersList.find(p => p.id === providerId);
    return provider?.available ?? false;
  };

  // Filter models that support tool calling
  const getAvailableModels = (): string[] => {
    if (!modelsData?.models || !Array.isArray(modelsData.models)) return [];

    // Filter for models that typically support tool calling
    // Common patterns: qwen, llama3, mistral, phi
    return modelsData.models
      .map(m => m.name)
      .filter(model => {
        const lowerModel = model.toLowerCase();
        return (
          lowerModel.includes('qwen') ||
          lowerModel.includes('llama3') ||
          lowerModel.includes('mistral') ||
          lowerModel.includes('phi') ||
          lowerModel.includes('deepseek') ||
          lowerModel.includes('command') ||
          lowerModel.includes('granite')
        );
      });
  };

  const handleProviderChange = (newProvider: string) => {
    if (newProvider !== selectedProvider) {
      // Switching providers restarts conversation
      setSelectedProvider(newProvider);
      // Model will be updated when modelsData query completes
      // Clear conversation
      setMessages([]);
      setCurrentConversation(null);
    }
    setShowProviderDropdown(false);
  };

  const handleModelChange = (newModel: string) => {
    if (newModel !== selectedModel) {
      setSelectedModel(newModel);
      // Clear conversation when changing models
      setMessages([]);
      setCurrentConversation(null);
    }
    setShowModelDropdown(false);
  };

  const enabledMCPCount = Array.isArray(mcpServers)
    ? mcpServers.filter(s => selectedMCPServers.includes(s.id)).length
    : 0;

  return (
    <div className="flex flex-col gap-2 pb-2">
      {/* Main toolbar */}
      <div className="flex items-center gap-1 flex-wrap">
        {/* Thinking Toggle */}
        <Button
          variant={safeToolbarSettings.thinkingEnabled ? 'default' : 'ghost'}
          size="sm"
          onClick={toggleThinking}
          className="gap-1.5 text-xs"
          title="Show thinking process"
        >
          <Brain className="h-3.5 w-3.5" />
          <span className="hidden sm:inline">Thinking</span>
          {safeToolbarSettings.thinkingEnabled && <Check className="h-3 w-3" />}
        </Button>

        {/* Attach Files */}
        <Button
          variant="ghost"
          size="sm"
          className="gap-1.5 text-xs"
          title="Attach files (coming soon)"
          disabled
        >
          <Paperclip className="h-3.5 w-3.5" />
          <span className="hidden sm:inline">Attach</span>
        </Button>

        {/* MCP Servers Toggle */}
        <Button
          variant={safeToolbarSettings.showMCPPanel ? 'default' : 'ghost'}
          size="sm"
          onClick={toggleMCPPanel}
          className="gap-1.5 text-xs"
          title="View active MCP servers"
        >
          <Server className="h-3.5 w-3.5" />
          <span className="hidden sm:inline">MCP</span>
          {enabledMCPCount > 0 && (
            <span className="rounded-full bg-primary/20 px-1.5 text-[10px] font-medium">
              {enabledMCPCount}
            </span>
          )}
        </Button>

        {/* Web Search Toggle */}
        <Button
          variant={safeToolbarSettings.webSearchEnabled ? 'default' : 'ghost'}
          size="sm"
          onClick={toggleWebSearch}
          className="gap-1.5 text-xs"
          title="Enable web search"
        >
          <Globe className="h-3.5 w-3.5" />
          <span className="hidden sm:inline">Web</span>
          {safeToolbarSettings.webSearchEnabled && <Check className="h-3 w-3" />}
        </Button>

        {/* Separator */}
        <div className="mx-1 h-4 w-px bg-border" />

        {/* Provider Selector */}
        <div className="relative">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setShowProviderDropdown(!showProviderDropdown)}
            className="gap-1 text-xs"
          >
            <span className="font-medium capitalize">{selectedProvider}</span>
            <ChevronDown className="h-3 w-3" />
          </Button>

          {showProviderDropdown && (
            <div className="absolute top-full left-0 z-50 mt-1 min-w-[120px] rounded-md border bg-popover p-1 shadow-md">
              {getProviderAvailable('ollama') && (
                <button
                  className={`w-full rounded px-2 py-1.5 text-left text-xs hover:bg-accent ${
                    selectedProvider === 'ollama' ? 'bg-accent' : ''
                  }`}
                  onClick={() => handleProviderChange('ollama')}
                >
                  Ollama
                </button>
              )}
              {getProviderAvailable('foundry_local') && (
                <button
                  className={`w-full rounded px-2 py-1.5 text-left text-xs hover:bg-accent ${
                    selectedProvider === 'foundry_local' ? 'bg-accent' : ''
                  }`}
                  onClick={() => handleProviderChange('foundry_local')}
                >
                  Foundry Local
                </button>
              )}
              {!getProviderAvailable('ollama') && !getProviderAvailable('foundry_local') && (
                <div className="px-2 py-1.5 text-xs text-muted-foreground">
                  No providers available
                </div>
              )}
            </div>
          )}
        </div>

        {/* Model Selector */}
        <div className="relative">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setShowModelDropdown(!showModelDropdown)}
            className="gap-1 text-xs max-w-[150px]"
          >
            <span className="truncate font-medium">{selectedModel}</span>
            <ChevronDown className="h-3 w-3 flex-shrink-0" />
          </Button>

          {showModelDropdown && (
            <div className="absolute top-full left-0 z-50 mt-1 max-h-[200px] min-w-[180px] overflow-y-auto rounded-md border bg-popover p-1 shadow-md">
              {getAvailableModels().map(model => (
                <button
                  key={model}
                  className={`w-full rounded px-2 py-1.5 text-left text-xs hover:bg-accent ${
                    selectedModel === model ? 'bg-accent' : ''
                  }`}
                  onClick={() => handleModelChange(model)}
                >
                  {model}
                </button>
              ))}
              {getAvailableModels().length === 0 && (
                <div className="px-2 py-1.5 text-xs text-muted-foreground">
                  No models available
                </div>
              )}
            </div>
          )}
        </div>
      </div>

      {/* MCP Panel (collapsible) */}
      {safeToolbarSettings.showMCPPanel && Array.isArray(mcpServers) && mcpServers.length > 0 && (
        <div className="rounded-md border bg-muted/30 p-2">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-medium">Active MCP Servers</span>
            <Button
              variant="ghost"
              size="icon"
              className="h-5 w-5"
              onClick={toggleMCPPanel}
            >
              <X className="h-3 w-3" />
            </Button>
          </div>
          <div className="flex flex-wrap gap-1">
            {mcpServers.map(server => (
              <button
                key={server.id}
                onClick={() => toggleMCPServer(server.id)}
                className={`rounded-full px-2 py-0.5 text-[10px] transition-colors ${
                  selectedMCPServers.includes(server.id)
                    ? 'bg-primary text-primary-foreground'
                    : 'bg-muted hover:bg-muted/80'
                }`}
                title={server.description}
              >
                {server.name}
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
