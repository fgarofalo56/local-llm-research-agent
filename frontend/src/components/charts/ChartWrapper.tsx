import type { ReactNode } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { MoreHorizontal, Pin, RefreshCw, Maximize2 } from 'lucide-react';
import * as DropdownMenu from '@radix-ui/react-dropdown-menu';

interface ChartWrapperProps {
  title: string;
  children: ReactNode;
  onPin?: () => void;
  onRefresh?: () => void;
  onExpand?: () => void;
  isRefreshing?: boolean;
}

export function ChartWrapper({
  title,
  children,
  onPin,
  onRefresh,
  onExpand,
  isRefreshing,
}: ChartWrapperProps) {
  return (
    <Card className="h-full">
      <CardHeader className="flex flex-row items-center justify-between pb-2">
        <CardTitle className="text-sm font-medium">{title}</CardTitle>
        <DropdownMenu.Root>
          <DropdownMenu.Trigger asChild>
            <Button variant="ghost" size="icon" className="h-8 w-8">
              <MoreHorizontal className="h-4 w-4" />
            </Button>
          </DropdownMenu.Trigger>
          <DropdownMenu.Portal>
            <DropdownMenu.Content
              className="min-w-[140px] rounded-md border bg-card p-1 shadow-md z-50"
              sideOffset={5}
            >
              {onPin && (
                <DropdownMenu.Item
                  className="flex cursor-pointer items-center rounded-sm px-2 py-1.5 text-sm outline-none hover:bg-accent"
                  onClick={onPin}
                >
                  <Pin className="mr-2 h-4 w-4" />
                  Pin to Dashboard
                </DropdownMenu.Item>
              )}
              {onRefresh && (
                <DropdownMenu.Item
                  className="flex cursor-pointer items-center rounded-sm px-2 py-1.5 text-sm outline-none hover:bg-accent"
                  onClick={onRefresh}
                >
                  <RefreshCw className={`mr-2 h-4 w-4 ${isRefreshing ? 'animate-spin' : ''}`} />
                  Refresh
                </DropdownMenu.Item>
              )}
              {onExpand && (
                <DropdownMenu.Item
                  className="flex cursor-pointer items-center rounded-sm px-2 py-1.5 text-sm outline-none hover:bg-accent"
                  onClick={onExpand}
                >
                  <Maximize2 className="mr-2 h-4 w-4" />
                  Expand
                </DropdownMenu.Item>
              )}
            </DropdownMenu.Content>
          </DropdownMenu.Portal>
        </DropdownMenu.Root>
      </CardHeader>
      <CardContent className="h-[calc(100%-4rem)]">
        {children}
      </CardContent>
    </Card>
  );
}
