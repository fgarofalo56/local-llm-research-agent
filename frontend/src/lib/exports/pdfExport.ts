import jsPDF from 'jspdf';
import html2canvas from 'html2canvas';

interface PdfExportOptions {
  title?: string;
  orientation?: 'portrait' | 'landscape';
  includeTimestamp?: boolean;
}

export async function exportToPdf(
  element: HTMLElement,
  filename: string = 'export.pdf',
  options: PdfExportOptions = {}
): Promise<void> {
  const {
    title,
    orientation = 'landscape',
    includeTimestamp = true,
  } = options;

  const canvas = await html2canvas(element, {
    backgroundColor: '#ffffff',
    scale: 2,
    logging: false,
    useCORS: true,
  });

  const imgData = canvas.toDataURL('image/png');
  const pdf = new jsPDF({
    orientation,
    unit: 'mm',
    format: 'a4',
  });

  const pageWidth = pdf.internal.pageSize.getWidth();
  const pageHeight = pdf.internal.pageSize.getHeight();
  const margin = 10;

  // Add title if provided
  let yOffset = margin;
  if (title) {
    pdf.setFontSize(16);
    pdf.text(title, margin, yOffset + 5);
    yOffset += 15;
  }

  // Add timestamp
  if (includeTimestamp) {
    pdf.setFontSize(10);
    pdf.setTextColor(128);
    pdf.text(
      `Generated: ${new Date().toLocaleString()}`,
      margin,
      yOffset + 3
    );
    yOffset += 10;
    pdf.setTextColor(0);
  }

  // Calculate image dimensions to fit page
  const imgWidth = pageWidth - 2 * margin;
  const imgHeight = (canvas.height * imgWidth) / canvas.width;

  // Add image (may span multiple pages)
  let remainingHeight = imgHeight;

  while (remainingHeight > 0) {
    const availableHeight = pageHeight - yOffset - margin;
    const drawHeight = Math.min(remainingHeight, availableHeight);

    pdf.addImage(
      imgData,
      'PNG',
      margin,
      yOffset,
      imgWidth,
      drawHeight,
      undefined,
      'FAST'
    );

    remainingHeight -= drawHeight;

    if (remainingHeight > 0) {
      pdf.addPage();
      yOffset = margin;
    }
  }

  pdf.save(filename);
}

export async function exportDashboardToPdf(
  dashboardElement: HTMLElement,
  dashboardName: string
): Promise<void> {
  await exportToPdf(dashboardElement, `${dashboardName}.pdf`, {
    title: dashboardName,
    orientation: 'landscape',
    includeTimestamp: true,
  });
}
