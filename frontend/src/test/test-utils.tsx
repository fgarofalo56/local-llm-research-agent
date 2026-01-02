import { render, type RenderOptions } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { BrowserRouter } from 'react-router-dom';
import { ThemeProvider } from '@/contexts/ThemeContext';
import type { ReactElement, ReactNode } from 'react';

// Create a fresh QueryClient for each test
function createTestQueryClient() {
  return new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
        gcTime: 0,
        staleTime: 0,
      },
      mutations: {
        retry: false,
      },
    },
  });
}

interface WrapperProps {
  children: ReactNode;
}

// Custom render function that wraps components with providers
function customRender(
  ui: ReactElement,
  options?: Omit<RenderOptions, 'wrapper'> & {
    queryClient?: QueryClient;
    withRouter?: boolean;
    withTheme?: boolean;
  }
) {
  const {
    queryClient = createTestQueryClient(),
    withRouter = true,
    withTheme = true,
    ...renderOptions
  } = options || {};

  function Wrapper({ children }: WrapperProps) {
    let content = (
      <QueryClientProvider client={queryClient}>
        {children}
      </QueryClientProvider>
    );

    if (withTheme) {
      content = <ThemeProvider>{content}</ThemeProvider>;
    }

    if (withRouter) {
      return <BrowserRouter>{content}</BrowserRouter>;
    }

    return content;
  }

  return {
    ...render(ui, { wrapper: Wrapper, ...renderOptions }),
    queryClient,
  };
}

// Re-export everything from testing-library
export * from '@testing-library/react';
export { customRender as render };
export { createTestQueryClient };
