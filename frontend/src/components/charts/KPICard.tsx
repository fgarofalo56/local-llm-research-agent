import { ArrowUp, ArrowDown, Minus } from 'lucide-react';
import { cn } from '@/lib/utils';

interface KPICardProps {
  title: string;
  value: string | number;
  previousValue?: number;
  format?: 'number' | 'currency' | 'percent';
  prefix?: string;
  suffix?: string;
}

export function KPICard({
  title,
  value,
  previousValue,
  format = 'number',
  prefix = '',
  suffix = '',
}: KPICardProps) {
  const numValue = typeof value === 'string' ? parseFloat(value) : value;

  const formatValue = (val: number) => {
    if (isNaN(val)) return String(value);

    switch (format) {
      case 'currency':
        return new Intl.NumberFormat('en-US', {
          style: 'currency',
          currency: 'USD',
          minimumFractionDigits: 0,
        }).format(val);
      case 'percent':
        return `${val.toFixed(1)}%`;
      default:
        return new Intl.NumberFormat('en-US').format(val);
    }
  };

  const change = previousValue ? ((numValue - previousValue) / previousValue) * 100 : null;

  const TrendIcon = change === null
    ? Minus
    : change > 0
      ? ArrowUp
      : change < 0
        ? ArrowDown
        : Minus;

  const trendColor = change === null
    ? 'text-muted-foreground'
    : change > 0
      ? 'text-green-500'
      : change < 0
        ? 'text-red-500'
        : 'text-muted-foreground';

  return (
    <div className="flex h-full flex-col justify-center p-4">
      <p className="text-sm font-medium text-muted-foreground">{title}</p>
      <div className="mt-2 flex items-baseline gap-2">
        <span className="text-3xl font-bold">
          {prefix}
          {formatValue(numValue)}
          {suffix}
        </span>
        {change !== null && (
          <span className={cn('flex items-center text-sm', trendColor)}>
            <TrendIcon className="mr-1 h-4 w-4" />
            {Math.abs(change).toFixed(1)}%
          </span>
        )}
      </div>
    </div>
  );
}
