import { lazy, Suspense } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ThemeProvider } from '@/contexts/ThemeContext';
import { AuthProvider } from '@/contexts/AuthContext';
import { Layout } from '@/components/layout/Layout';
import { GlobalUploadProgress } from '@/components/upload';
import { LoadingPage } from '@/components/ui/LoadingPage';

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
    <QueryClientProvider client={queryClient}>
      <ThemeProvider>
        <AuthProvider>
          <BrowserRouter>
            <Suspense fallback={<LoadingPage />}>
              <Routes>
                {/* Public route - Login page without layout */}
                <Route path="/login" element={<LoginPage />} />

                {/* App routes with layout */}
                <Route
                  path="/*"
                  element={
                    <Layout>
                      <Routes>
                        <Route path="/" element={<Navigate to="/chat" replace />} />
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
                      </Routes>
                    </Layout>
                  }
                />
              </Routes>
            </Suspense>
            {/* Global upload progress - visible across all pages */}
            <GlobalUploadProgress />
          </BrowserRouter>
        </AuthProvider>
      </ThemeProvider>
    </QueryClientProvider>
  );
}

export default App;
