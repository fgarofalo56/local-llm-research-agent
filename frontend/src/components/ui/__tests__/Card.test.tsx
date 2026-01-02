import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@/test/test-utils';
import { Card, CardHeader, CardTitle, CardContent } from '../Card';

describe('Card', () => {
  it('renders Card with children', () => {
    render(<Card>Card content</Card>);
    expect(screen.getByText('Card content')).toBeInTheDocument();
  });

  it('applies default styles to Card', () => {
    render(<Card data-testid="card">Content</Card>);
    const card = screen.getByTestId('card');
    expect(card).toHaveClass('rounded-lg', 'border', 'bg-card');
  });

  it('applies custom className to Card', () => {
    render(<Card className="custom-card" data-testid="card">Content</Card>);
    const card = screen.getByTestId('card');
    expect(card).toHaveClass('custom-card');
  });

  it('forwards ref to Card', () => {
    const ref = vi.fn();
    render(<Card ref={ref}>Content</Card>);
    expect(ref).toHaveBeenCalled();
  });
});

describe('CardHeader', () => {
  it('renders CardHeader with children', () => {
    render(<CardHeader>Header content</CardHeader>);
    expect(screen.getByText('Header content')).toBeInTheDocument();
  });

  it('applies default styles', () => {
    render(<CardHeader data-testid="header">Content</CardHeader>);
    const header = screen.getByTestId('header');
    expect(header).toHaveClass('flex', 'flex-col', 'p-6');
  });

  it('applies custom className', () => {
    render(<CardHeader className="custom-header" data-testid="header">Content</CardHeader>);
    expect(screen.getByTestId('header')).toHaveClass('custom-header');
  });
});

describe('CardTitle', () => {
  it('renders CardTitle with proper heading element', () => {
    render(<CardTitle>My Title</CardTitle>);
    const title = screen.getByText('My Title');
    expect(title).toBeInTheDocument();
    expect(title.tagName).toBe('H3');
  });

  it('applies typography styles', () => {
    render(<CardTitle data-testid="title">Title</CardTitle>);
    const title = screen.getByTestId('title');
    expect(title).toHaveClass('text-2xl', 'font-semibold');
  });

  it('applies custom className', () => {
    render(<CardTitle className="custom-title" data-testid="title">Title</CardTitle>);
    expect(screen.getByTestId('title')).toHaveClass('custom-title');
  });
});

describe('CardContent', () => {
  it('renders CardContent with children', () => {
    render(<CardContent>Main content</CardContent>);
    expect(screen.getByText('Main content')).toBeInTheDocument();
  });

  it('applies default padding', () => {
    render(<CardContent data-testid="content">Content</CardContent>);
    const content = screen.getByTestId('content');
    expect(content).toHaveClass('p-6', 'pt-0');
  });
});

describe('Card composition', () => {
  it('renders complete Card structure', () => {
    render(
      <Card data-testid="card">
        <CardHeader>
          <CardTitle>Test Card</CardTitle>
        </CardHeader>
        <CardContent>
          <p>Main content here</p>
        </CardContent>
      </Card>
    );

    expect(screen.getByTestId('card')).toBeInTheDocument();
    expect(screen.getByText('Test Card')).toBeInTheDocument();
    expect(screen.getByText('Main content here')).toBeInTheDocument();
  });
});
