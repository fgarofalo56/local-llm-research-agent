/**
 * Badge Component
 * Status indicators and labels
 */

import { forwardRef, type HTMLAttributes } from 'react';
import { cn } from '@/lib/utils';

interface BadgeProps extends HTMLAttributes<HTMLSpanElement> {
  variant?: 'default' | 'secondary' | 'success' | 'warning' | 'error' | 'info' | 'outline';
  size?: 'sm' | 'md' | 'lg';
  dot?: boolean;
  pulse?: boolean;
}

const Badge = forwardRef<HTMLSpanElement, BadgeProps>(
  ({ className, variant = 'default', size = 'md', dot = false, pulse = false, children, ...props }, ref) => {
    return (
      <span
        ref={ref}
        className={cn(
          'inline-flex items-center gap-1.5 font-medium rounded-full transition-colors',
          // Size variants
          {
            'px-2 py-0.5 text-xs': size === 'sm',
            'px-2.5 py-0.5 text-sm': size === 'md',
            'px-3 py-1 text-sm': size === 'lg',
          },
          // Color variants
          {
            'bg-primary text-primary-foreground': variant === 'default',
            'bg-secondary text-secondary-foreground': variant === 'secondary',
            'bg-green-500/15 text-green-700 dark:text-green-400 border border-green-500/20': variant === 'success',
            'bg-amber-500/15 text-amber-700 dark:text-amber-400 border border-amber-500/20': variant === 'warning',
            'bg-red-500/15 text-red-700 dark:text-red-400 border border-red-500/20': variant === 'error',
            'bg-blue-500/15 text-blue-700 dark:text-blue-400 border border-blue-500/20': variant === 'info',
            'border border-border bg-transparent text-foreground': variant === 'outline',
          },
          className
        )}
        {...props}
      >
        {dot && (
          <span
            className={cn(
              'h-1.5 w-1.5 rounded-full',
              {
                'bg-primary-foreground': variant === 'default',
                'bg-secondary-foreground': variant === 'secondary',
                'bg-green-500': variant === 'success',
                'bg-amber-500': variant === 'warning',
                'bg-red-500': variant === 'error',
                'bg-blue-500': variant === 'info',
                'bg-foreground': variant === 'outline',
              },
              pulse && 'animate-pulse'
            )}
          />
        )}
        {children}
      </span>
    );
  }
);
Badge.displayName = 'Badge';

// Status badge with dot indicator
interface StatusBadgeProps extends Omit<BadgeProps, 'dot' | 'variant'> {
  status: 'online' | 'offline' | 'busy' | 'away' | 'connecting';
}

const StatusBadge = forwardRef<HTMLSpanElement, StatusBadgeProps>(
  ({ status, className, ...props }, ref) => {
    const statusConfig = {
      online: { variant: 'success' as const, label: 'Online' },
      offline: { variant: 'secondary' as const, label: 'Offline' },
      busy: { variant: 'error' as const, label: 'Busy' },
      away: { variant: 'warning' as const, label: 'Away' },
      connecting: { variant: 'info' as const, label: 'Connecting' },
    };

    const config = statusConfig[status];

    return (
      <Badge
        ref={ref}
        variant={config.variant}
        dot
        pulse={status === 'connecting'}
        className={className}
        {...props}
      >
        {config.label}
      </Badge>
    );
  }
);
StatusBadge.displayName = 'StatusBadge';

// Count badge (for notifications, etc.)
interface CountBadgeProps extends Omit<BadgeProps, 'children'> {
  count: number;
  max?: number;
  showZero?: boolean;
}

const CountBadge = forwardRef<HTMLSpanElement, CountBadgeProps>(
  ({ count, max = 99, showZero = false, variant = 'default', className, ...props }, ref) => {
    if (count === 0 && !showZero) {
      return null;
    }

    const displayCount = count > max ? `${max}+` : count;

    return (
      <Badge
        ref={ref}
        variant={variant}
        size="sm"
        className={cn('min-w-[20px] justify-center', className)}
        {...props}
      >
        {displayCount}
      </Badge>
    );
  }
);
CountBadge.displayName = 'CountBadge';

export { Badge, StatusBadge, CountBadge };
