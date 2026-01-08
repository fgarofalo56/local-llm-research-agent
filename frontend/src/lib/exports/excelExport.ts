import ExcelJS from 'exceljs';
import { saveAs } from 'file-saver';

interface ExcelExportOptions {
  sheetName?: string;
  includeHeaders?: boolean;
  columnWidths?: number[];
}

export async function exportToExcel(
  data: Record<string, unknown>[],
  filename: string = 'data.xlsx',
  options: ExcelExportOptions = {}
): Promise<void> {
  const {
    sheetName = 'Data',
    includeHeaders = true,
    columnWidths,
  } = options;

  // Create workbook and worksheet
  const workbook = new ExcelJS.Workbook();
  const worksheet = workbook.addWorksheet(sheetName);

  if (data.length === 0) {
    // Empty data - just create empty sheet
    const buffer = await workbook.xlsx.writeBuffer();
    const blob = new Blob([buffer], {
      type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    });
    saveAs(blob, filename);
    return;
  }

  // Get column headers from first data item
  const columns = Object.keys(data[0]);

  // Set up columns with headers and widths
  worksheet.columns = columns.map((col, idx) => {
    let width = 15; // default width
    if (columnWidths && columnWidths[idx]) {
      width = columnWidths[idx];
    } else {
      // Auto-calculate width based on content
      const maxLength = Math.max(
        col.length,
        ...data.map((row) => String(row[col] || '').length)
      );
      width = Math.min(maxLength + 2, 50);
    }
    return {
      header: includeHeaders ? col : undefined,
      key: col,
      width,
    };
  });

  // Add data rows
  data.forEach((row) => {
    worksheet.addRow(row);
  });

  // Style header row if included
  if (includeHeaders) {
    const headerRow = worksheet.getRow(1);
    headerRow.font = { bold: true };
    headerRow.fill = {
      type: 'pattern',
      pattern: 'solid',
      fgColor: { argb: 'FFE0E0E0' },
    };
  }

  // Generate buffer and save
  const buffer = await workbook.xlsx.writeBuffer();
  const blob = new Blob([buffer], {
    type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
  });
  saveAs(blob, filename);
}

export async function exportMultipleSheetsToExcel(
  sheets: { name: string; data: Record<string, unknown>[] }[],
  filename: string = 'data.xlsx'
): Promise<void> {
  const workbook = new ExcelJS.Workbook();

  sheets.forEach(({ name, data }) => {
    // Sheet name max 31 chars
    const sheetName = name.slice(0, 31);
    const worksheet = workbook.addWorksheet(sheetName);

    if (data.length > 0) {
      const columns = Object.keys(data[0]);

      // Set up columns
      worksheet.columns = columns.map((col) => ({
        header: col,
        key: col,
        width: Math.min(
          Math.max(col.length, ...data.map((row) => String(row[col] || '').length)) + 2,
          50
        ),
      }));

      // Add data rows
      data.forEach((row) => {
        worksheet.addRow(row);
      });

      // Style header row
      const headerRow = worksheet.getRow(1);
      headerRow.font = { bold: true };
    }
  });

  const buffer = await workbook.xlsx.writeBuffer();
  const blob = new Blob([buffer], {
    type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
  });
  saveAs(blob, filename);
}
