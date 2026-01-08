import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@/test/test-utils';
import { ExportMenu } from '../ExportMenu';

// Mock all export dependencies
vi.mock('html2canvas', () => ({
  default: vi.fn().mockResolvedValue({
    toDataURL: () => 'data:image/png;base64,test',
    toBlob: (callback: (blob: Blob) => void) => callback(new Blob(['test'])),
  }),
}));

vi.mock('jspdf', () => ({
  default: vi.fn().mockImplementation(() => ({
    addImage: vi.fn(),
    save: vi.fn(),
    internal: {
      pageSize: { getWidth: () => 210, getHeight: () => 297 },
    },
  })),
}));

vi.mock('file-saver', () => ({
  saveAs: vi.fn(),
}));

vi.mock('exceljs', () => ({
  default: {
    Workbook: vi.fn().mockImplementation(() => ({
      addWorksheet: vi.fn().mockReturnValue({
        columns: [],
        addRow: vi.fn(),
        getRow: vi.fn().mockReturnValue({
          font: {},
          fill: {},
        }),
      }),
      xlsx: {
        writeBuffer: vi.fn().mockResolvedValue(new ArrayBuffer(8)),
      },
    })),
  },
}));

describe('ExportMenu', () => {
  const mockData = [
    { name: 'Item 1', value: 100 },
    { name: 'Item 2', value: 200 },
  ];

  const mockElementRef = {
    current: document.createElement('div'),
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders export button', () => {
    render(<ExportMenu data={mockData} elementRef={mockElementRef} filename="test" />);

    expect(screen.getByRole('button')).toBeInTheDocument();
  });

  it('button has dropdown trigger attributes', () => {
    render(<ExportMenu data={mockData} elementRef={mockElementRef} filename="test" />);

    const button = screen.getByRole('button');
    expect(button).toHaveAttribute('aria-haspopup', 'menu');
  });

  it('renders with custom filename', () => {
    render(<ExportMenu data={mockData} elementRef={mockElementRef} filename="my-report" />);

    expect(screen.getByRole('button')).toBeInTheDocument();
  });

  it('handles empty data', () => {
    render(<ExportMenu data={[]} elementRef={mockElementRef} filename="test" />);

    expect(screen.getByRole('button')).toBeInTheDocument();
  });

  it('handles null elementRef', () => {
    render(<ExportMenu data={mockData} elementRef={{ current: null }} filename="test" />);

    expect(screen.getByRole('button')).toBeInTheDocument();
  });
});
