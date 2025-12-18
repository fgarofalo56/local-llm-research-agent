import { useEffect, useRef, useCallback, useState } from 'react';
import { useChatStore } from '@/stores/chatStore';
import type { Message } from '@/types';

interface WebSocketMessage {
  type: 'chunk' | 'complete' | 'error' | 'tool_call';
  content?: string;
  message?: Message;
  tool_name?: string;
  tool_args?: Record<string, unknown>;
  error?: string;
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
  const {
    appendStreamingContent,
    clearStreamingContent,
    setIsStreaming,
    addMessage,
    selectedMCPServers,
    selectedProvider,
    selectedModel,
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
        }));
        pending.resolve();
      }
    }
  }, [clearStreamingContent, setIsStreaming, selectedMCPServers, selectedProvider, selectedModel]);

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
          appendStreamingContent(data.content || '');
          break;
        case 'complete':
          if (data.message) {
            addMessage(data.message);
          }
          clearStreamingContent();
          setIsStreaming(false);
          break;
        case 'tool_call':
          // Could show tool call indicator in UI
          console.log('Tool call:', data.tool_name, data.tool_args);
          break;
        case 'error':
          console.error('Agent error:', data.error);
          clearStreamingContent();
          setIsStreaming(false);
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
  }, [conversationId, appendStreamingContent, clearStreamingContent, setIsStreaming, addMessage, processPendingMessages]);

  const sendMessage = useCallback((content: string): Promise<void> => {
    return new Promise((resolve, reject) => {
      // If connected, send immediately
      if (wsRef.current?.readyState === WebSocket.OPEN) {
        clearStreamingContent();
        setIsStreaming(true);
        wsRef.current.send(JSON.stringify({
          type: 'message',
          content,
          mcp_servers: selectedMCPServers,
          provider: selectedProvider,
          model: selectedModel,
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
  }, [clearStreamingContent, setIsStreaming, selectedMCPServers, selectedProvider, selectedModel]);

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

  useEffect(() => {
    connect();
    return () => disconnect();
  }, [connect, disconnect]);

  return { sendMessage, disconnect, reconnect: connect, isConnected };
}
