# Chart Components

Data visualization components built on Recharts with automatic theme support and responsive design.

## Overview

All chart components are theme-aware and automatically adapt to light/dark mode. They use CSS variables for consistent theming and include responsive containers that fill available space.

---

## AreaChartComponent

Renders an area chart with support for multiple data series and optional stacking.

### Props

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `data` | `Record<string, unknown>[]` | Required | Array of data objects |
| `xKey` | `string` | Required | Key for X-axis values |
| `yKeys` | `string[]` | Required | Keys for Y-axis data series |
| `colors` | `string[]` | Default palette | Custom colors for each series |
| `stacked` | `boolean` | `false` | Stack areas on top of each other |

### Usage Example

```tsx
import { AreaChartComponent } from '@/components/charts/AreaChartComponent';

const data = [
  { month: 'Jan', revenue: 4000, expenses: 2400 },
  { month: 'Feb', revenue: 3000, expenses: 1398 },
  { month: 'Mar', revenue: 2000, expenses: 9800 },
];

<AreaChartComponent
  data={data}
  xKey="month"
  yKeys={['revenue', 'expenses']}
  stacked={true}
/>
```

### Notes
- **Accessibility**: ARIA labels automatically generated from data keys
- **Performance**: Uses Recharts memoization for efficient re-renders
- **Responsive**: Automatically fills parent container
- **Theme**: Grid color, text color, and tooltip styles adapt to theme

---

## BarChartComponent

Renders a vertical bar chart with support for grouped or stacked bars.

### Props

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `data` | `Record<string, unknown>[]` | Required | Array of data objects |
| `xKey` | `string` | Required | Key for X-axis categories |
| `yKeys` | `string[]` | Required | Keys for bar values |
| `colors` | `string[]` | Default palette | Custom colors for each bar series |

### Usage Example

```tsx
import { BarChartComponent } from '@/components/charts/BarChartComponent';

const data = [
  { department: 'Sales', q1: 4000, q2: 3000 },
  { department: 'Marketing', q1: 3000, q2: 2000 },
  { department: 'Engineering', q1: 2000, q2: 2780 },
];

<BarChartComponent
  data={data}
  xKey="department"
  yKeys={['q1', 'q2']}
  colors={['#3b82f6', '#10b981']}
/>
```

### Notes
- **Rounded Corners**: Bars have rounded top corners for modern appearance
- **Hover Effects**: Interactive tooltips on hover
- **Responsive Width**: Automatically adjusts to container

---

## LineChartComponent

Renders a line chart for time-series or continuous data.

### Props

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `data` | `Record<string, unknown>[]` | Required | Array of data objects |
| `xKey` | `string` | Required | Key for X-axis values |
| `yKeys` | `string[]` | Required | Keys for line series |
| `colors` | `string[]` | Default palette | Custom colors for each line |

### Usage Example

```tsx
import { LineChartComponent } from '@/components/charts/LineChartComponent';

const data = [
  { date: '2024-01', users: 120, sessions: 450 },
  { date: '2024-02', users: 150, sessions: 520 },
  { date: '2024-03', users: 180, sessions: 680 },
];

<LineChartComponent
  data={data}
  xKey="date"
  yKeys={['users', 'sessions']}
/>
```

### Notes
- **Smooth Lines**: Uses `monotone` curve type for smooth interpolation
- **Data Points**: Dots shown at each data point
- **Legend**: Automatically generated with color coding

---

## PieChartComponent

Renders a donut chart for proportional data visualization.

### Props

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `data` | `{ name: string; value: number }[]` | Required | Array of data with name/value pairs |
| `colors` | `string[]` | Default palette | Custom colors for each slice |

### Usage Example

```tsx
import { PieChartComponent } from '@/components/charts/PieChartComponent';

const data = [
  { name: 'Desktop', value: 400 },
  { name: 'Mobile', value: 300 },
  { name: 'Tablet', value: 200 },
];

<PieChartComponent data={data} />
```

### Notes
- **Donut Style**: Inner radius creates donut appearance
- **Padding**: 5-degree padding between slices
- **Centered**: Automatically centered in container
- **Tooltips**: Show percentage and value on hover

---

## ScatterChartComponent

Renders a scatter plot for correlation analysis and data distribution.

### Props

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `data` | `Record<string, unknown>[]` | Required | Array of data objects |
| `xKey` | `string` | Required | Key for X-axis values |
| `yKey` | `string` | Required | Key for Y-axis values |
| `zKey` | `string` | Optional | Key for bubble size (creates bubble chart) |
| `name` | `string` | `'Data'` | Series name for legend |
| `color` | `string` | Primary blue | Color for data points |

### Usage Example

