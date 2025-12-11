import {
  ScatterChart,
  Scatter,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  ZAxis,
} from 'recharts';
import { useTheme } from '@/contexts/ThemeContext';

interface ScatterChartProps {
  data: Record<string, unknown>[];
  xKey: string;
  yKey: string;
  zKey?: string;
  name?: string;
  color?: string;
}

export function ScatterChartComponent({
  data,
  xKey,
  yKey,
  zKey,
  name = 'Data',
  color = 'hsl(221, 83%, 53%)'
}: ScatterChartProps) {
  const { resolvedTheme } = useTheme();
  const textColor = resolvedTheme === 'dark' ? '#a1a1aa' : '#52525b';
  const gridColor = resolvedTheme === 'dark' ? '#27272a' : '#e4e4e7';

  return (
    <ResponsiveContainer width="100%" height="100%">
      <ScatterChart margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
        <CartesianGrid strokeDasharray="3 3" stroke={gridColor} />
        <XAxis
          dataKey={xKey}
          type="number"
          name={xKey}
          tick={{ fill: textColor }}
        />
        <YAxis
          dataKey={yKey}
          type="number"
          name={yKey}
          tick={{ fill: textColor }}
        />
        {zKey && (
          <ZAxis
            dataKey={zKey}
            type="number"
            range={[50, 400]}
            name={zKey}
          />
        )}
        <Tooltip
          cursor={{ strokeDasharray: '3 3' }}
          contentStyle={{
            backgroundColor: resolvedTheme === 'dark' ? '#18181b' : '#ffffff',
            border: `1px solid ${gridColor}`,
            borderRadius: '8px',
          }}
        />
        <Legend />
        <Scatter name={name} data={data} fill={color} />
      </ScatterChart>
    </ResponsiveContainer>
  );
}
