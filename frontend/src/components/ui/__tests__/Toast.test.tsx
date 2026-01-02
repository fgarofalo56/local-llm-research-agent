import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, act } from '@/test/test-utils';
import { renderHook } from '@testing-library/react';
import { ToastProvider, useToast } from '../Toast';
import type { ReactNode } from 'react';

function wrapper({ children }: { children: ReactNode }) {
  return <ToastProvider>{children}</ToastProvider>;
}

describe('Toast', () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  describe('ToastProvider', () => {
    it('renders children', () => {
      render(
        <ToastProvider>
          <div data-testid="child">Hello</div>
        </ToastProvider>
      );

      expect(screen.getByTestId('child')).toBeInTheDocument();
    });
  });

  describe('useToast hook', () => {
    it('throws error when used outside provider', () => {
      const consoleError = vi.spyOn(console, 'error').mockImplementation(() => {});

      expect(() => {
        renderHook(() => useToast());
      }).toThrow('useToast must be used within ToastProvider');

      consoleError.mockRestore();
    });

    it('provides toast methods', () => {
      const { result } = renderHook(() => useToast(), { wrapper });

      expect(result.current.addToast).toBeDefined();
      expect(result.current.removeToast).toBeDefined();
      expect(result.current.success).toBeDefined();
      expect(result.current.error).toBeDefined();
      expect(result.current.warning).toBeDefined();
      expect(result.current.info).toBeDefined();
    });

    it('adds toast with success helper', () => {
      const { result } = renderHook(() => useToast(), { wrapper });

      act(() => {
        result.current.success('Success!', 'Operation completed');
      });

      expect(result.current.toasts).toHaveLength(1);
      expect(result.current.toasts[0].type).toBe('success');
      expect(result.current.toasts[0].title).toBe('Success!');
      expect(result.current.toasts[0].description).toBe('Operation completed');
    });

    it('adds toast with error helper', () => {
      const { result } = renderHook(() => useToast(), { wrapper });

      act(() => {
        result.current.error('Error!');
      });

      expect(result.current.toasts).toHaveLength(1);
      expect(result.current.toasts[0].type).toBe('error');
    });

    it('adds toast with warning helper', () => {
      const { result } = renderHook(() => useToast(), { wrapper });

      act(() => {
        result.current.warning('Warning!');
      });

      expect(result.current.toasts).toHaveLength(1);
      expect(result.current.toasts[0].type).toBe('warning');
    });

    it('adds toast with info helper', () => {
      const { result } = renderHook(() => useToast(), { wrapper });

      act(() => {
        result.current.info('Info!');
      });

      expect(result.current.toasts).toHaveLength(1);
      expect(result.current.toasts[0].type).toBe('info');
    });

    it('removes toast by id', () => {
      const { result } = renderHook(() => useToast(), { wrapper });

      act(() => {
        result.current.success('Toast 1');
        result.current.success('Toast 2');
      });

      expect(result.current.toasts).toHaveLength(2);

      const toastId = result.current.toasts[0].id;
      act(() => {
        result.current.removeToast(toastId);
      });

      expect(result.current.toasts).toHaveLength(1);
      expect(result.current.toasts[0].title).toBe('Toast 2');
    });

    it('auto-removes toast after duration', () => {
      const { result } = renderHook(() => useToast(), { wrapper });

      act(() => {
        result.current.addToast({
          type: 'success',
          title: 'Auto-remove',
          duration: 3000,
        });
      });

      expect(result.current.toasts).toHaveLength(1);

      // Fast-forward past duration
      act(() => {
        vi.advanceTimersByTime(3001);
      });

      expect(result.current.toasts).toHaveLength(0);
    });

    it('uses default duration when not specified', () => {
      const { result } = renderHook(() => useToast(), { wrapper });

      act(() => {
        result.current.success('Default duration');
      });

      expect(result.current.toasts).toHaveLength(1);

      // Default is 5000ms
      act(() => {
        vi.advanceTimersByTime(5001);
      });

      expect(result.current.toasts).toHaveLength(0);
    });

    it('does not auto-remove when duration is 0', () => {
      const { result } = renderHook(() => useToast(), { wrapper });

      act(() => {
        result.current.addToast({
          type: 'info',
          title: 'Persistent',
          duration: 0,
        });
      });

      expect(result.current.toasts).toHaveLength(1);

      // Fast-forward a long time
      act(() => {
        vi.advanceTimersByTime(60000);
      });

      // Should still be there
      expect(result.current.toasts).toHaveLength(1);
    });

    it('generates unique IDs for toasts', () => {
      const { result } = renderHook(() => useToast(), { wrapper });

      act(() => {
        result.current.success('Toast 1');
        result.current.success('Toast 2');
        result.current.success('Toast 3');
      });

      const ids = result.current.toasts.map((t) => t.id);
      const uniqueIds = new Set(ids);

      expect(uniqueIds.size).toBe(3);
    });
  });

  describe('Toast rendering', () => {
    it('renders toast with title', () => {
      render(
        <ToastProvider>
          <TestComponent />
        </ToastProvider>
      );

      const button = screen.getByRole('button', { name: 'Show Toast' });
      act(() => {
        button.click();
      });

      expect(screen.getByText('Test Toast')).toBeInTheDocument();
    });

    it('renders toast with description', () => {
      render(
        <ToastProvider>
          <TestComponentWithDescription />
        </ToastProvider>
      );

      const button = screen.getByRole('button', { name: 'Show Toast' });
      act(() => {
        button.click();
      });

      expect(screen.getByText('This is a description')).toBeInTheDocument();
    });
  });
});

// Helper components for rendering tests
function TestComponent() {
  const { success } = useToast();
  return (
    <button onClick={() => success('Test Toast')}>
      Show Toast
    </button>
  );
}

function TestComponentWithDescription() {
  const { info } = useToast();
  return (
    <button onClick={() => info('Info Toast', 'This is a description')}>
      Show Toast
    </button>
  );
}
