import { Link, useLocation } from 'react-router-dom';
import {
  MessageSquare,
  FileText,
  LayoutDashboard,
  Settings,
  Database,
  History,
  Plus,
  BarChart3,
  Link2,
  Activity,
  Sparkles,
  Clock,
  type LucideIcon,
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';
import { useConversations, useCreateConversation } from '@/hooks/useConversations';
import { useChatStore } from '@/stores/chatStore';

// Grouped navigation structure for better organization
interface NavSection {
  title?: string;
  items: {
    path: string;
    icon: LucideIcon;
    label: string;
    badge?: string;
    badgeVariant?: 'default' | 'success' | 'warning' | 'info';
  }[];
}

const navSections: NavSection[] = [
  {
    title: 'Main',
    items: [
      { path: '/chat', icon: MessageSquare, label: 'Chat' },
      { path: '/documents', icon: FileText, label: 'Documents' },
      { path: '/dashboards', icon: LayoutDashboard, label: 'Dashboards' },
      { path: '/queries', icon: History, label: 'Query History' },
    ],
  },
  {
    title: 'Analytics',
    items: [
      { path: '/analytics', icon: Activity, label: 'Analytics' },
      { path: '/superset', icon: BarChart3, label: 'Superset Reports' },
    ],
  },
  {
    title: 'Configuration',
    items: [
      { path: '/mcp-servers', icon: Database, label: 'MCP Servers' },
      { path: '/database-connections', icon: Link2, label: 'DB Connections' },
      { path: '/settings', icon: Settings, label: 'Settings' },
    ],
  },
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

  const isActive = (path: string) =>
    location.pathname === path || location.pathname.startsWith(path + '/');

  return (
    <aside className="flex w-64 flex-col border-r bg-card/50 backdrop-blur-sm">
      {/* Logo/Brand with gradient accent */}
      <div className="flex h-14 items-center border-b px-4 bg-gradient-to-r from-primary/5 to-transparent">
        <div className="flex items-center gap-2">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary text-primary-foreground">
            <Sparkles className="h-4 w-4" />
          </div>
          <div className="flex flex-col">
            <span className="font-semibold text-sm leading-tight">Research</span>
            <span className="text-xs text-muted-foreground leading-tight">Analytics Agent</span>
          </div>
        </div>
      </div>

      {/* New Chat Button */}
      <div className="p-3">
        <Button
          className="w-full shadow-sm"
          onClick={handleNewChat}
          isLoading={createConversation.isPending}
          loadingText="Creating..."
          leftIcon={<Plus className="h-4 w-4" />}
        >
          New Chat
        </Button>
      </div>

      {/* Navigation with sections */}
      <nav className="flex-1 overflow-y-auto px-3 pb-4" role="navigation" aria-label="Main navigation">
        {navSections.map((section, sectionIndex) => (
          <div key={section.title || sectionIndex} className={cn(sectionIndex > 0 && 'mt-6')}>
            {section.title && (
              <h3 className="mb-2 px-3 text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                {section.title}
              </h3>
            )}
            <div className="space-y-1">
              {section.items.map((item) => (
                <Link
                  key={item.path}
                  to={item.path}
                  className={cn(
                    'group flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-all duration-200',
                    isActive(item.path)
                      ? 'bg-primary text-primary-foreground shadow-sm'
                      : 'text-muted-foreground hover:bg-accent hover:text-accent-foreground'
                  )}
                  aria-current={isActive(item.path) ? 'page' : undefined}
                >
                  <item.icon
                    className={cn(
                      'h-4 w-4 shrink-0 transition-transform duration-200',
                      !isActive(item.path) && 'group-hover:scale-110'
                    )}
                  />
                  <span className="flex-1 truncate">{item.label}</span>
                  {item.badge && (
                    <Badge
                      variant={item.badgeVariant || 'info'}
                      size="sm"
                      className={cn(
                        isActive(item.path) && 'bg-primary-foreground/20 text-primary-foreground'
                      )}
                    >
                      {item.badge}
                    </Badge>
                  )}
                </Link>
              ))}
            </div>
          </div>
        ))}
      </nav>

      {/* Recent Conversations with improved styling */}
      <div className="border-t bg-muted/30">
        <div className="p-3">
          <div className="flex items-center gap-2 mb-3 px-1">
            <Clock className="h-3.5 w-3.5 text-muted-foreground" />
            <h3 className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
              Recent Chats
            </h3>
          </div>
          <div className="space-y-1">
            {conversationsData?.conversations.length === 0 ? (
              <p className="px-2 py-3 text-center text-xs text-muted-foreground">
                No recent conversations
              </p>
            ) : (
              conversationsData?.conversations.slice(0, 5).map((conv) => (
                <Link
                  key={conv.id}
                  to={`/chat/${conv.id}`}
                  className={cn(
                    'block truncate rounded-md px-3 py-1.5 text-sm transition-colors',
                    location.pathname === `/chat/${conv.id}`
                      ? 'bg-accent text-accent-foreground font-medium'
                      : 'text-muted-foreground hover:bg-accent hover:text-accent-foreground'
                  )}
                  title={conv.title || `Chat ${conv.id}`}
                >
                  {conv.title || `Chat ${conv.id}`}
                </Link>
              ))
            )}
          </div>
        </div>
      </div>
    </aside>
  );
}
