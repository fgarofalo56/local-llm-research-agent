import { describe, it, expect, beforeEach } from 'vitest';
import { useChatStore } from '../chatStore';
import type { Message } from '@/types';

// Reset store before each test
beforeEach(() => {
  const store = useChatStore.getState();
  // Reset to initial state
  store.setMessages([]);
  store.setCurrentConversation(null);
  store.setIsStreaming(false);
  store.clearStreamingContent();
  store.resetTokenCount();
});

describe('chatStore', () => {
  describe('conversation state', () => {
    it('sets current conversation ID', () => {
      const store = useChatStore.getState();
      store.setCurrentConversation(123);

      expect(useChatStore.getState().currentConversationId).toBe(123);
    });

    it('clears current conversation', () => {
      const store = useChatStore.getState();
      store.setCurrentConversation(123);
      store.setCurrentConversation(null);

      expect(useChatStore.getState().currentConversationId).toBeNull();
    });
  });

  describe('messages', () => {
    const testMessage: Message = {
      id: 1,
      conversation_id: 1,
      role: 'user',
      content: 'Hello',
      tool_calls: null,
      tokens_used: null,
      created_at: new Date().toISOString(),
    };

    it('sets messages array', () => {
      const store = useChatStore.getState();
      store.setMessages([testMessage]);

      expect(useChatStore.getState().messages).toHaveLength(1);
      expect(useChatStore.getState().messages[0]).toEqual(testMessage);
    });

    it('adds new message', () => {
      const store = useChatStore.getState();
      store.setMessages([testMessage]);
      store.addMessage({
        ...testMessage,
        id: 2,
        role: 'assistant',
        content: 'Hi there!',
      });

      expect(useChatStore.getState().messages).toHaveLength(2);
    });

    it('preserves existing messages when adding new one', () => {
      const store = useChatStore.getState();
      store.setMessages([testMessage]);
      store.addMessage({
        ...testMessage,
        id: 2,
        content: 'New message',
      });

      expect(useChatStore.getState().messages[0].content).toBe('Hello');
      expect(useChatStore.getState().messages[1].content).toBe('New message');
    });
  });

  describe('streaming', () => {
    it('sets streaming state', () => {
      const store = useChatStore.getState();
      store.setIsStreaming(true);

      expect(useChatStore.getState().isStreaming).toBe(true);
    });

    it('appends streaming content', () => {
      const store = useChatStore.getState();
      store.appendStreamingContent('Hello');
      store.appendStreamingContent(' world');

      expect(useChatStore.getState().streamingContent).toBe('Hello world');
    });

    it('clears streaming content', () => {
      const store = useChatStore.getState();
      store.appendStreamingContent('Some content');
      store.clearStreamingContent();

      expect(useChatStore.getState().streamingContent).toBe('');
    });
  });

  describe('MCP servers', () => {
    it('sets selected MCP servers', () => {
      const store = useChatStore.getState();
      store.setSelectedMCPServers(['server1', 'server2']);

      expect(useChatStore.getState().selectedMCPServers).toEqual(['server1', 'server2']);
    });

    it('toggles MCP server on', () => {
      const store = useChatStore.getState();
      store.setSelectedMCPServers(['mssql']);
      store.toggleMCPServer('postgres');

      expect(useChatStore.getState().selectedMCPServers).toContain('postgres');
      expect(useChatStore.getState().selectedMCPServers).toContain('mssql');
    });

    it('toggles MCP server off', () => {
      const store = useChatStore.getState();
      store.setSelectedMCPServers(['mssql', 'postgres']);
      store.toggleMCPServer('postgres');

      expect(useChatStore.getState().selectedMCPServers).not.toContain('postgres');
      expect(useChatStore.getState().selectedMCPServers).toContain('mssql');
    });
  });

  describe('model configuration', () => {
    it('sets selected provider', () => {
      const store = useChatStore.getState();
      store.setSelectedProvider('foundry_local');

      expect(useChatStore.getState().selectedProvider).toBe('foundry_local');
    });

    it('sets selected model', () => {
      const store = useChatStore.getState();
      store.setSelectedModel('phi-4');

      expect(useChatStore.getState().selectedModel).toBe('phi-4');
    });

    it('updates model parameters partially', () => {
      const store = useChatStore.getState();
      const originalParams = store.modelParameters;

      store.setModelParameters({ temperature: 0.5 });

      expect(useChatStore.getState().modelParameters.temperature).toBe(0.5);
      expect(useChatStore.getState().modelParameters.topP).toBe(originalParams.topP);
    });

    it('sets system prompt', () => {
      const store = useChatStore.getState();
      store.setSystemPrompt('Custom prompt');

      expect(useChatStore.getState().systemPrompt).toBe('Custom prompt');
    });
  });

  describe('token tracking', () => {
    it('updates token count', () => {
      const store = useChatStore.getState();
      store.updateTokenCount({ prompt: 100, completion: 50 });

      const state = useChatStore.getState();
      expect(state.tokenCount.prompt).toBe(100);
      expect(state.tokenCount.completion).toBe(50);
      expect(state.tokenCount.total).toBe(150);
    });

    it('resets token count', () => {
      const store = useChatStore.getState();
      store.updateTokenCount({ prompt: 100, completion: 50 });
      store.resetTokenCount();

      const state = useChatStore.getState();
      expect(state.tokenCount.prompt).toBe(0);
      expect(state.tokenCount.completion).toBe(0);
      expect(state.tokenCount.total).toBe(0);
    });
  });

  describe('RAG settings', () => {
    it('updates RAG settings partially', () => {
      const store = useChatStore.getState();
      store.setRAGSettings({ topK: 10 });

      expect(useChatStore.getState().ragSettings.topK).toBe(10);
      expect(useChatStore.getState().ragSettings.enabled).toBe(true); // unchanged
    });

    it('toggles RAG enabled state', () => {
      const store = useChatStore.getState();
      const initial = store.ragSettings.enabled;

      store.toggleRAG();
      expect(useChatStore.getState().ragSettings.enabled).toBe(!initial);

      store.toggleRAG();
      expect(useChatStore.getState().ragSettings.enabled).toBe(initial);
    });

    it('toggles hybrid search', () => {
      const store = useChatStore.getState();
      const initial = store.ragSettings.hybridSearch;

      store.toggleHybridSearch();
      expect(useChatStore.getState().ragSettings.hybridSearch).toBe(!initial);
    });
  });

  describe('message ratings', () => {
    it('rates message as up', () => {
      const store = useChatStore.getState();
      store.rateMessage(1, 'up');

      expect(useChatStore.getState().messageRatings[1]).toBe('up');
    });

    it('rates message as down', () => {
      const store = useChatStore.getState();
      store.rateMessage(1, 'down');

      expect(useChatStore.getState().messageRatings[1]).toBe('down');
    });

    it('clears rating', () => {
      const store = useChatStore.getState();
      store.rateMessage(1, 'up');
      store.rateMessage(1, null);

      expect(useChatStore.getState().messageRatings[1]).toBeNull();
    });

    it('handles multiple message ratings', () => {
      const store = useChatStore.getState();
      store.rateMessage(1, 'up');
      store.rateMessage(2, 'down');
      store.rateMessage(3, 'up');

      const ratings = useChatStore.getState().messageRatings;
      expect(ratings[1]).toBe('up');
      expect(ratings[2]).toBe('down');
      expect(ratings[3]).toBe('up');
    });
  });
});
