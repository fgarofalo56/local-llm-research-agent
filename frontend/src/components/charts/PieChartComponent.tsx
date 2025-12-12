import { PieChart, Pie, Cell, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { useTheme } from '@/contexts/ThemeContext';

interface PieChartProps {
  data: { name: string; value: number }[];
  colors?: string[];
}

const defaultColors = [
  'hsl(221, 83%, 53%)', // primary blue
  'hsl(210, 70%, 50%)',
  'hsl(150, 70%, 50%)',
  'hsl(30, 70%, 50%)',
  'hsl(280, 70%, 50%)',
  'hsl(0, 70%, 50%)',
];

export function PieChartComponent({ data, colors = defaultColors }: PieChartProps) {
  const { resolvedTheme } = useTheme();
  const gridColor = resolvedTheme === 'dark' ? '#27272a' : '#e4e4e7';

  return (
    <ResponsiveContainer width="100%" height="100%">
      <PieChart>
        <Pie
          data={data}
          cx="50%"
          cy="50%"
          innerRadius={60}
          outerRadius={80}
          paddingAngle={5}
          dataKey="value"
        >
          {data.map((_, index) => (
            <Cell key={`cell-${index}`} fill={colors[index % colors.length]} />
          ))}
        </Pie>
        <Tooltip
          contentStyle={{
            backgroundColor: resolvedTheme === 'dark' ? '#18181b' : '#ffffff',
            border: `1px solid ${gridColor}`,
            borderRadius: '8px',
          }}
        />
        <Legend />
      </PieChart>
    </ResponsiveContainer>
  );
}
