import { lazy, Suspense, Component, type ReactNode } from 'react';
import { BrowserRouter, Routes, Route, Navigate, Outlet } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ThemeProvider } from '@/contexts/ThemeContext';
import { AuthProvider } from '@/contexts/AuthContext';
import { ToastProvider, useToast } from '@/components/ui/Toast';
import { GlobalUploadProgress } from '@/components/upload';
import { LoadingPage } from '@/components/ui/LoadingPage';
import { useDocuments } from '@/hooks/useDocuments';
import { useAlertNotifications } from '@/hooks/useAlertNotifications';
import { Sidebar } from '@/components/layout/Sidebar';
import { Header } from '@/components/layout/Header';

// Error Boundary to catch and display React errors
interface ErrorBoundaryState {
  hasError: boolean;
  error: Error | null;
}

class ErrorBoundary extends Component<{ children: ReactNode }, ErrorBoundaryState> {
  constructor(props: { children: ReactNode }) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    console.error('React Error Boundary caught:', error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="flex h-screen items-center justify-center bg-red-50 p-8">
          <div className="max-w-xl rounded-lg border border-red-200 bg-white p-6 shadow-lg">
            <h1 className="mb-4 text-xl font-bold text-red-600">Something went wrong</h1>
            <pre className="mb-4 overflow-auto rounded bg-red-100 p-4 text-sm text-red-800">
              {this.state.error?.message}
            </pre>
            <pre className="overflow-auto rounded bg-gray-100 p-4 text-xs text-gray-600">
              {this.state.error?.stack}
            </pre>
            <button
              onClick={() => window.location.reload()}
              className="mt-4 rounded bg-red-600 px-4 py-2 text-white hover:bg-red-700"
            >
              Reload Page
            </button>
          </div>
        </div>
      );
    }
    return this.props.children;
  }
}

// Component to enable global document polling for upload status sync
function DocumentPollingProvider() {
  // This hook polls for documents when there are processing uploads
  // and syncs the upload status with document processing status
  useDocuments();
  return null;
}

// New component to handle global alert notifications
function GlobalNotificationHandler() {
  const { warning } = useToast();

  useAlertNotifications({
    onAlert: (alert) => {
      warning(`Alert: ${alert.name}`, alert.message);
    },
    showBrowserNotification: true, // Also trigger native browser notifications
  });

  return null; // This component does not render anything
}


// Layout component using Outlet for nested routes
function AppLayout() {
  return (
    <div className="flex h-screen bg-background">
      <Sidebar />
      <div className="flex flex-1 flex-col overflow-hidden">
        <Header />
        <main className="flex-1 overflow-auto p-6">
          <Outlet />
        </main>
      </div>
    </div>
  );
}

// Lazy load page components for code splitting
const ChatPage = lazy(() => import('@/pages/ChatPage').then(m => ({ default: m.ChatPage })));
const DashboardsPage = lazy(() => import('@/pages/DashboardsPage').then(m => ({ default: m.DashboardsPage })));
const DocumentsPage = lazy(() => import('@/pages/DocumentsPage').then(m => ({ default: m.DocumentsPage })));
const MCPServersPage = lazy(() => import('@/pages/MCPServersPage').then(m => ({ default: m.MCPServersPage })));
const QueriesPage = lazy(() => import('@/pages/QueriesPage').then(m => ({ default: m.QueriesPage })));
const SettingsPage = lazy(() => import('@/pages/SettingsPage').then(m => ({ default: m.SettingsPage })));
const SupersetPage = lazy(() => import('@/pages/SupersetPage').then(m => ({ default: m.SupersetPage })));
const DatabaseSettingsPage = lazy(() => import('@/pages/DatabaseSettingsPage').then(m => ({ default: m.DatabaseSettingsPage })));
const DatabaseConnectionsPage = lazy(() => import('@/pages/DatabaseConnectionsPage').then(m => ({ default: m.DatabaseConnectionsPage })));
const AnalyticsPage = lazy(() => import('@/pages/AnalyticsPage').then(m => ({ default: m.AnalyticsPage })));
const LoginPage = lazy(() => import('@/pages/LoginPage').then(m => ({ default: m.LoginPage })));

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 1000 * 60, // 1 minute
      retry: 1,
    },
  },
});

function App() {
  return (
    <ErrorBoundary>
      <QueryClientProvider client={queryClient}>
        <ThemeProvider>
          <AuthProvider>
            <ToastProvider>
              <BrowserRouter>
              <Suspense fallback={<LoadingPage />}>
                <Routes>
                  {/* Public route - Login page without layout */}
                  <Route path="/login" element={<LoginPage />} />

                  {/* App routes with layout */}
                  <Route element={<AppLayout />}>
                    <Route index element={<Navigate to="/chat" replace />} />
                    <Route path="/chat" element={<ChatPage />} />
                    <Route path="/chat/:conversationId" element={<ChatPage />} />
                    <Route path="/documents" element={<DocumentsPage />} />
                    <Route path="/dashboards" element={<DashboardsPage />} />
                    <Route path="/queries" element={<QueriesPage />} />
                    <Route path="/mcp-servers" element={<MCPServersPage />} />
                    <Route path="/superset" element={<SupersetPage />} />
                    <Route path="/settings" element={<SettingsPage />} />
                    <Route path="/settings/database" element={<DatabaseSettingsPage />} />
                    <Route path="/database-connections" element={<DatabaseConnectionsPage />} />
                    <Route path="/analytics" element={<AnalyticsPage />} />
                  </Route>
                </Routes>
              </Suspense>
              {/* Global components */}
              <GlobalNotificationHandler />
              <DocumentPollingProvider />
              <GlobalUploadProgress />
            </BrowserRouter>
          </ToastProvider>
        </AuthProvider>
      </ThemeProvider>
    </QueryClientProvider>
    </ErrorBoundary>
  );
}

export default App;