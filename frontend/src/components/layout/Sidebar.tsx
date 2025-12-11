import { Link, useLocation } from 'react-router-dom';
import {
  MessageSquare,
  FileText,
  LayoutDashboard,
  Settings,
  Database,
  History,
  Plus,
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { Button } from '@/components/ui/Button';
import { useConversations, useCreateConversation } from '@/hooks/useConversations';
import { useChatStore } from '@/stores/chatStore';

const navItems = [
  { path: '/chat', icon: MessageSquare, label: 'Chat' },
  { path: '/documents', icon: FileText, label: 'Documents' },
  { path: '/dashboards', icon: LayoutDashboard, label: 'Dashboards' },
  { path: '/queries', icon: History, label: 'Query History' },
  { path: '/mcp-servers', icon: Database, label: 'MCP Servers' },
  { path: '/settings', icon: Settings, label: 'Settings' },
];

export function Sidebar() {
  const location = useLocation();
  const { data: conversationsData } = useConversations();
  const createConversation = useCreateConversation();
  const { setCurrentConversation } = useChatStore();

  const handleNewChat = async () => {
    const conversation = await createConversation.mutateAsync(undefined);
    setCurrentConversation(conversation.id);
  };

  return (
    <aside className="flex w-64 flex-col border-r bg-card">
      {/* Logo/Brand */}
      <div className="flex h-14 items-center border-b px-4">
        <Database className="mr-2 h-6 w-6 text-primary" />
        <span className="font-semibold">Research Analytics</span>
      </div>

      {/* New Chat Button */}
      <div className="p-4">
        <Button
          className="w-full"
          onClick={handleNewChat}
          disabled={createConversation.isPending}
        >
          <Plus className="mr-2 h-4 w-4" />
          New Chat
        </Button>
      </div>

      {/* Navigation */}
      <nav className="flex-1 space-y-1 px-2">
        {navItems.map((item) => (
          <Link
            key={item.path}
            to={item.path}
            className={cn(
              'flex items-center rounded-md px-3 py-2 text-sm font-medium transition-colors',
              location.pathname === item.path || location.pathname.startsWith(item.path + '/')
                ? 'bg-accent text-accent-foreground'
                : 'text-muted-foreground hover:bg-accent hover:text-accent-foreground'
            )}
          >
            <item.icon className="mr-3 h-4 w-4" />
            {item.label}
          </Link>
        ))}
      </nav>

      {/* Recent Conversations */}
      <div className="border-t p-4">
        <h3 className="mb-2 text-xs font-semibold uppercase text-muted-foreground">
          Recent Chats
        </h3>
        <div className="space-y-1">
          {conversationsData?.conversations.slice(0, 5).map((conv) => (
            <Link
              key={conv.id}
              to={`/chat/${conv.id}`}
              className="block truncate rounded-md px-2 py-1 text-sm text-muted-foreground hover:bg-accent hover:text-accent-foreground"
            >
              {conv.title || `Chat ${conv.id}`}
            </Link>
          ))}
        </div>
      </div>
    </aside>
  );
}
