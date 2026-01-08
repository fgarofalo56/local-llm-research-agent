import { useEffect, useState, useRef, type ReactNode } from 'react';
import { ArrowUp, ArrowDown, Minus, TrendingUp, TrendingDown, type LucideIcon } from 'lucide-react';
import { cn } from '@/lib/utils';

interface KPICardProps {
  title: string;
  value: string | number;
  previousValue?: number;
  format?: 'number' | 'currency' | 'percent';
  prefix?: string;
  suffix?: string;
  icon?: LucideIcon;
  description?: string;
  variant?: 'default' | 'compact' | 'detailed';
  trend?: 'up' | 'down' | 'neutral';
  loading?: boolean;
  animate?: boolean;
  sparklineData?: number[];
}

// Animated counter hook
function useAnimatedCounter(
  endValue: number,
  duration: number = 1000,
  enabled: boolean = true
) {
  const [count, setCount] = useState(0);
  const startTime = useRef<number | null>(null);
  const requestRef = useRef<number>();

  useEffect(() => {
    if (!enabled) {
      setCount(endValue);
      return;
    }

    startTime.current = null;

    const animate = (timestamp: number) => {
      if (!startTime.current) startTime.current = timestamp;
      const progress = Math.min((timestamp - startTime.current) / duration, 1);

      // Easing function for smooth animation
      const easeOutExpo = 1 - Math.pow(2, -10 * progress);
      setCount(Math.floor(easeOutExpo * endValue));

      if (progress < 1) {
        requestRef.current = requestAnimationFrame(animate);
      } else {
        setCount(endValue);
      }
    };

    requestRef.current = requestAnimationFrame(animate);

    return () => {
      if (requestRef.current) {
        cancelAnimationFrame(requestRef.current);
      }
    };
  }, [endValue, duration, enabled]);

  return count;
}

// Mini sparkline component
function MiniSparkline({ data, className }: { data: number[]; className?: string }) {
  if (!data || data.length < 2) return null;

  const min = Math.min(...data);
  const max = Math.max(...data);
  const range = max - min || 1;
  const width = 60;
  const height = 24;
  const padding = 2;

  const points = data
    .map((value, index) => {
      const x = padding + (index / (data.length - 1)) * (width - 2 * padding);
      const y = height - padding - ((value - min) / range) * (height - 2 * padding);
      return `${x},${y}`;
    })
    .join(' ');

  const isPositive = data[data.length - 1] >= data[0];

  return (
    <svg
      width={width}
      height={height}
      className={cn('overflow-visible', className)}
      aria-hidden="true"
    >
      <polyline
        fill="none"
        stroke={isPositive ? 'rgb(34, 197, 94)' : 'rgb(239, 68, 68)'}
        strokeWidth="1.5"
        strokeLinecap="round"
        strokeLinejoin="round"
        points={points}
      />
    </svg>
  );
}

// Skeleton loader for KPI
function KPICardSkeleton({ variant = 'default' }: { variant?: 'default' | 'compact' | 'detailed' }) {
  return (
    <div className={cn('flex flex-col justify-center animate-pulse', variant === 'compact' ? 'p-3' : 'p-4')}>
      <div className="h-4 w-20 bg-muted rounded mb-2" />
      <div className="h-8 w-32 bg-muted rounded mb-1" />
      {variant === 'detailed' && <div className="h-3 w-24 bg-muted rounded mt-2" />}
    </div>
  );
}

