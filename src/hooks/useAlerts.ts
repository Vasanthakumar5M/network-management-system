/**
 * Hook for managing alerts
 */

import { useCallback, useMemo } from 'react';
import { useAlertsStore } from '@/stores';
import { alerts } from '@/lib/api';
import type { Alert, AlertSeverity, AlertCategory } from '@/types';

export function useAlerts() {
  const {
    alerts: alertList,
    unreadCount,
    isLoading,
    setAlerts,
    addAlert,
    markAsRead,
    markAllAsRead,
    resolveAlert,
    deleteAlert,
  } = useAlertsStore();

  // Fetch all alerts
  const fetchAlerts = useCallback(async (unreadOnly = false) => {
    try {
      const data = await alerts.getAll(unreadOnly);
      setAlerts(data);
      return data;
    } catch (error) {
      console.error('Failed to fetch alerts:', error);
      throw error;
    }
  }, [setAlerts]);

  // Mark single alert as read
  const handleMarkAsRead = useCallback(async (alertId: string) => {
    try {
      await alerts.markAsRead(alertId);
      markAsRead(alertId);
    } catch (error) {
      console.error('Failed to mark alert as read:', error);
      throw error;
    }
  }, [markAsRead]);

  // Mark all alerts as read
  const handleMarkAllAsRead = useCallback(async () => {
    try {
      await alerts.markAllAsRead();
      markAllAsRead();
    } catch (error) {
      console.error('Failed to mark all alerts as read:', error);
      throw error;
    }
  }, [markAllAsRead]);

  // Resolve alert
  const handleResolve = useCallback(async (alertId: string) => {
    try {
      await alerts.resolve(alertId);
      resolveAlert(alertId);
    } catch (error) {
      console.error('Failed to resolve alert:', error);
      throw error;
    }
  }, [resolveAlert]);

  // Delete alert
  const handleDelete = useCallback(async (alertId: string) => {
    try {
      await alerts.delete(alertId);
      deleteAlert(alertId);
    } catch (error) {
      console.error('Failed to delete alert:', error);
      throw error;
    }
  }, [deleteAlert]);

  // Filter alerts by severity
  const alertsBySeverity = useMemo(() => {
    const grouped: Record<AlertSeverity, Alert[]> = {
      critical: [],
      high: [],
      medium: [],
      low: [],
    };

    alertList.forEach((alert) => {
      grouped[alert.severity].push(alert);
    });

    return grouped;
  }, [alertList]);

  // Filter alerts by category
  const alertsByCategory = useMemo(() => {
    const grouped: Partial<Record<AlertCategory, Alert[]>> = {};

    alertList.forEach((alert) => {
      if (!grouped[alert.category]) {
        grouped[alert.category] = [];
      }
      grouped[alert.category]!.push(alert);
    });

    return grouped;
  }, [alertList]);

  // Get unread alerts
  const unreadAlerts = useMemo(() => {
    return alertList.filter((a) => !a.isRead);
  }, [alertList]);

  // Get unresolved alerts
  const unresolvedAlerts = useMemo(() => {
    return alertList.filter((a) => !a.isResolved);
  }, [alertList]);

  // Get critical/high alerts (for urgent notifications)
  const urgentAlerts = useMemo(() => {
    return alertList.filter(
      (a) => (a.severity === 'critical' || a.severity === 'high') && !a.isResolved
    );
  }, [alertList]);

  // Alert stats
  const stats = useMemo(() => ({
    total: alertList.length,
    unread: unreadCount,
    unresolved: unresolvedAlerts.length,
    critical: alertsBySeverity.critical.length,
    high: alertsBySeverity.high.length,
    medium: alertsBySeverity.medium.length,
    low: alertsBySeverity.low.length,
  }), [alertList, unreadCount, unresolvedAlerts, alertsBySeverity]);

  return {
    alerts: alertList,
    unreadAlerts,
    unresolvedAlerts,
    urgentAlerts,
    alertsBySeverity,
    alertsByCategory,
    unreadCount,
    isLoading,
    stats,
    fetchAlerts,
    markAsRead: handleMarkAsRead,
    markAllAsRead: handleMarkAllAsRead,
    resolve: handleResolve,
    delete: handleDelete,
    addAlert,
  };
}
