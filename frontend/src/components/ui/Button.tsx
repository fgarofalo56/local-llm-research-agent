import { forwardRef, type ButtonHTMLAttributes, type ReactNode } from 'react';
import { Loader2 } from 'lucide-react';
import { cn } from '@/lib/utils';

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'default' | 'secondary' | 'outline' | 'ghost' | 'destructive' | 'success';
  size?: 'sm' | 'md' | 'lg' | 'icon';
  isLoading?: boolean;
  loadingText?: string;
  leftIcon?: ReactNode;
  rightIcon?: ReactNode;
}

const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  (
    {
      className,
      variant = 'default',
      size = 'md',
      isLoading = false,
      loadingText,
      leftIcon,
      rightIcon,
      disabled,
      children,
      ...props
    },
    ref
  ) => {
    const isDisabled = disabled || isLoading;

    return (
      <button
        ref={ref}
        disabled={isDisabled}
        aria-disabled={isDisabled}
        aria-busy={isLoading}
        className={cn(
          // Base styles
          'inline-flex items-center justify-center gap-2 rounded-md font-medium',
          // Transitions for smooth interactions
          'transition-all duration-200 ease-out',
          'active:scale-[0.98]',
          // Focus styles (accessibility)
          'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-background',
          // Disabled states
          'disabled:pointer-events-none disabled:opacity-50',
          // Variant styles
          {
            // Default - primary action
            'bg-primary text-primary-foreground hover:bg-primary/90 shadow-sm hover:shadow-md':
              variant === 'default',
            // Secondary
            'bg-secondary text-secondary-foreground hover:bg-secondary/80':
              variant === 'secondary',
            // Outline
            'border border-input bg-background hover:bg-accent hover:text-accent-foreground hover:border-accent':
              variant === 'outline',
            // Ghost
            'hover:bg-accent hover:text-accent-foreground':
              variant === 'ghost',
            // Destructive
            'bg-destructive text-destructive-foreground hover:bg-destructive/90 shadow-sm':
              variant === 'destructive',
            // Success
            'bg-green-600 text-white hover:bg-green-700 shadow-sm':
              variant === 'success',
          },
          // Size styles
          {
            'h-8 px-3 text-xs': size === 'sm',
            'h-10 px-4 text-sm': size === 'md',
            'h-12 px-6 text-base': size === 'lg',
            'h-10 w-10 p-0': size === 'icon',
          },
          className
        )}
        {...props}
      >
        {/* Loading spinner */}
        {isLoading && (
          <Loader2
            className={cn('animate-spin', {
              'h-3 w-3': size === 'sm',
              'h-4 w-4': size === 'md' || size === 'icon',
              'h-5 w-5': size === 'lg',
            })}
            aria-hidden="true"
          />
        )}

        {/* Left icon (hidden when loading) */}
        {!isLoading && leftIcon && (
          <span className="shrink-0" aria-hidden="true">
            {leftIcon}
          </span>
        )}

        {/* Button text */}
        {size !== 'icon' && (
          <span className={cn(isLoading && 'opacity-70')}>
            {isLoading && loadingText ? loadingText : children}
          </span>
        )}

        {/* Right icon */}
        {!isLoading && rightIcon && (
          <span className="shrink-0" aria-hidden="true">
            {rightIcon}
          </span>
        )}

        {/* Screen reader text for icon buttons */}
        {size === 'icon' && !isLoading && (
          <span className="sr-only">{children}</span>
        )}
      </button>
    );
  }
);
Button.displayName = 'Button';

export { Button };
export type { ButtonProps };
