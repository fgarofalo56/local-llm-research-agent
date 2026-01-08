import html2canvas from 'html2canvas';

export async function exportToPng(
  element: HTMLElement,
  filename: string = 'chart.png'
): Promise<void> {
  const canvas = await html2canvas(element, {
    backgroundColor: null,
    scale: 2, // Higher resolution
    logging: false,
    useCORS: true,
  });

  const link = document.createElement('a');
  link.download = filename;
  link.href = canvas.toDataURL('image/png');
  link.click();
}

export async function elementToDataUrl(element: HTMLElement): Promise<string> {
  const canvas = await html2canvas(element, {
    backgroundColor: null,
    scale: 2,
    logging: false,
    useCORS: true,
  });
  return canvas.toDataURL('image/png');
}
