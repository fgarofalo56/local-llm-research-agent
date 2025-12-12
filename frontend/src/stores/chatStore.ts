import { create } from 'zustand';
import type { Message } from '@/types';

interface ChatState {
  currentConversationId: number | null;
  messages: Message[];
  isStreaming: boolean;
  streamingContent: string;
  selectedMCPServers: string[];

  setCurrentConversation: (id: number | null) => void;
  setMessages: (messages: Message[]) => void;
  addMessage: (message: Message) => void;
  setIsStreaming: (isStreaming: boolean) => void;
  appendStreamingContent: (content: string) => void;
  clearStreamingContent: () => void;
  setSelectedMCPServers: (servers: string[]) => void;
  toggleMCPServer: (serverId: string) => void;
}

export const useChatStore = create<ChatState>((set) => ({
  currentConversationId: null,
  messages: [],
  isStreaming: false,
  streamingContent: '',
  selectedMCPServers: ['mssql'], // Default enabled servers

  setCurrentConversation: (id) => set({ currentConversationId: id }),
  setMessages: (messages) => set({ messages }),
  addMessage: (message) => set((state) => ({ messages: [...state.messages, message] })),
  setIsStreaming: (isStreaming) => set({ isStreaming }),
  appendStreamingContent: (content) =>
    set((state) => ({ streamingContent: state.streamingContent + content })),
  clearStreamingContent: () => set({ streamingContent: '' }),
  setSelectedMCPServers: (servers) => set({ selectedMCPServers: servers }),
  toggleMCPServer: (serverId) =>
    set((state) => ({
      selectedMCPServers: state.selectedMCPServers.includes(serverId)
        ? state.selectedMCPServers.filter((id) => id !== serverId)
        : [...state.selectedMCPServers, serverId],
    })),
}));
