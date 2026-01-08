import { useState } from 'react';
import * as DropdownMenu from '@radix-ui/react-dropdown-menu';
import {
  Download,
  Image,
  FileText,
  Table,
  FileSpreadsheet,
  FileType,
  Loader2,
} from 'lucide-react';
import { Button } from '@/components/ui/Button';
import { exportToPng } from '@/lib/exports/pngExport';
import { exportToPdf } from '@/lib/exports/pdfExport';
import { exportToCsv } from '@/lib/exports/csvExport';
import { exportToExcel } from '@/lib/exports/excelExport';

interface ExportMenuProps {
  elementRef?: React.RefObject<HTMLElement | null>;
  data?: Record<string, unknown>[];
  filename?: string;
  title?: string;
  onPowerBIExport?: () => void;
  showPowerBI?: boolean;
}

export function ExportMenu({
  elementRef,
  data,
  filename = 'export',
  title,
  onPowerBIExport,
  showPowerBI = false,
}: ExportMenuProps) {
  const [isExporting, setIsExporting] = useState(false);

  const handleExport = async (type: string) => {
    setIsExporting(true);
    try {
      switch (type) {
        case 'png':
          if (elementRef?.current) {
            await exportToPng(elementRef.current, `${filename}.png`);
          }
          break;
        case 'pdf':
          if (elementRef?.current) {
            await exportToPdf(elementRef.current, `${filename}.pdf`, { title });
          }
          break;
        case 'csv':
          if (data) {
            exportToCsv(data, `${filename}.csv`);
          }
          break;
        case 'excel':
          if (data) {
            await exportToExcel(data, `${filename}.xlsx`);
          }
          break;
        case 'powerbi':
          onPowerBIExport?.();
          break;
      }
    } finally {
      setIsExporting(false);
    }
  };

  return (
    <DropdownMenu.Root>
      <DropdownMenu.Trigger asChild>
        <Button variant="outline" size="sm" disabled={isExporting}>
          {isExporting ? (
            <Loader2 className="mr-2 h-4 w-4 animate-spin" />
          ) : (
            <Download className="mr-2 h-4 w-4" />
          )}
          Export
        </Button>
      </DropdownMenu.Trigger>
      <DropdownMenu.Portal>
        <DropdownMenu.Content
          className="min-w-[160px] rounded-md border bg-card p-1 shadow-md z-50"
          sideOffset={5}
        >
          {elementRef && (
            <>
              <DropdownMenu.Item
                className="flex cursor-pointer items-center rounded-sm px-2 py-1.5 text-sm outline-none hover:bg-accent"
                onClick={() => handleExport('png')}
              >
                <Image className="mr-2 h-4 w-4" />
                PNG Image
              </DropdownMenu.Item>
              <DropdownMenu.Item
                className="flex cursor-pointer items-center rounded-sm px-2 py-1.5 text-sm outline-none hover:bg-accent"
                onClick={() => handleExport('pdf')}
              >
                <FileText className="mr-2 h-4 w-4" />
                PDF Document
              </DropdownMenu.Item>
              <DropdownMenu.Separator className="my-1 h-px bg-border" />
            </>
          )}

          {data && (
            <>
              <DropdownMenu.Item
                className="flex cursor-pointer items-center rounded-sm px-2 py-1.5 text-sm outline-none hover:bg-accent"
                onClick={() => handleExport('csv')}
              >
                <Table className="mr-2 h-4 w-4" />
                CSV
              </DropdownMenu.Item>
              <DropdownMenu.Item
                className="flex cursor-pointer items-center rounded-sm px-2 py-1.5 text-sm outline-none hover:bg-accent"
                onClick={() => handleExport('excel')}
              >
                <FileSpreadsheet className="mr-2 h-4 w-4" />
                Excel
              </DropdownMenu.Item>
            </>
          )}

          {showPowerBI && (
            <>
              <DropdownMenu.Separator className="my-1 h-px bg-border" />
              <DropdownMenu.Item
                className="flex cursor-pointer items-center rounded-sm px-2 py-1.5 text-sm outline-none hover:bg-accent"
                onClick={() => handleExport('powerbi')}
              >
                <FileType className="mr-2 h-4 w-4" />
                Power BI (.pbix)
              </DropdownMenu.Item>
            </>
          )}
        </DropdownMenu.Content>
      </DropdownMenu.Portal>
    </DropdownMenu.Root>
  );
}
