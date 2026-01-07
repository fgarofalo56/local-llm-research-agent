import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import type { Message } from '@/types';

// Model parameters interface
interface ModelParameters {
  temperature: number;
  topP: number;
  maxTokens: number;
}

// Token count interface
interface TokenCount {
  prompt: number;
  completion: number;
  total: number;
  contextWindowSize: number;
}

// RAG settings interface
interface RAGSettings {
  enabled: boolean;
  hybridSearch: boolean;
  topK: number;
}

// Chat toolbar settings
interface ToolbarSettings {
  thinkingEnabled: boolean;
  webSearchEnabled: boolean;
  showMCPPanel: boolean;
}

// Agent status tracking
interface AgentStatus {
  isActive: boolean;
  currentPhase: string;  // 'thinking', 'tool_calling', 'generating', 'idle'
  toolName: string | null;
  toolArgs: Record<string, unknown> | null;
  animatedMessage: string;
}

// Provider config from localStorage (used by loadSavedSettings)

interface ChatState {
  // Conversation state
  currentConversationId: number | null;
  messages: Message[];
  isStreaming: boolean;
  streamingContent: string;

  // MCP servers
  selectedMCPServers: string[];

  // Model configuration
  selectedProvider: string;
  selectedModel: string;
  modelParameters: ModelParameters;
  systemPrompt: string;

  // Token tracking
  tokenCount: TokenCount;

  // RAG settings
  ragSettings: RAGSettings;

  // Toolbar settings
  toolbarSettings: ToolbarSettings;

  // Agent status for live indicators
  agentStatus: AgentStatus;

  // Message ratings (message_id -> rating)
  messageRatings: Record<number, 'up' | 'down' | null>;

  // Actions - Conversation
  setCurrentConversation: (id: number | null) => void;
  setMessages: (messages: Message[]) => void;
  addMessage: (message: Message) => void;
  setIsStreaming: (isStreaming: boolean) => void;
  appendStreamingContent: (content: string) => void;
  clearStreamingContent: () => void;

  // Actions - MCP Servers
  setSelectedMCPServers: (servers: string[]) => void;
  toggleMCPServer: (serverId: string) => void;

  // Actions - Model Configuration
  setSelectedProvider: (provider: string) => void;
  setSelectedModel: (model: string) => void;
  setModelParameters: (params: Partial<ModelParameters>) => void;
  setSystemPrompt: (prompt: string) => void;

  // Actions - Token Tracking
  updateTokenCount: (count: Partial<TokenCount>) => void;
  resetTokenCount: () => void;

  // Actions - RAG
  setRAGSettings: (settings: Partial<RAGSettings>) => void;
  toggleRAG: () => void;
  toggleHybridSearch: () => void;

  // Actions - Toolbar
  setToolbarSettings: (settings: Partial<ToolbarSettings>) => void;
  toggleThinking: () => void;
  toggleWebSearch: () => void;
  toggleMCPPanel: () => void;

  // Actions - Agent Status
  setAgentStatus: (status: Partial<AgentStatus>) => void;
  setToolCall: (toolName: string, toolArgs: Record<string, unknown>) => void;
  setAgentActive: (isActive: boolean) => void;
  clearToolCall: () => void;

  // Actions - Ratings
  rateMessage: (messageId: number, rating: 'up' | 'down' | null) => void;

  // Load settings from localStorage
  loadSavedSettings: () => void;
}

// Default values
const DEFAULT_MODEL_PARAMS: ModelParameters = {
  temperature: 0.7,
  topP: 0.9,
  maxTokens: 2048,
};

const DEFAULT_TOKEN_COUNT: TokenCount = {
  prompt: 0,
  completion: 0,
  total: 0,
  contextWindowSize: 32768, // Default context window
};

const DEFAULT_RAG_SETTINGS: RAGSettings = {
  enabled: true,
  hybridSearch: true,
  topK: 5,
};

const DEFAULT_TOOLBAR_SETTINGS: ToolbarSettings = {
  thinkingEnabled: false,
  webSearchEnabled: false,
  showMCPPanel: false,
};

const DEFAULT_AGENT_STATUS: AgentStatus = {
  isActive: false,
  currentPhase: 'idle',
  toolName: null,
  toolArgs: null,
  animatedMessage: '',
};

const DEFAULT_SYSTEM_PROMPT = `You are a helpful research assistant with access to SQL Server databases.
You can query data, analyze results, and provide insights.
Always explain your reasoning and the SQL queries you generate.`;

