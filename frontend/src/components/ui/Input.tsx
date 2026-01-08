import { forwardRef, type InputHTMLAttributes, type ReactNode } from 'react';
import { AlertCircle, Check } from 'lucide-react';
import { cn } from '@/lib/utils';

interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  error?: string;
  success?: boolean;
  hint?: string;
  leftIcon?: ReactNode;
  rightIcon?: ReactNode;
  label?: string;
}

const Input = forwardRef<HTMLInputElement, InputProps>(
  ({ className, type, error, success, hint, leftIcon, rightIcon, label, id, ...props }, ref) => {
    const inputId = id || (label ? `input-${label.toLowerCase().replace(/\s+/g, '-')}` : undefined);
    const hasError = Boolean(error);
    const hasSuccess = success && !hasError;

    const inputElement = (
      <div className="relative">
        {/* Left icon */}
        {leftIcon && (
          <div className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground">
            {leftIcon}
          </div>
        )}

        <input
          type={type}
          id={inputId}
          ref={ref}
          aria-invalid={hasError}
          aria-describedby={
            error ? `${inputId}-error` : hint ? `${inputId}-hint` : undefined
          }
          className={cn(
            // Base styles
            'flex h-10 w-full rounded-md border bg-background px-3 py-2',
            'text-sm ring-offset-background transition-all duration-200',
            // File input styles
            'file:border-0 file:bg-transparent file:text-sm file:font-medium',
            // Placeholder
            'placeholder:text-muted-foreground',
            // Focus styles
            'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-2',
            // Disabled styles
            'disabled:cursor-not-allowed disabled:opacity-50 disabled:bg-muted',
            // State styles
            {
              'border-input focus-visible:ring-ring': !hasError && !hasSuccess,
              'border-red-500 focus-visible:ring-red-500 pr-10': hasError,
              'border-green-500 focus-visible:ring-green-500 pr-10': hasSuccess,
              'pl-10': leftIcon,
              'pr-10': rightIcon && !hasError && !hasSuccess,
            },
            className
          )}
          {...props}
        />

        {/* Right icon or status icon */}
        {(rightIcon || hasError || hasSuccess) && (
          <div
            className={cn(
              'absolute right-3 top-1/2 -translate-y-1/2',
              hasError && 'text-red-500',
              hasSuccess && 'text-green-500',
              !hasError && !hasSuccess && 'text-muted-foreground'
            )}
          >
            {hasError ? (
              <AlertCircle className="h-4 w-4" aria-hidden="true" />
            ) : hasSuccess ? (
              <Check className="h-4 w-4" aria-hidden="true" />
            ) : (
              rightIcon
            )}
          </div>
        )}
      </div>
    );

    // If no label, hint, or error, just return the input
    if (!label && !hint && !error) {
      return inputElement;
    }

    // Return input with label and/or hint/error
    return (
      <div className="space-y-1.5">
        {label && (
          <label
            htmlFor={inputId}
            className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70"
          >
            {label}
          </label>
        )}
        {inputElement}
        {(error || hint) && (
          <p
            id={error ? `${inputId}-error` : `${inputId}-hint`}
            className={cn(
              'text-xs',
              error ? 'text-red-500' : 'text-muted-foreground'
            )}
          >
            {error || hint}
          </p>
        )}
      </div>
    );
  }
);
Input.displayName = 'Input';

// Textarea variant
interface TextareaProps extends React.TextareaHTMLAttributes<HTMLTextAreaElement> {
  error?: string;
  hint?: string;
  label?: string;
}

const Textarea = forwardRef<HTMLTextAreaElement, TextareaProps>(
  ({ className, error, hint, label, id, ...props }, ref) => {
    const inputId = id || (label ? `textarea-${label.toLowerCase().replace(/\s+/g, '-')}` : undefined);
    const hasError = Boolean(error);

    const textareaElement = (
      <textarea
        id={inputId}
        ref={ref}
        aria-invalid={hasError}
        aria-describedby={
          error ? `${inputId}-error` : hint ? `${inputId}-hint` : undefined
        }
        className={cn(
          // Base styles
          'flex min-h-[80px] w-full rounded-md border bg-background px-3 py-2',
          'text-sm ring-offset-background transition-all duration-200',
          'placeholder:text-muted-foreground resize-y',
          // Focus styles
          'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-2',
          // Disabled styles
          'disabled:cursor-not-allowed disabled:opacity-50 disabled:bg-muted',
          // State styles
          {
            'border-input focus-visible:ring-ring': !hasError,
            'border-red-500 focus-visible:ring-red-500': hasError,
          },
          className
        )}
        {...props}
      />
    );

    if (!label && !hint && !error) {
      return textareaElement;
    }

    return (
      <div className="space-y-1.5">
        {label && (
          <label
            htmlFor={inputId}
            className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70"
          >
            {label}
          </label>
        )}
        {textareaElement}
        {(error || hint) && (
          <p
            id={error ? `${inputId}-error` : `${inputId}-hint`}
            className={cn(
              'text-xs',
              error ? 'text-red-500' : 'text-muted-foreground'
            )}
          >
            {error || hint}
          </p>
        )}
      </div>
    );
  }
);
Textarea.displayName = 'Textarea';

export { Input, Textarea };
export type { InputProps, TextareaProps };
