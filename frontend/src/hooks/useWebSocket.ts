import { useEffect, useRef, useCallback, useState } from 'react';
import { useChatStore } from '@/stores/chatStore';
import type { Message } from '@/types';

interface WebSocketMessage {
  type: 'chunk' | 'complete' | 'error' | 'tool_call' | 'warning';
  content?: string;
  message?: Message;
  tool_name?: string;
  tool_args?: Record<string, unknown>;
  error?: string;
  warning?: string;
  warning_type?: string;
}

// Queue for messages waiting to be sent
interface PendingMessage {
  content: string;
  resolve: () => void;
  reject: (error: Error) => void;
}

export function useAgentWebSocket(conversationId: number | null) {
  const wsRef = useRef<WebSocket | null>(null);
  const pendingMessagesRef = useRef<PendingMessage[]>([]);
  const [isConnected, setIsConnected] = useState(false);
  const [lastWarning, setLastWarning] = useState<{ message: string; type: string } | null>(null);
  const {
    appendStreamingContent,
    clearStreamingContent,
    setIsStreaming,
    addMessage,
    selectedMCPServers,
    selectedProvider,
    selectedModel,
    setToolCall,
    setAgentActive,
    clearToolCall,
    toolbarSettings,
    ragSettings,
  } = useChatStore();

  // Process pending messages when connection opens
  const processPendingMessages = useCallback(() => {
    while (pendingMessagesRef.current.length > 0 && wsRef.current?.readyState === WebSocket.OPEN) {
      const pending = pendingMessagesRef.current.shift();
      if (pending) {
        clearStreamingContent();
        setIsStreaming(true);
        wsRef.current.send(JSON.stringify({
          type: 'message',
          content: pending.content,
          mcp_servers: selectedMCPServers,
          provider: selectedProvider,
          model: selectedModel,
          thinking_enabled: toolbarSettings.thinkingEnabled,
          rag_enabled: ragSettings.enabled,
          rag_top_k: ragSettings.topK,
          rag_hybrid_search: ragSettings.hybridSearch,
        }));
        pending.resolve();
      }
    }
  }, [clearStreamingContent, setIsStreaming, selectedMCPServers, selectedProvider, selectedModel, toolbarSettings, ragSettings]);

  const connect = useCallback(() => {
    if (!conversationId) return;

    // Close existing connection if any
    if (wsRef.current) {
      wsRef.current.close();
    }

    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/ws/agent/${conversationId}`;

    wsRef.current = new WebSocket(wsUrl);

    wsRef.current.onopen = () => {
      console.log('WebSocket connected');
      setIsConnected(true);
      // Process any pending messages
      processPendingMessages();
    };

    wsRef.current.onmessage = (event) => {
      const data: WebSocketMessage = JSON.parse(event.data);

      switch (data.type) {
        case 'chunk':
          // Clear tool call when we start getting response chunks
          clearToolCall();
          appendStreamingContent(data.content || '');
          break;
        case 'complete':
          if (data.message) {
            addMessage(data.message);
          }
          clearStreamingContent();
          setIsStreaming(false);
          setAgentActive(false);
          break;
        case 'tool_call':
          // Update agent status with tool call info
          if (data.tool_name) {
            setToolCall(data.tool_name, data.tool_args || {});
          }
          console.log('Tool call:', data.tool_name, data.tool_args);
          break;
        case 'warning':
          // Tool calling or other warnings from backend
          console.warn('Agent warning:', data.warning);
          setLastWarning({
            message: data.warning || 'Unknown warning',
            type: data.warning_type || 'unknown',
          });
          break;
        case 'error':
          console.error('Agent error:', data.error);
          clearStreamingContent();
          setIsStreaming(false);
          setAgentActive(false);
          break;
      }
    };

    wsRef.current.onerror = (error) => {
      console.error('WebSocket error:', error);
      setIsConnected(false);
      setIsStreaming(false);
    };

    wsRef.current.onclose = () => {
      console.log('WebSocket closed');
      setIsConnected(false);
    };
  }, [conversationId, appendStreamingContent, clearStreamingContent, setIsStreaming, addMessage, processPendingMessages, setToolCall, clearToolCall, setAgentActive]);

  const sendMessage = useCallback((content: string): Promise<void> => {
    return new Promise((resolve, reject) => {
      // If connected, send immediately
      if (wsRef.current?.readyState === WebSocket.OPEN) {
        clearStreamingContent();
        setIsStreaming(true);
        setAgentActive(true);  // Start agent status indicator
        wsRef.current.send(JSON.stringify({
          type: 'message',
          content,
          mcp_servers: selectedMCPServers,
          provider: selectedProvider,
          model: selectedModel,
          thinking_enabled: toolbarSettings.thinkingEnabled,
          rag_enabled: ragSettings.enabled,
          rag_top_k: ragSettings.topK,
          rag_hybrid_search: ragSettings.hybridSearch,
        }));
        resolve();
      } else {
        // Queue message for when connection opens
        console.log('WebSocket not ready, queueing message');
        pendingMessagesRef.current.push({ content, resolve, reject });

        // If WebSocket is connecting, wait for it
        if (wsRef.current?.readyState === WebSocket.CONNECTING) {
          // Message will be sent when onopen fires
          return;
        }

        // If no connection at all, try to connect (will happen when conversationId changes)
        // Set a timeout to reject if connection doesn't happen
        setTimeout(() => {
          const idx = pendingMessagesRef.current.findIndex(p => p.content === content);
          if (idx !== -1) {
            pendingMessagesRef.current.splice(idx, 1);
            reject(new Error('WebSocket connection timeout'));
          }
        }, 10000);
      }
    });
  }, [clearStreamingContent, setIsStreaming, setAgentActive, selectedMCPServers, selectedProvider, selectedModel, toolbarSettings, ragSettings]);

  const disconnect = useCallback(() => {
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
    setIsConnected(false);
    // Reject any pending messages
    pendingMessagesRef.current.forEach(p => p.reject(new Error('WebSocket disconnected')));
    pendingMessagesRef.current = [];
  }, []);

  const clearWarning = useCallback(() => {
    setLastWarning(null);
  }, []);

  useEffect(() => {
    connect();
    return () => disconnect();
  }, [connect, disconnect]);

  return { sendMessage, disconnect, reconnect: connect, isConnected, lastWarning, clearWarning };
}
