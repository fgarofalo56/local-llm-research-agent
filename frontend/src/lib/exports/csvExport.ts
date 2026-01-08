import { saveAs } from 'file-saver';

export function exportToCsv(
  data: Record<string, unknown>[],
  filename: string = 'data.csv'
): void {
  if (data.length === 0) return;

  const columns = Object.keys(data[0]);

  // Create header row
  const header = columns.map((col) => `"${col}"`).join(',');

  // Create data rows
  const rows = data.map((row) => {
    return columns
      .map((col) => {
        const value = row[col];
        if (value === null || value === undefined) return '';
        if (typeof value === 'string') {
          // Escape quotes and wrap in quotes
          return `"${value.replace(/"/g, '""')}"`;
        }
        return String(value);
      })
      .join(',');
  });

  const csv = [header, ...rows].join('\n');
  const blob = new Blob([csv], { type: 'text/csv;charset=utf-8' });
  saveAs(blob, filename);
}
