import { useLocation, Link } from 'react-router-dom';
import { Moon, Sun, Monitor, ChevronRight, Bell, User, LogOut } from 'lucide-react';
import { useTheme } from '@/contexts/ThemeContext';
import { useAuth } from '@/contexts/AuthContext';
import { Button } from '@/components/ui/Button';
import * as DropdownMenu from '@radix-ui/react-dropdown-menu';

// Page title and icon mapping
const pageConfig: Record<string, { title: string; description?: string }> = {
  '/chat': { title: 'Chat', description: 'Ask questions about your data' },
  '/documents': { title: 'Documents', description: 'Manage knowledge base documents' },
  '/dashboards': { title: 'Dashboards', description: 'View and manage dashboards' },
  '/queries': { title: 'Query History', description: 'View past queries and results' },
  '/analytics': { title: 'Analytics', description: 'Usage metrics and insights' },
  '/mcp-servers': { title: 'MCP Servers', description: 'Manage MCP server connections' },
  '/database-connections': { title: 'Database Connections', description: 'Configure database access' },
  '/superset': { title: 'Superset Reports', description: 'Apache Superset integration' },
  '/settings': { title: 'Settings', description: 'Application configuration' },
  '/settings/database': { title: 'Database Settings', description: 'Backend database configuration' },
};

// Generate breadcrumbs from path
function getBreadcrumbs(pathname: string) {
  const segments = pathname.split('/').filter(Boolean);
  const breadcrumbs: { label: string; path: string }[] = [];

  let currentPath = '';
  for (const segment of segments) {
    currentPath += `/${segment}`;
    const config = pageConfig[currentPath];
    breadcrumbs.push({
      label: config?.title || segment.charAt(0).toUpperCase() + segment.slice(1).replace(/-/g, ' '),
      path: currentPath,
    });
  }

  return breadcrumbs;
}

export function Header() {
  const location = useLocation();
  const { mode, setMode } = useTheme();
  const { user, logout, isAuthenticated } = useAuth();

  const breadcrumbs = getBreadcrumbs(location.pathname);
  const currentPage = pageConfig[location.pathname] || pageConfig[`/${location.pathname.split('/')[1]}`];

  return (
    <header className="flex h-14 items-center justify-between border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60 px-6">
      {/* Left side - Breadcrumbs and page info */}
      <div className="flex items-center gap-2">
        {/* Breadcrumbs */}
        <nav aria-label="Breadcrumb" className="flex items-center text-sm">
          {breadcrumbs.map((crumb, index) => (
            <div key={crumb.path} className="flex items-center">
              {index > 0 && (
                <ChevronRight className="mx-1.5 h-4 w-4 text-muted-foreground" aria-hidden="true" />
              )}
              {index === breadcrumbs.length - 1 ? (
                <span className="font-medium text-foreground">{crumb.label}</span>
              ) : (
                <Link
                  to={crumb.path}
                  className="text-muted-foreground hover:text-foreground transition-colors"
                >
                  {crumb.label}
                </Link>
              )}
            </div>
          ))}
        </nav>

        {/* Page description (on larger screens) */}
        {currentPage?.description && (
          <span className="hidden md:inline-block text-sm text-muted-foreground border-l pl-3 ml-2">
            {currentPage.description}
          </span>
        )}
      </div>

      {/* Right side - Actions */}
      <div className="flex items-center gap-2">
        {/* Notifications (placeholder) */}
        <Button variant="ghost" size="icon" className="relative" aria-label="Notifications">
          <Bell className="h-5 w-5" />
          <span className="sr-only">Notifications</span>
        </Button>

        {/* Theme Toggle */}
        <DropdownMenu.Root>
          <DropdownMenu.Trigger asChild>
            <Button variant="ghost" size="icon" aria-label="Toggle theme">
              {mode === 'dark' ? (
                <Moon className="h-5 w-5" />
              ) : mode === 'light' ? (
                <Sun className="h-5 w-5" />
              ) : (
                <Monitor className="h-5 w-5" />
              )}
              <span className="sr-only">Toggle theme</span>
            </Button>
          </DropdownMenu.Trigger>
          <DropdownMenu.Portal>
            <DropdownMenu.Content
              className="min-w-[140px] rounded-lg border bg-card p-1.5 shadow-lg animate-scale-in"
              sideOffset={5}
              align="end"
            >
              <DropdownMenu.Item
                className="flex cursor-pointer items-center gap-2 rounded-md px-2.5 py-2 text-sm outline-none transition-colors hover:bg-accent focus:bg-accent"
                onClick={() => setMode('light')}
              >
                <Sun className="h-4 w-4" />
                Light
                {mode === 'light' && <span className="ml-auto text-primary">✓</span>}
              </DropdownMenu.Item>
              <DropdownMenu.Item
                className="flex cursor-pointer items-center gap-2 rounded-md px-2.5 py-2 text-sm outline-none transition-colors hover:bg-accent focus:bg-accent"
                onClick={() => setMode('dark')}
              >
                <Moon className="h-4 w-4" />
                Dark
                {mode === 'dark' && <span className="ml-auto text-primary">✓</span>}
              </DropdownMenu.Item>
              <DropdownMenu.Item
                className="flex cursor-pointer items-center gap-2 rounded-md px-2.5 py-2 text-sm outline-none transition-colors hover:bg-accent focus:bg-accent"
                onClick={() => setMode('system')}
              >
                <Monitor className="h-4 w-4" />
                System
                {mode === 'system' && <span className="ml-auto text-primary">✓</span>}
              </DropdownMenu.Item>
            </DropdownMenu.Content>
          </DropdownMenu.Portal>
        </DropdownMenu.Root>

        {/* User Menu */}
        {isAuthenticated && (
          <DropdownMenu.Root>
            <DropdownMenu.Trigger asChild>
              <Button variant="ghost" size="icon" className="rounded-full" aria-label="User menu">
                <div className="flex h-8 w-8 items-center justify-center rounded-full bg-primary text-primary-foreground text-sm font-medium">
                  {user?.username?.charAt(0).toUpperCase() || 'U'}
                </div>
              </Button>
            </DropdownMenu.Trigger>
            <DropdownMenu.Portal>
              <DropdownMenu.Content
                className="min-w-[180px] rounded-lg border bg-card p-1.5 shadow-lg animate-scale-in"
                sideOffset={5}
                align="end"
              >
                <div className="px-2.5 py-2 border-b mb-1">
                  <p className="text-sm font-medium">{user?.username}</p>
                  <p className="text-xs text-muted-foreground">{user?.email}</p>
                </div>
                <DropdownMenu.Item
                  className="flex cursor-pointer items-center gap-2 rounded-md px-2.5 py-2 text-sm outline-none transition-colors hover:bg-accent focus:bg-accent"
                  asChild
                >
                  <Link to="/settings">
                    <User className="h-4 w-4" />
                    Profile Settings
                  </Link>
                </DropdownMenu.Item>
                <DropdownMenu.Separator className="my-1 h-px bg-border" />
                <DropdownMenu.Item
                  className="flex cursor-pointer items-center gap-2 rounded-md px-2.5 py-2 text-sm text-destructive outline-none transition-colors hover:bg-destructive/10 focus:bg-destructive/10"
                  onClick={logout}
                >
                  <LogOut className="h-4 w-4" />
                  Sign Out
                </DropdownMenu.Item>
              </DropdownMenu.Content>
            </DropdownMenu.Portal>
          </DropdownMenu.Root>
        )}
      </div>
    </header>
  );
}