export const useChatStore = create<ChatState>()(
  persist(
    (set) => ({
      // Initial state
      currentConversationId: null,
      messages: [],
      isStreaming: false,
      streamingContent: '',
      selectedMCPServers: ['mssql'],
      selectedProvider: 'ollama',
      selectedModel: 'qwen3:30b',
      modelParameters: DEFAULT_MODEL_PARAMS,
      systemPrompt: DEFAULT_SYSTEM_PROMPT,
      tokenCount: DEFAULT_TOKEN_COUNT,
      ragSettings: DEFAULT_RAG_SETTINGS,
      toolbarSettings: DEFAULT_TOOLBAR_SETTINGS,
      agentStatus: DEFAULT_AGENT_STATUS,
      messageRatings: {},

      // Conversation actions
      setCurrentConversation: (id) => set({ currentConversationId: id }),
      setMessages: (messages) => set({ messages }),
      addMessage: (message) => set((state) => ({ messages: [...state.messages, message] })),
      setIsStreaming: (isStreaming) => set({ isStreaming }),
      appendStreamingContent: (content) =>
        set((state) => ({ streamingContent: state.streamingContent + content })),
      clearStreamingContent: () => set({ streamingContent: '' }),

      // MCP Server actions
      setSelectedMCPServers: (servers) => set({ selectedMCPServers: servers }),
      toggleMCPServer: (serverId) =>
        set((state) => ({
          selectedMCPServers: state.selectedMCPServers.includes(serverId)
            ? state.selectedMCPServers.filter((id) => id !== serverId)
            : [...state.selectedMCPServers, serverId],
        })),

      // Model configuration actions
      setSelectedProvider: (provider) => set({ selectedProvider: provider }),
      setSelectedModel: (model) => set({ selectedModel: model }),
      setModelParameters: (params) =>
        set((state) => ({
          modelParameters: { ...state.modelParameters, ...params },
        })),
      setSystemPrompt: (prompt) => set({ systemPrompt: prompt }),

      // Token tracking actions
      updateTokenCount: (count) =>
        set((state) => ({
          tokenCount: {
            ...state.tokenCount,
            ...count,
            total: (count.prompt ?? state.tokenCount.prompt) + (count.completion ?? state.tokenCount.completion),
          },
        })),
      resetTokenCount: () => set({ tokenCount: DEFAULT_TOKEN_COUNT }),

      // RAG actions
      setRAGSettings: (settings) =>
        set((state) => ({
          ragSettings: { ...state.ragSettings, ...settings },
        })),
      toggleRAG: () =>
        set((state) => ({
          ragSettings: { ...state.ragSettings, enabled: !state.ragSettings.enabled },
        })),
      toggleHybridSearch: () =>
        set((state) => ({
          ragSettings: { ...state.ragSettings, hybridSearch: !state.ragSettings.hybridSearch },
        })),

      // Toolbar actions
      setToolbarSettings: (settings) =>
        set((state) => ({
          toolbarSettings: { ...state.toolbarSettings, ...settings },
        })),
      toggleThinking: () =>
        set((state) => ({
          toolbarSettings: { ...state.toolbarSettings, thinkingEnabled: !state.toolbarSettings.thinkingEnabled },
        })),
      toggleWebSearch: () =>
        set((state) => ({
          toolbarSettings: { ...state.toolbarSettings, webSearchEnabled: !state.toolbarSettings.webSearchEnabled },
        })),
      toggleMCPPanel: () =>
        set((state) => ({
          toolbarSettings: { ...state.toolbarSettings, showMCPPanel: !state.toolbarSettings.showMCPPanel },
        })),

      // Agent Status actions
      setAgentStatus: (status) =>
        set((state) => ({
          agentStatus: { ...state.agentStatus, ...status },
        })),
      setToolCall: (toolName, toolArgs) =>
        set((state) => ({
          agentStatus: {
            ...state.agentStatus,
            currentPhase: 'tool_calling',
            toolName,
            toolArgs,
          },
        })),
      setAgentActive: (isActive) =>
        set((state) => ({
          agentStatus: {
            ...state.agentStatus,
            isActive,
            currentPhase: isActive ? 'thinking' : 'idle',
            toolName: isActive ? state.agentStatus.toolName : null,
            toolArgs: isActive ? state.agentStatus.toolArgs : null,
          },
        })),
      clearToolCall: () =>
        set((state) => ({
          agentStatus: {
            ...state.agentStatus,
            currentPhase: 'generating',
            toolName: null,
            toolArgs: null,
          },
        })),

      // Rating actions
      rateMessage: (messageId, rating) =>
        set((state) => ({
          messageRatings: {
            ...state.messageRatings,
            [messageId]: rating,
          },
        })),

      // Load saved settings from localStorage (for provider config)
      loadSavedSettings: () => {
        try {
          const saved = localStorage.getItem('llm-settings');
          if (saved) {
            const parsed = JSON.parse(saved);
            if (parsed.primary) {
              set({
                selectedProvider: parsed.primary.provider || 'ollama',
                selectedModel: parsed.primary.model || 'qwen3:30b',
              });
            }
          }
        } catch {
          // Ignore parse errors
        }
      },
    }),
    {
      name: 'chat-settings',
      partialize: (state) => ({
        selectedMCPServers: state.selectedMCPServers,
        selectedProvider: state.selectedProvider,
        selectedModel: state.selectedModel,
        modelParameters: state.modelParameters,
        systemPrompt: state.systemPrompt,
        ragSettings: state.ragSettings,
        toolbarSettings: state.toolbarSettings,
      }),
      // Custom merge function to handle partial/corrupted localStorage data
      merge: (persistedState, currentState) => {
        const persisted = persistedState as Partial<ChatState> | undefined;
        return {
          ...currentState,
          // Primitives - use persisted or current
          selectedMCPServers: persisted?.selectedMCPServers ?? currentState.selectedMCPServers,
          selectedProvider: persisted?.selectedProvider ?? currentState.selectedProvider,
          selectedModel: persisted?.selectedModel ?? currentState.selectedModel,
          systemPrompt: persisted?.systemPrompt ?? currentState.systemPrompt,
          // Nested objects - deep merge with defaults to handle partial objects
          modelParameters: {
            ...DEFAULT_MODEL_PARAMS,
            ...(persisted?.modelParameters ?? {}),
          },
          ragSettings: {
            ...DEFAULT_RAG_SETTINGS,
            ...(persisted?.ragSettings ?? {}),
          },
          toolbarSettings: {
            ...DEFAULT_TOOLBAR_SETTINGS,
            ...(persisted?.toolbarSettings ?? {}),
          },
        };
      },
    }
  )
);