```tsx
import { ScatterChartComponent } from '@/components/charts/ScatterChartComponent';

const data = [
  { age: 25, salary: 50000, experience: 2 },
  { age: 35, salary: 75000, experience: 10 },
  { age: 45, salary: 90000, experience: 20 },
];

// Basic scatter
<ScatterChartComponent
  data={data}
  xKey="age"
  yKey="salary"
  name="Employee Data"
/>

// Bubble chart with size dimension
<ScatterChartComponent
  data={data}
  xKey="age"
  yKey="salary"
  zKey="experience"
  name="Experience vs Salary"
/>
```

### Notes
- **Bubble Charts**: Add `zKey` prop to create bubble charts with varying sizes
- **Size Range**: Z-axis values mapped to 50-400px range
- **Correlation**: Useful for identifying trends and outliers

---

## KPICard

Displays a key performance indicator with optional trend comparison.

### Props

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `title` | `string` | Required | KPI label/title |
| `value` | `string \| number` | Required | Current KPI value |
| `previousValue` | `number` | Optional | Previous value for trend calculation |
| `format` | `'number' \| 'currency' \| 'percent'` | `'number'` | Value formatting type |
| `prefix` | `string` | `''` | Text before value (e.g., '$') |
| `suffix` | `string` | `''` | Text after value (e.g., ' users') |

### Usage Example

```tsx
import { KPICard } from '@/components/charts/KPICard';

// Simple KPI
<KPICard
  title="Total Users"
  value={1250}
  format="number"
/>

// KPI with trend
<KPICard
  title="Revenue"
  value={85000}
  previousValue={75000}
  format="currency"
/>

// Custom prefix/suffix
<KPICard
  title="CPU Usage"
  value={67}
  suffix="%"
  previousValue={72}
/>
```

### Trend Indicators

| Scenario | Icon | Color |
|----------|------|-------|
| Increase | Arrow Up | Green |
| Decrease | Arrow Down | Red |
| No change | Minus | Muted |
| No previous value | Minus | Muted |

### Notes
- **Auto Formatting**: Numbers formatted with thousands separators
- **Currency**: Uses Intl.NumberFormat for proper currency display
- **Percentage**: Calculated automatically when previousValue provided
- **Accessibility**: Semantic HTML with proper ARIA labels

---

## DataTable

Interactive data table with sorting and responsive design.

### Props

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `data` | `Record<string, unknown>[]` | Required | Array of data objects |
| `columns` | `string[]` | Optional | Column keys to display (defaults to all keys) |

### Usage Example

```tsx
import { DataTable } from '@/components/charts/DataTable';

const data = [
  { id: 1, name: 'Alice', age: 28, department: 'Engineering' },
  { id: 2, name: 'Bob', age: 35, department: 'Sales' },
  { id: 3, name: 'Carol', age: 42, department: 'Marketing' },
];

// All columns
<DataTable data={data} />

// Specific columns
<DataTable
  data={data}
  columns={['name', 'department', 'age']}
/>
```

### Features
- **Sortable**: Click column headers to sort ascending/descending
- **Formatted Values**: Numbers, dates, and nulls formatted appropriately
- **Sticky Header**: Header stays visible when scrolling
- **Hover States**: Row highlighting on hover
- **Responsive**: Horizontal scroll for wide tables

### Notes
- **Null Handling**: Empty cells for null/undefined values
- **Number Formatting**: Automatic thousands separators
- **Date Formatting**: Uses toLocaleDateString() for dates
- **Accessibility**: Proper table semantics and ARIA labels

---

## ChartWrapper

Container component that wraps charts with title, actions menu, and consistent styling.

### Props

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `title` | `string` | Required | Chart title |
| `children` | `ReactNode` | Required | Chart component to wrap |
| `onPin` | `() => void` | Optional | Callback for pin action |
| `onRefresh` | `() => void` | Optional | Callback for refresh action |
| `onExpand` | `() => void` | Optional | Callback for expand action |
| `isRefreshing` | `boolean` | `false` | Show refresh spinner |

### Usage Example

```tsx
import { ChartWrapper } from '@/components/charts/ChartWrapper';
import { BarChartComponent } from '@/components/charts/BarChartComponent';

<ChartWrapper
  title="Monthly Revenue"
  onPin={() => console.log('Pin to dashboard')}
  onRefresh={handleRefresh}
  isRefreshing={isLoading}
>
  <BarChartComponent data={data} xKey="month" yKeys={['revenue']} />
</ChartWrapper>
```

### Action Menu

The wrapper includes a three-dot menu with optional actions:
- **Pin to Dashboard**: If `onPin` provided
- **Refresh**: If `onRefresh` provided (shows spinner when `isRefreshing`)
- **Expand**: If `onExpand` provided

### Notes
- **Consistent Layout**: Standardized card with header and content area
- **Height Management**: Content area uses calc() for proper sizing
- **Responsive**: Adapts to container size

---

## ChartRenderer

Smart component that automatically renders the appropriate chart type based on data structure.

### Props

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `data` | `Record<string, unknown>[]` | Required | Data to visualize |
| `config` | `Partial<ChartConfig>` | Optional | Chart configuration override |
| `autoSuggest` | `boolean` | `true` | Auto-detect best chart type |

