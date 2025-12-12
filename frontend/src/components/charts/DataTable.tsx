import { useState } from 'react';
import { ChevronUp, ChevronDown } from 'lucide-react';

interface DataTableProps {
  data: Record<string, unknown>[];
  columns?: string[];
}

export function DataTable({ data, columns }: DataTableProps) {
  const [sortColumn, setSortColumn] = useState<string | null>(null);
  const [sortDirection, setSortDirection] = useState<'asc' | 'desc'>('asc');

  const cols = columns || (data.length > 0 ? Object.keys(data[0]) : []);

  const handleSort = (column: string) => {
    if (sortColumn === column) {
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc');
    } else {
      setSortColumn(column);
      setSortDirection('asc');
    }
  };

  const sortedData = [...data].sort((a, b) => {
    if (!sortColumn) return 0;
    const aVal = a[sortColumn];
    const bVal = b[sortColumn];

    if (aVal === bVal) return 0;
    if (aVal === null || aVal === undefined) return 1;
    if (bVal === null || bVal === undefined) return -1;

    const comparison = aVal < bVal ? -1 : 1;
    return sortDirection === 'asc' ? comparison : -comparison;
  });

  if (data.length === 0) {
    return (
      <div className="flex h-full items-center justify-center text-muted-foreground">
        No data available
      </div>
    );
  }

  return (
    <div className="h-full overflow-auto">
      <table className="w-full text-sm">
        <thead className="sticky top-0 bg-card">
          <tr className="border-b">
            {cols.map((col) => (
              <th
                key={col}
                className="cursor-pointer px-4 py-2 text-left font-medium hover:bg-accent"
                onClick={() => handleSort(col)}
              >
                <span className="flex items-center gap-1">
                  {col}
                  {sortColumn === col && (
                    sortDirection === 'asc'
                      ? <ChevronUp className="h-4 w-4" />
                      : <ChevronDown className="h-4 w-4" />
                  )}
                </span>
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {sortedData.map((row, index) => (
            <tr key={index} className="border-b hover:bg-muted/50">
              {cols.map((col) => (
                <td key={col} className="px-4 py-2">
                  {formatCellValue(row[col])}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function formatCellValue(value: unknown): string {
  if (value === null || value === undefined) return '';
  if (typeof value === 'number') {
    return new Intl.NumberFormat('en-US').format(value);
  }
  if (value instanceof Date) {
    return value.toLocaleDateString();
  }
  return String(value);
}
