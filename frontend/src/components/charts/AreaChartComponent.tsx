import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';
import { useTheme } from '@/contexts/ThemeContext';

interface AreaChartProps {
  data: Record<string, unknown>[];
  xKey: string;
  yKeys: string[];
  colors?: string[];
  stacked?: boolean;
}

const defaultColors = [
  'hsl(221, 83%, 53%)', // primary blue
  'hsl(210, 70%, 50%)',
  'hsl(150, 70%, 50%)',
  'hsl(30, 70%, 50%)',
];

export function AreaChartComponent({
  data,
  xKey,
  yKeys,
  colors = defaultColors,
  stacked = false
}: AreaChartProps) {
  const { resolvedTheme } = useTheme();
  const textColor = resolvedTheme === 'dark' ? '#a1a1aa' : '#52525b';
  const gridColor = resolvedTheme === 'dark' ? '#27272a' : '#e4e4e7';

  return (
    <ResponsiveContainer width="100%" height="100%">
      <AreaChart data={data} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
        <CartesianGrid strokeDasharray="3 3" stroke={gridColor} />
        <XAxis dataKey={xKey} tick={{ fill: textColor }} />
        <YAxis tick={{ fill: textColor }} />
        <Tooltip
          contentStyle={{
            backgroundColor: resolvedTheme === 'dark' ? '#18181b' : '#ffffff',
            border: `1px solid ${gridColor}`,
            borderRadius: '8px',
          }}
        />
        <Legend />
        {yKeys.map((key, index) => (
          <Area
            key={key}
            type="monotone"
            dataKey={key}
            stroke={colors[index % colors.length]}
            fill={colors[index % colors.length]}
            fillOpacity={0.3}
            strokeWidth={2}
            stackId={stacked ? 'stack' : undefined}
          />
        ))}
      </AreaChart>
    </ResponsiveContainer>
  );
}