export function KPICard({
  title,
  value,
  previousValue,
  format = 'number',
  prefix = '',
  suffix = '',
  icon: Icon,
  description,
  variant = 'default',
  trend,
  loading = false,
  animate = true,
  sparklineData,
}: KPICardProps) {
  const numValue = typeof value === 'string' ? parseFloat(value) : value;
  const animatedValue = useAnimatedCounter(numValue, 1000, animate && !loading);

  if (loading) {
    return <KPICardSkeleton variant={variant} />;
  }

  const formatValue = (val: number) => {
    if (isNaN(val)) return String(value);

    switch (format) {
      case 'currency':
        return new Intl.NumberFormat('en-US', {
          style: 'currency',
          currency: 'USD',
          minimumFractionDigits: 0,
          maximumFractionDigits: 0,
        }).format(val);
      case 'percent':
        return `${val.toFixed(1)}%`;
      default:
        return new Intl.NumberFormat('en-US').format(val);
    }
  };

  const change = previousValue ? ((numValue - previousValue) / previousValue) * 100 : null;
  const effectiveTrend = trend || (change === null ? 'neutral' : change > 0 ? 'up' : change < 0 ? 'down' : 'neutral');

  const TrendIcon = effectiveTrend === 'up'
    ? TrendingUp
    : effectiveTrend === 'down'
      ? TrendingDown
      : Minus;

  const trendColor = effectiveTrend === 'up'
    ? 'text-green-500'
    : effectiveTrend === 'down'
      ? 'text-red-500'
      : 'text-muted-foreground';

  const trendBgColor = effectiveTrend === 'up'
    ? 'bg-green-500/10'
    : effectiveTrend === 'down'
      ? 'bg-red-500/10'
      : 'bg-muted';

  // Compact variant
  if (variant === 'compact') {
    return (
      <div className="flex items-center justify-between p-3">
        <div className="flex items-center gap-2">
          {Icon && (
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary/10 text-primary">
              <Icon className="h-4 w-4" />
            </div>
          )}
          <div>
            <p className="text-xs font-medium text-muted-foreground">{title}</p>
            <p className="text-lg font-bold animate-count-up">
              {prefix}
              {formatValue(animate ? animatedValue : numValue)}
              {suffix}
            </p>
          </div>
        </div>
        {change !== null && (
          <span className={cn('flex items-center gap-0.5 text-xs font-medium rounded-full px-2 py-0.5', trendColor, trendBgColor)}>
            <TrendIcon className="h-3 w-3" />
            {Math.abs(change).toFixed(1)}%
          </span>
        )}
      </div>
    );
  }

  // Detailed variant
  if (variant === 'detailed') {
    return (
      <div className="flex flex-col p-4">
        <div className="flex items-start justify-between mb-3">
          <div className="flex items-center gap-2">
            {Icon && (
              <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-primary/10 text-primary">
                <Icon className="h-5 w-5" />
              </div>
            )}
            <div>
              <p className="text-sm font-medium text-muted-foreground">{title}</p>
              {description && <p className="text-xs text-muted-foreground/70">{description}</p>}
            </div>
          </div>
          {sparklineData && <MiniSparkline data={sparklineData} />}
        </div>
        <div className="flex items-end justify-between">
          <span className="text-3xl font-bold tracking-tight animate-count-up">
            {prefix}
            {formatValue(animate ? animatedValue : numValue)}
            {suffix}
          </span>
          {change !== null && (
            <div className={cn('flex items-center gap-1 text-sm font-medium rounded-full px-2.5 py-1', trendColor, trendBgColor)}>
              <TrendIcon className="h-4 w-4" />
              <span>{Math.abs(change).toFixed(1)}%</span>
            </div>
          )}
        </div>
        {previousValue !== undefined && (
          <p className="mt-2 text-xs text-muted-foreground">
            vs. previous: {formatValue(previousValue)}
          </p>
        )}
      </div>
    );
  }

  // Default variant
  return (
    <div className="flex h-full flex-col justify-center p-4">
      <div className="flex items-center gap-2 mb-2">
        {Icon && (
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary/10 text-primary">
            <Icon className="h-4 w-4" />
          </div>
        )}
        <p className="text-sm font-medium text-muted-foreground">{title}</p>
      </div>
      <div className="flex items-baseline gap-3">
        <span className="text-3xl font-bold tracking-tight animate-count-up">
          {prefix}
          {formatValue(animate ? animatedValue : numValue)}
          {suffix}
        </span>
        {change !== null && (
          <span className={cn('flex items-center gap-0.5 text-sm font-medium', trendColor)}>
            <TrendIcon className="h-4 w-4" />
            {Math.abs(change).toFixed(1)}%
          </span>
        )}
        {sparklineData && <MiniSparkline data={sparklineData} className="ml-auto" />}
      </div>
      {description && (
        <p className="mt-2 text-xs text-muted-foreground">{description}</p>
      )}
    </div>
  );
}
