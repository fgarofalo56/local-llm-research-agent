import { useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { MessageList } from '@/components/chat/MessageList';
import { ChatInput } from '@/components/chat/ChatInput';
import { MCPServerSelector } from '@/components/chat/MCPServerSelector';
import { useMessages, useCreateConversation } from '@/hooks/useConversations';
import { useAgentWebSocket } from '@/hooks/useWebSocket';
import { useChatStore } from '@/stores/chatStore';

export function ChatPage() {
  const { conversationId } = useParams<{ conversationId: string }>();
  const { currentConversationId, setCurrentConversation, setMessages } = useChatStore();
  const createConversation = useCreateConversation();

  // Parse conversation ID
  const parsedId = conversationId ? parseInt(conversationId, 10) : null;

  // Set current conversation
  useEffect(() => {
    if (parsedId) {
      setCurrentConversation(parsedId);
    }
  }, [parsedId, setCurrentConversation]);

  // Fetch messages
  const { data: messagesData } = useMessages(currentConversationId);

  // Update messages in store
  useEffect(() => {
    if (messagesData?.messages) {
      setMessages(messagesData.messages);
    }
  }, [messagesData, setMessages]);

  // WebSocket connection
  const { sendMessage } = useAgentWebSocket(currentConversationId);

  const handleSendMessage = async (content: string) => {
    // Create conversation if needed
    if (!currentConversationId) {
      const conversation = await createConversation.mutateAsync(content.slice(0, 50));
      setCurrentConversation(conversation.id);
      // Wait for WebSocket to connect before sending
      setTimeout(() => sendMessage(content), 100);
    } else {
      sendMessage(content);
    }
  };

  return (
    <div className="flex h-full flex-col">
      {/* MCP Server Selection */}
      <div className="border-b p-4">
        <MCPServerSelector />
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
