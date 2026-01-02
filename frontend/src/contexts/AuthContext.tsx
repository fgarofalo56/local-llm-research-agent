import { createContext, useContext, useEffect, useState, useCallback, type ReactNode } from 'react';
import { api } from '@/api/client';

// Types
interface User {
  id: number;
  email: string;
  username: string;
  display_name: string | null;
  is_active: boolean;
  is_admin: boolean;
  created_at: string;
}

interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
}

interface AuthContextType {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, username: string, password: string, displayName?: string) => Promise<void>;
  logout: () => Promise<void>;
  refreshToken: () => Promise<boolean>;
}

// Storage keys
const ACCESS_TOKEN_KEY = 'access_token';
const REFRESH_TOKEN_KEY = 'refresh_token';

// Helper functions
function getAccessToken(): string | null {
  return localStorage.getItem(ACCESS_TOKEN_KEY);
}

function getRefreshToken(): string | null {
  return localStorage.getItem(REFRESH_TOKEN_KEY);
}

function setTokens(accessToken: string, refreshToken: string): void {
  localStorage.setItem(ACCESS_TOKEN_KEY, accessToken);
  localStorage.setItem(REFRESH_TOKEN_KEY, refreshToken);
}

function clearTokens(): void {
  localStorage.removeItem(ACCESS_TOKEN_KEY);
  localStorage.removeItem(REFRESH_TOKEN_KEY);
}

// Create context
const AuthContext = createContext<AuthContextType | null>(null);

// Auth provider component
export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  // Fetch current user profile
  const fetchUser = useCallback(async () => {
    const token = getAccessToken();
    if (!token) {
      setIsLoading(false);
      return;
    }

    try {
      const userData = await api.get<User>('/auth/me', {
        headers: { Authorization: `Bearer ${token}` },
      });
      setUser(userData);
    } catch (error) {
      // Token might be expired, try to refresh
      const refreshed = await refreshTokenInternal();
      if (!refreshed) {
        clearTokens();
        setUser(null);
      }
    } finally {
      setIsLoading(false);
    }
  }, []);

  // Refresh token internally
  const refreshTokenInternal = async (): Promise<boolean> => {
    const refreshTokenValue = getRefreshToken();
    if (!refreshTokenValue) return false;

    try {
      const response = await api.post<TokenResponse>('/auth/refresh', {
        refresh_token: refreshTokenValue,
      });
      setTokens(response.access_token, response.refresh_token);
      await fetchUser();
      return true;
    } catch {
      clearTokens();
      setUser(null);
      return false;
    }
  };

  // Initialize auth state on mount
  useEffect(() => {
    fetchUser();
  }, [fetchUser]);

  // Login function
  const login = async (email: string, password: string): Promise<void> => {
    const response = await api.post<TokenResponse>('/auth/login', {
      email,
      password,
    });
    setTokens(response.access_token, response.refresh_token);
    await fetchUser();
  };

  // Register function
  const register = async (
    email: string,
    username: string,
    password: string,
    displayName?: string
  ): Promise<void> => {
    const response = await api.post<TokenResponse>('/auth/register', {
      email,
      username,
      password,
      display_name: displayName,
    });
    setTokens(response.access_token, response.refresh_token);
    await fetchUser();
  };

  // Logout function
  const logout = async (): Promise<void> => {
    const refreshTokenValue = getRefreshToken();
    const accessToken = getAccessToken();

    if (refreshTokenValue && accessToken) {
      try {
        await api.post('/auth/logout', { refresh_token: refreshTokenValue }, {
          headers: { Authorization: `Bearer ${accessToken}` },
        });
      } catch {
        // Ignore errors during logout
      }
    }

    clearTokens();
    setUser(null);
  };

  // Refresh token (public interface)
  const refreshToken = async (): Promise<boolean> => {
    return refreshTokenInternal();
  };

  const value: AuthContextType = {
    user,
    isAuthenticated: !!user,
    isLoading,
    login,
    register,
    logout,
    refreshToken,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

// Hook to use auth context
export function useAuth(): AuthContextType {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}

// Hook to get access token for API calls
export function useAccessToken(): string | null {
  return getAccessToken();
}

// Export utility functions for use in API client
export { getAccessToken, getRefreshToken, setTokens, clearTokens };
