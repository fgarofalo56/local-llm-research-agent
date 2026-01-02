/**
 * Alert Notifications Hook
 * Phase 2.5: Advanced Features & Polish
 *
 * WebSocket-based alert delivery to frontend with browser notifications.
 */

import { useEffect, useCallback, useRef, useState } from 'react';

export interface AlertNotification {
  alert_id: number;
  name: string;
  condition: string;
  threshold: number | null;
  current_value: number;
  triggered_at: string;
  message: string;
}

interface UseAlertNotificationsOptions {
  enabled?: boolean;
  onAlert?: (alert: AlertNotification) => void;
  showBrowserNotification?: boolean;
}

export function useAlertNotifications(options: UseAlertNotificationsOptions = {}) {
  const { enabled = true, onAlert, showBrowserNotification = true } = options;

  const [connected, setConnected] = useState(false);
  const [lastAlert, setLastAlert] = useState<AlertNotification | null>(null);
  const [notificationPermission, setNotificationPermission] = useState<NotificationPermission>(
    'Notification' in window ? Notification.permission : 'denied'
  );
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  // Request notification permission
  const requestNotificationPermission = useCallback(async () => {
    if (!('Notification' in window)) {
      console.warn('Browser does not support notifications');
      return false;
    }

    if (Notification.permission === 'granted') {
      setNotificationPermission('granted');
      return true;
    }

    if (Notification.permission !== 'denied') {
      const permission = await Notification.requestPermission();
      setNotificationPermission(permission);
      return permission === 'granted';
    }

    return false;
  }, []);

  // Show browser notification
  const showNotification = useCallback((alert: AlertNotification) => {
    if (notificationPermission !== 'granted') return;

    const notification = new Notification(`Alert: ${alert.name}`, {
      body: alert.message,
      icon: '/favicon.ico',
      tag: `alert-${alert.alert_id}`,
      requireInteraction: true,
    });

    notification.onclick = () => {
      window.focus();
      notification.close();
    };

    // Auto-close after 10 seconds
    setTimeout(() => notification.close(), 10000);
  }, [notificationPermission]);

  // Handle incoming alert
  const handleAlert = useCallback(
    (alert: AlertNotification) => {
      setLastAlert(alert);

      if (showBrowserNotification) {
        showNotification(alert);
      }

      onAlert?.(alert);
    },
    [onAlert, showBrowserNotification, showNotification]
  );

  // Use ref to store connect function to avoid circular dependency
  const connectRef = useRef<() => void>(() => {});

  // Connect to WebSocket - defined after connectRef but uses it for reconnection
  const connect = useCallback(() => {
    if (!enabled) return;

    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const host = window.location.host;
    const wsUrl = `${protocol}//${host}/ws/alerts`;

    try {
      const ws = new WebSocket(wsUrl);
      wsRef.current = ws;

      ws.onopen = () => {
        console.log('Alert WebSocket connected');
        setConnected(true);
      };

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          if (data.type === 'alert') {
            handleAlert(data.payload);
          }
        } catch (e) {
          console.error('Failed to parse alert message:', e);
        }
      };

      ws.onclose = (event) => {
        console.log('Alert WebSocket closed:', event.code, event.reason);
        setConnected(false);
        wsRef.current = null;

        // Reconnect after delay (unless intentionally closed)
        // Use connectRef to avoid accessing connect before declaration
        if (event.code !== 1000 && enabled) {
          reconnectTimeoutRef.current = setTimeout(() => {
            console.log('Reconnecting alert WebSocket...');
            connectRef.current();
          }, 5000);
        }
      };

      ws.onerror = (error) => {
        console.error('Alert WebSocket error:', error);
      };
    } catch (error) {
      console.error('Failed to create alert WebSocket:', error);
    }
  }, [enabled, handleAlert]);

  // Keep connectRef in sync with connect - must be in useEffect to avoid setting during render
  useEffect(() => {
    connectRef.current = connect;
  }, [connect]);

  // Disconnect from WebSocket
  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
    }

    if (wsRef.current) {
      wsRef.current.close(1000, 'Client disconnect');
      wsRef.current = null;
    }

    setConnected(false);
  }, []);

  // Connect on mount, disconnect on unmount
  useEffect(() => {
    if (enabled) {
      connect();
    }

    return () => {
      disconnect();
    };
  }, [enabled, connect, disconnect]);

  // Request notification permission on mount
  useEffect(() => {
    if (enabled && showBrowserNotification && notificationPermission === 'default') {
      requestNotificationPermission();
    }
  }, [enabled, showBrowserNotification, notificationPermission, requestNotificationPermission]);

  return {
    connected,
    lastAlert,
    notificationPermission,
    requestNotificationPermission,
    disconnect,
    reconnect: connect,
  };
}

export default useAlertNotifications;
