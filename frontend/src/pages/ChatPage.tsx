import { useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { FileText, Download } from 'lucide-react';
import { MessageList } from '@/components/chat/MessageList';
import { ChatInput } from '@/components/chat/ChatInput';
import { MCPServerSelector } from '@/components/chat/MCPServerSelector';
import { Button } from '@/components/ui/Button';
import { useMessages, useCreateConversation, useConversation } from '@/hooks/useConversations';
import { useAgentWebSocket } from '@/hooks/useWebSocket';
import { useChatStore } from '@/stores/chatStore';
import { exportChatToMarkdown, exportChatToPdf } from '@/lib/exports/chatExport';

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
      {/* Header with MCP Server Selection and Export */}
      <div className="flex items-center justify-between border-b p-4">
        <MCPServerSelector />

        {/* Export buttons - only show when we have a conversation */}
        {currentConversationId && messagesData?.messages && messagesData.messages.length > 0 && (
          <div className="flex gap-2">
            <Button variant="ghost" size="sm" onClick={handleExportMarkdown}>
              <FileText className="mr-2 h-4 w-4" />
              Export MD
            </Button>
            <Button variant="ghost" size="sm" onClick={handleExportPdf}>
              <Download className="mr-2 h-4 w-4" />
              Export PDF
            </Button>
          </div>
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
