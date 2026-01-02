/**
 * Toast Notification Component
 * Phase 2.5: Advanced Features & Polish
 *
 * Toast notifications using Radix Toast primitive with global state.
 */

import { createContext, useContext, useState, useCallback, type ReactNode } from 'react';
import * as ToastPrimitive from '@radix-ui/react-toast';
import { X, CheckCircle, AlertCircle, Info, AlertTriangle } from 'lucide-react';
import { cn } from '../../lib/utils';

export type ToastType = 'success' | 'error' | 'warning' | 'info';

export interface Toast {
  id: string;
  type: ToastType;
  title: string;
  description?: string;
  duration?: number;
}

interface ToastContextType {
  toasts: Toast[];
  addToast: (toast: Omit<Toast, 'id'>) => void;
  removeToast: (id: string) => void;
  success: (title: string, description?: string) => void;
  error: (title: string, description?: string) => void;
  warning: (title: string, description?: string) => void;
  info: (title: string, description?: string) => void;
}

const ToastContext = createContext<ToastContextType | undefined>(undefined);

export function ToastProvider({ children }: { children: ReactNode }) {
  const [toasts, setToasts] = useState<Toast[]>([]);

  // Define removeToast first since addToast depends on it
  const removeToast = useCallback((id: string) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  }, []);

  const addToast = useCallback((toast: Omit<Toast, 'id'>) => {
    const id = `toast-${Date.now()}-${Math.random().toString(36).slice(2)}`;
    setToasts((prev) => [...prev, { ...toast, id }]);

    // Auto-remove after duration
    const duration = toast.duration ?? 5000;
    if (duration > 0) {
      setTimeout(() => {
        removeToast(id);
      }, duration);
    }
  }, [removeToast]);

  const success = useCallback(
    (title: string, description?: string) => {
      addToast({ type: 'success', title, description });
    },
    [addToast]
  );

  const error = useCallback(
    (title: string, description?: string) => {
      addToast({ type: 'error', title, description, duration: 8000 });
    },
    [addToast]
  );

  const warning = useCallback(
    (title: string, description?: string) => {
      addToast({ type: 'warning', title, description, duration: 6000 });
    },
    [addToast]
  );

  const info = useCallback(
    (title: string, description?: string) => {
      addToast({ type: 'info', title, description });
    },
    [addToast]
  );

  return (
    <ToastContext.Provider value={{ toasts, addToast, removeToast, success, error, warning, info }}>
      <ToastPrimitive.Provider swipeDirection="right">
        {children}
        {toasts.map((toast) => (
          <ToastItem key={toast.id} toast={toast} onClose={() => removeToast(toast.id)} />
        ))}
        <ToastPrimitive.Viewport className="fixed bottom-0 right-0 flex flex-col p-6 gap-2 w-[400px] max-w-[100vw] m-0 list-none z-[100] outline-none" />
      </ToastPrimitive.Provider>
    </ToastContext.Provider>
  );
}

interface ToastItemProps {
  toast: Toast;
  onClose: () => void;
}

function ToastItem({ toast, onClose }: ToastItemProps) {
  const icons = {
    success: CheckCircle,
    error: AlertCircle,
    warning: AlertTriangle,
    info: Info,
  };

  const colors = {
    success: 'bg-green-500/10 border-green-500/20 text-green-500',
    error: 'bg-red-500/10 border-red-500/20 text-red-500',
    warning: 'bg-amber-500/10 border-amber-500/20 text-amber-500',
    info: 'bg-blue-500/10 border-blue-500/20 text-blue-500',
  };

  const Icon = icons[toast.type];

  return (
    <ToastPrimitive.Root
      className={cn(
        'bg-card border rounded-lg shadow-lg p-4 grid grid-cols-[auto_1fr_auto] gap-3 items-start',
        'data-[state=open]:animate-in data-[state=closed]:animate-out',
        'data-[swipe=end]:animate-out',
        'data-[state=closed]:fade-out-80 data-[state=closed]:slide-out-to-right-full',
        'data-[state=open]:slide-in-from-top-full data-[state=open]:sm:slide-in-from-bottom-full'
      )}
      duration={toast.duration ?? 5000}
    >
      <div className={cn('p-1 rounded', colors[toast.type])}>
        <Icon className="h-5 w-5" />
      </div>

      <div className="flex flex-col gap-1">
        <ToastPrimitive.Title className="font-semibold text-foreground">
          {toast.title}
        </ToastPrimitive.Title>
        {toast.description && (
          <ToastPrimitive.Description className="text-sm text-muted-foreground">
            {toast.description}
          </ToastPrimitive.Description>
        )}
      </div>

      <ToastPrimitive.Close
        className="rounded-md p-1 text-muted-foreground hover:text-foreground hover:bg-muted transition-colors"
        onClick={onClose}
      >
        <X className="h-4 w-4" />
      </ToastPrimitive.Close>
    </ToastPrimitive.Root>
  );
}

export function useToast() {
  const context = useContext(ToastContext);
  if (!context) {
    throw new Error('useToast must be used within ToastProvider');
  }
  return context;
}

export default ToastProvider;