### ChartConfig Interface

```typescript
interface ChartConfig {
  type: 'bar' | 'line' | 'area' | 'pie' | 'scatter' | 'kpi' | 'table';
  xKey?: string;
  yKeys?: string[];
  title?: string;
  colors?: string[];
}
```

### Usage Example

```tsx
import { ChartRenderer } from '@/components/charts/ChartRenderer';

// Auto-detect chart type
<ChartRenderer data={data} />

// Specific chart type
<ChartRenderer
  data={data}
  config={{
    type: 'line',
    xKey: 'date',
    yKeys: ['revenue', 'profit'],
  }}
/>

// Disable auto-suggest
<ChartRenderer
  data={data}
  config={{ type: 'table' }}
  autoSuggest={false}
/>
```

### Auto-Suggestion Logic

The component analyzes data structure to suggest the best chart type:

1. **Single numeric value** → KPI Card
2. **Time-series data** → Line Chart
3. **Categorical data** → Bar Chart
4. **Part-to-whole** → Pie Chart
5. **Correlation** → Scatter Chart
6. **Fallback** → Data Table

### Notes
- **Flexible**: Works with any data structure
- **Smart Defaults**: Automatically detects X/Y keys
- **Override**: Config prop overrides auto-detection
- **Graceful Fallback**: Shows table if chart can't be rendered

---

## QueryResultPanel

Specialized component for displaying SQL query results with export and visualization options.

### Props

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `data` | `Record<string, unknown>[]` | Required | Query result data |
| `columns` | `string[]` | Optional | Column list |
| `executionTime` | `number` | Optional | Query execution time (ms) |
| `rowCount` | `number` | Optional | Total rows returned |

### Usage Example

```tsx
import { QueryResultPanel } from '@/components/charts/QueryResultPanel';

<QueryResultPanel
  data={queryResults}
  columns={['id', 'name', 'value']}
  executionTime={245}
  rowCount={150}
/>
```

### Features
- Automatic chart type selection
- Export to CSV, Excel, PNG, PDF
- Execution metrics display
- Pin to dashboard option
- Table/chart toggle

### Notes
- **Context Aware**: Shows relevant visualizations for SQL results
- **Performance**: Displays query execution time
- **Export Ready**: Multiple export formats available

---

## Color Palette

Default color palette used across all charts:

```typescript
const defaultColors = [
  'hsl(221, 83%, 53%)', // Primary blue
  'hsl(210, 70%, 50%)', // Blue
  'hsl(150, 70%, 50%)', // Green
  'hsl(30, 70%, 50%)',  // Orange
  'hsl(280, 70%, 50%)', // Purple
  'hsl(0, 70%, 50%)',   // Red
];
```

### Customizing Colors

Pass custom colors to any chart component:

```tsx
<BarChartComponent
  data={data}
  xKey="category"
  yKeys={['value1', 'value2']}
  colors={['#FF6384', '#36A2EB', '#FFCE56']}
/>
```

---

## Responsive Behavior

All chart components use `ResponsiveContainer` from Recharts:

```tsx
<ResponsiveContainer width="100%" height="100%">
  {/* Chart content */}
</ResponsiveContainer>
```

### Parent Sizing Requirements

Charts must have a parent with defined height:

```tsx
// Good
<div style={{ height: '400px' }}>
  <BarChartComponent data={data} xKey="x" yKeys={['y']} />
</div>

// Also good
<div className="h-96">
  <LineChartComponent data={data} xKey="x" yKeys={['y']} />
</div>

// Won't display (no height)
<div>
  <AreaChartComponent data={data} xKey="x" yKeys={['y']} />
</div>
```

---

## Accessibility

### ARIA Support
- All charts have descriptive ARIA labels
- Interactive elements (tooltips, legend items) are keyboard accessible
- Color is not the only way to distinguish data (shapes, labels used)

### Keyboard Navigation
- Tab through legend items
- Focus visible on interactive elements
- Tooltips accessible via keyboard

### Screen Readers
- Data tables preferred for screen reader users
- Provide summary descriptions for complex visualizations

---

## Performance Tips

1. **Memoize Data**: Prevent unnecessary re-renders
   ```tsx
   const chartData = useMemo(() => processData(rawData), [rawData]);
   ```

2. **Limit Data Points**: For large datasets, consider:
   - Pagination
   - Data aggregation
   - Virtual scrolling (for tables)

3. **Debounce Updates**: When data updates frequently
   ```tsx
   const debouncedData = useDebounce(data, 500);
   ```

4. **Use Keys Properly**: Ensure stable keys for list items
   ```tsx
   {data.map((item) => (
     <Bar key={item.id} dataKey={item.key} />
   ))}
   ```

---

## Related Documentation

- [Dashboard Components](./dashboard.md) - Using charts in dashboards
- [Export Components](./export.md) - Exporting chart visualizations
- [UI Components](./ui.md) - Card wrapper component
