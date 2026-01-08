import { saveAs } from 'file-saver';
import jsPDF from 'jspdf';
import type { Conversation, Message } from '@/types';

export function exportChatToMarkdown(
  conversation: Conversation,
  messages: Message[]
): void {
  const lines: string[] = [];

  // Title
  lines.push(`# ${conversation.title || `Conversation ${conversation.id}`}`);
  lines.push('');
  lines.push(`*Exported: ${new Date().toLocaleString()}*`);
  lines.push('');
  lines.push('---');
  lines.push('');

  // Messages
  messages.forEach((msg) => {
    const role = msg.role === 'user' ? '**You**' : '**Assistant**';
    const timestamp = new Date(msg.created_at).toLocaleString();

    lines.push(`### ${role}`);
    lines.push(`*${timestamp}*`);
    lines.push('');
    lines.push(msg.content);
    lines.push('');

    // Include tool calls if present
    if (msg.tool_calls) {
      try {
        const tools = JSON.parse(msg.tool_calls);
        if (tools.length > 0) {
          lines.push('> **Tools used:**');
          tools.forEach((tool: { name: string }) => {
            lines.push(`> - ${tool.name}`);
          });
          lines.push('');
        }
      } catch {
        // Ignore parse errors
      }
    }

    lines.push('---');
    lines.push('');
  });

  const markdown = lines.join('\n');
  const blob = new Blob([markdown], { type: 'text/markdown;charset=utf-8' });
  saveAs(blob, `${conversation.title || 'conversation'}.md`);
}

export function exportChatToPdf(
  conversation: Conversation,
  messages: Message[]
): void {
  const pdf = new jsPDF({
    orientation: 'portrait',
    unit: 'mm',
    format: 'a4',
  });

  const pageWidth = pdf.internal.pageSize.getWidth();
  const pageHeight = pdf.internal.pageSize.getHeight();
  const margin = 15;
  const maxWidth = pageWidth - 2 * margin;
  let yOffset = margin;

  // Title
  pdf.setFontSize(18);
  pdf.setFont('helvetica', 'bold');
  pdf.text(
    conversation.title || `Conversation ${conversation.id}`,
    margin,
    yOffset
  );
  yOffset += 10;

  // Export date
  pdf.setFontSize(10);
  pdf.setFont('helvetica', 'italic');
  pdf.setTextColor(128);
  pdf.text(`Exported: ${new Date().toLocaleString()}`, margin, yOffset);
  yOffset += 10;
  pdf.setTextColor(0);

  // Separator
  pdf.setDrawColor(200);
  pdf.line(margin, yOffset, pageWidth - margin, yOffset);
  yOffset += 10;

  // Messages
  messages.forEach((msg) => {
    // Check if we need a new page
    if (yOffset > pageHeight - 30) {
      pdf.addPage();
      yOffset = margin;
    }

    // Role header
    pdf.setFontSize(11);
    pdf.setFont('helvetica', 'bold');
    const role = msg.role === 'user' ? 'You' : 'Assistant';
    pdf.text(role, margin, yOffset);

    // Timestamp
    pdf.setFont('helvetica', 'normal');
    pdf.setFontSize(8);
    pdf.setTextColor(128);
    const timestamp = new Date(msg.created_at).toLocaleString();
    pdf.text(timestamp, margin + 30, yOffset);
    pdf.setTextColor(0);
    yOffset += 6;

    // Content
    pdf.setFontSize(10);
    pdf.setFont('helvetica', 'normal');

    // Split content into lines that fit
    const lines = pdf.splitTextToSize(msg.content, maxWidth);
    lines.forEach((line: string) => {
      if (yOffset > pageHeight - 15) {
        pdf.addPage();
        yOffset = margin;
      }
      pdf.text(line, margin, yOffset);
      yOffset += 5;
    });

    yOffset += 5;

    // Separator
    pdf.setDrawColor(230);
    pdf.line(margin, yOffset, pageWidth - margin, yOffset);
    yOffset += 8;
  });

  pdf.save(`${conversation.title || 'conversation'}.pdf`);
}
