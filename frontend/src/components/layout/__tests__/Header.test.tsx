import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@/test/test-utils';
import { Header } from '../Header';

describe('Header', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders header element', () => {
    render(<Header />);
    expect(screen.getByRole('banner')).toBeInTheDocument();
  });

  it('shows theme toggle button', () => {
    render(<Header />);
    expect(screen.getByRole('button')).toBeInTheDocument();
  });

  it('has correct styling classes', () => {
    render(<Header />);
    const header = screen.getByRole('banner');
    expect(header).toHaveClass('flex', 'h-14', 'border-b');
  });

  it('button has dropdown trigger attributes', () => {
    render(<Header />);
    const button = screen.getByRole('button');
    expect(button).toHaveAttribute('aria-haspopup', 'menu');
    expect(button).toHaveAttribute('data-state', 'closed');
  });
});
