import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ThemeProvider } from '@/contexts/ThemeContext';
import { Layout } from '@/components/layout/Layout';
import { ChatPage } from '@/pages/ChatPage';
import { DashboardsPage } from '@/pages/DashboardsPage';
import { DocumentsPage } from '@/pages/DocumentsPage';
import { MCPServersPage } from '@/pages/MCPServersPage';
import { QueriesPage } from '@/pages/QueriesPage';
import { SettingsPage } from '@/pages/SettingsPage';
import { SupersetPage } from '@/pages/SupersetPage';

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
        <BrowserRouter>
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
            </Routes>
          </Layout>
        </BrowserRouter>
      </ThemeProvider>
    </QueryClientProvider>
  );
}

export default App;
