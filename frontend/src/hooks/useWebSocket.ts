import { useEffect, useRef, useCallback } from 'react';
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

export function useAgentWebSocket(conversationId: number | null) {
  const wsRef = useRef<WebSocket | null>(null);
  const {
    appendStreamingContent,
    clearStreamingContent,
    setIsStreaming,
    addMessage,
    selectedMCPServers,
  } = useChatStore();

  const connect = useCallback(() => {
    if (!conversationId) return;

    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/ws/agent/${conversationId}`;

    wsRef.current = new WebSocket(wsUrl);

    wsRef.current.onopen = () => {
      console.log('WebSocket connected');
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
          setIsStreaming(false);
          break;
      }
    };

    wsRef.current.onerror = (error) => {
      console.error('WebSocket error:', error);
      setIsStreaming(false);
    };

    wsRef.current.onclose = () => {
      console.log('WebSocket closed');
    };
  }, [conversationId, appendStreamingContent, clearStreamingContent, setIsStreaming, addMessage]);

  const sendMessage = useCallback((content: string) => {
    if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) {
      console.error('WebSocket not connected');
      return;
    }

    clearStreamingContent();
    setIsStreaming(true);

    wsRef.current.send(JSON.stringify({
      type: 'message',
      content,
      mcp_servers: selectedMCPServers,
    }));
  }, [clearStreamingContent, setIsStreaming, selectedMCPServers]);

  const disconnect = useCallback(() => {
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
  }, []);

  useEffect(() => {
    connect();
    return () => disconnect();
  }, [connect, disconnect]);

  return { sendMessage, disconnect, reconnect: connect };
}
