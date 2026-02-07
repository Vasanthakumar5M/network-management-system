/**
 * Hook for managing monitoring status and controls
 */

import { useCallback, useEffect, useRef } from 'react';
import { useMonitoringStore } from '@/stores';
import { monitoring } from '@/lib/api';

export function useMonitoring() {
  const {
    status,
    setStatus,
  } = useMonitoringStore();

  const uptimeInterval = useRef<ReturnType<typeof setInterval> | null>(null);

  // Fetch current status
  const fetchStatus = useCallback(async () => {
    try {
      const currentStatus = await monitoring.getStatus();
      setStatus(currentStatus);
      return currentStatus;
    } catch (error) {
      console.error('Failed to fetch monitoring status:', error);
      throw error;
    }
  }, [setStatus]);

  // Start monitoring
  const start = useCallback(async () => {
    try {
      await monitoring.start();
      const newStatus = await monitoring.getStatus();
      setStatus(newStatus);
      
      // Start uptime counter
      uptimeInterval.current = setInterval(() => {
        setStatus({ uptime: status.uptime + 1 });
      }, 1000);
    } catch (error) {
      console.error('Failed to start monitoring:', error);
      setStatus({
        errors: [...status.errors, error instanceof Error ? error.message : 'Unknown error'],
      });
      throw error;
    }
  }, [setStatus, status.errors, status.uptime]);

  // Stop monitoring
  const stop = useCallback(async () => {
    try {
      if (uptimeInterval.current) {
        clearInterval(uptimeInterval.current);
        uptimeInterval.current = null;
      }
      
      await monitoring.stop();
      setStatus({
        isRunning: false,
        arpSpoofing: false,
        httpsProxy: false,
        dnsCapture: false,
        uptime: 0,
      });
    } catch (error) {
      console.error('Failed to stop monitoring:', error);
      throw error;
    }
  }, [setStatus]);

  // Toggle monitoring
  const toggle = useCallback(async () => {
    if (status.isRunning) {
      await stop();
    } else {
      await start();
    }
  }, [status.isRunning, start, stop]);

  // Clean up interval on unmount
  useEffect(() => {
    return () => {
      if (uptimeInterval.current) {
        clearInterval(uptimeInterval.current);
      }
    };
  }, []);

  // Format uptime as HH:MM:SS
  const formatUptime = useCallback((seconds: number): string => {
    const hrs = Math.floor(seconds / 3600);
    const mins = Math.floor((seconds % 3600) / 60);
    const secs = seconds % 60;
    return [hrs, mins, secs]
      .map((v) => v.toString().padStart(2, '0'))
      .join(':');
  }, []);

  return {
    status,
    isRunning: status.isRunning,
    uptime: status.uptime,
    uptimeFormatted: formatUptime(status.uptime),
    errors: status.errors,
    fetchStatus,
    start,
    stop,
    toggle,
    setStatus,
  };
}
