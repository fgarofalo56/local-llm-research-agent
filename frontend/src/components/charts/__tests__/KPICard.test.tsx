import { describe, it, expect } from 'vitest';
import { render, screen } from '@/test/test-utils';
import { KPICard } from '../KPICard';

describe('KPICard', () => {
  it('renders title and value', () => {
    render(<KPICard title="Total Users" value={1000} />);

    expect(screen.getByText('Total Users')).toBeInTheDocument();
    expect(screen.getByText('1,000')).toBeInTheDocument();
  });

  it('handles string values', () => {
    render(<KPICard title="Revenue" value="5000" />);

    expect(screen.getByText('5,000')).toBeInTheDocument();
  });

  it('formats currency correctly', () => {
    render(<KPICard title="Revenue" value={1500} format="currency" />);

    expect(screen.getByText('$1,500')).toBeInTheDocument();
  });

  it('formats percent correctly', () => {
    render(<KPICard title="Growth" value={25.5} format="percent" />);

    expect(screen.getByText('25.5%')).toBeInTheDocument();
  });

  it('adds prefix to value', () => {
    render(<KPICard title="Count" value={100} prefix="#" />);

    expect(screen.getByText(/#100/)).toBeInTheDocument();
  });

  it('adds suffix to value', () => {
    render(<KPICard title="Speed" value={60} suffix=" mph" />);

    expect(screen.getByText(/60 mph/)).toBeInTheDocument();
  });

  it('shows positive change indicator', () => {
    render(<KPICard title="Sales" value={1200} previousValue={1000} />);

    // 20% increase
    expect(screen.getByText(/20\.0%/)).toBeInTheDocument();
  });

  it('shows negative change indicator', () => {
    render(<KPICard title="Sales" value={800} previousValue={1000} />);

    // 20% decrease
    expect(screen.getByText(/20\.0%/)).toBeInTheDocument();
  });

  it('shows no change indicator when values are equal', () => {
    render(<KPICard title="Sales" value={1000} previousValue={1000} />);

    // 0% change
    expect(screen.getByText(/0\.0%/)).toBeInTheDocument();
  });

  it('handles no previous value', () => {
    render(<KPICard title="New Metric" value={500} />);

    // No percentage should be shown
    expect(screen.queryByText(/%/)).not.toBeInTheDocument();
  });

  it('handles NaN values gracefully', () => {
    render(<KPICard title="Invalid" value="not a number" />);

    expect(screen.getByText('not a number')).toBeInTheDocument();
  });

  it('formats large numbers correctly', () => {
    render(<KPICard title="Big Number" value={1234567890} />);

    expect(screen.getByText('1,234,567,890')).toBeInTheDocument();
  });

  it('formats currency with large values', () => {
    render(<KPICard title="Revenue" value={1500000} format="currency" />);

    expect(screen.getByText('$1,500,000')).toBeInTheDocument();
  });
});
