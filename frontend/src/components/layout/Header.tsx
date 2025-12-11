import { Moon, Sun, Monitor } from 'lucide-react';
import { useTheme } from '@/contexts/ThemeContext';
import { Button } from '@/components/ui/Button';
import * as DropdownMenu from '@radix-ui/react-dropdown-menu';

export function Header() {
  const { theme, setTheme } = useTheme();

  return (
    <header className="flex h-14 items-center justify-between border-b px-6">
      <div>
        {/* Breadcrumb or page title could go here */}
      </div>

      <div className="flex items-center gap-2">
        <DropdownMenu.Root>
          <DropdownMenu.Trigger asChild>
            <Button variant="ghost" size="icon">
              {theme === 'dark' ? (
                <Moon className="h-5 w-5" />
              ) : theme === 'light' ? (
                <Sun className="h-5 w-5" />
              ) : (
                <Monitor className="h-5 w-5" />
              )}
            </Button>
          </DropdownMenu.Trigger>
          <DropdownMenu.Portal>
            <DropdownMenu.Content
              className="min-w-[120px] rounded-md border bg-card p-1 shadow-md"
              sideOffset={5}
            >
              <DropdownMenu.Item
                className="cursor-pointer rounded-sm px-2 py-1.5 text-sm outline-none hover:bg-accent"
                onClick={() => setTheme('light')}
              >
                <Sun className="mr-2 inline h-4 w-4" />
                Light
              </DropdownMenu.Item>
              <DropdownMenu.Item
                className="cursor-pointer rounded-sm px-2 py-1.5 text-sm outline-none hover:bg-accent"
                onClick={() => setTheme('dark')}
              >
                <Moon className="mr-2 inline h-4 w-4" />
                Dark
              </DropdownMenu.Item>
              <DropdownMenu.Item
                className="cursor-pointer rounded-sm px-2 py-1.5 text-sm outline-none hover:bg-accent"
                onClick={() => setTheme('system')}
              >
                <Monitor className="mr-2 inline h-4 w-4" />
                System
              </DropdownMenu.Item>
            </DropdownMenu.Content>
          </DropdownMenu.Portal>
        </DropdownMenu.Root>
      </div>
    </header>
  );
}
