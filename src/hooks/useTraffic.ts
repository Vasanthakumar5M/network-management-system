/**
 * Hook for managing traffic data and filtering
 */

import { useCallback, useMemo } from 'react';
import { useTrafficStore } from '@/stores';
import { traffic } from '@/lib/api';
import type { TrafficEntry } from '@/types';

export function useTraffic() {
  const {
    entries,
    selectedEntryId,
    filter,
    isLoading,
    setEntries,
    addEntry,
    selectEntry,
    setFilter,
    clearFilter,
  } = useTrafficStore();

  // Fetch traffic data
  const fetchTraffic = useCallback(async (params?: {
    limit?: number;
    offset?: number;
    deviceId?: string;
  }) => {
    try {
      const data = await traffic.get(params || {});
      setEntries(data);
      return data;
    } catch (error) {
      console.error('Failed to fetch traffic:', error);
      throw error;
    }
  }, [setEntries]);

  // Search traffic
  const searchTraffic = useCallback(async (query: string) => {
    try {
      const data = await traffic.search(query);
      setEntries(data);
      return data;
    } catch (error) {
      console.error('Failed to search traffic:', error);
      throw error;
    }
  }, [setEntries]);

  // Filter entries client-side
  const filteredEntries = useMemo(() => {
    return entries.filter((entry) => {
      // Search filter
      if (filter.search) {
        const searchLower = filter.search.toLowerCase();
        const matches =
          entry.url.toLowerCase().includes(searchLower) ||
          entry.host.toLowerCase().includes(searchLower) ||
          entry.path.toLowerCase().includes(searchLower);
        if (!matches) return false;
      }

      // Method filter
      if (filter.method && entry.method !== filter.method) {
        return false;
      }

      // Status code filter
      if (filter.statusCode) {
        const codeGroup = filter.statusCode;
        if (codeGroup === '2xx' && (entry.statusCode < 200 || entry.statusCode >= 300)) return false;
        if (codeGroup === '3xx' && (entry.statusCode < 300 || entry.statusCode >= 400)) return false;
        if (codeGroup === '4xx' && (entry.statusCode < 400 || entry.statusCode >= 500)) return false;
        if (codeGroup === '5xx' && entry.statusCode < 500) return false;
      }

      // Device filter
      if (filter.deviceId && entry.deviceId !== filter.deviceId) {
        return false;
      }

      // Blocked filter
      if (filter.isBlocked !== null && entry.isBlocked !== filter.isBlocked) {
        return false;
      }

      // Alert filter
      if (filter.hasAlert !== null && entry.hasAlert !== filter.hasAlert) {
        return false;
      }

      return true;
    });
  }, [entries, filter]);

  // Get selected entry
  const selectedEntry = useMemo(() => {
    if (!selectedEntryId) return null;
    return entries.find((e) => e.id === selectedEntryId) || null;
  }, [entries, selectedEntryId]);

  // Add new entry (for real-time updates)
  const handleNewEntry = useCallback((entry: TrafficEntry) => {
    addEntry(entry);
  }, [addEntry]);

  return {
    entries: filteredEntries,
    allEntries: entries,
    selectedEntry,
    isLoading,
    filter,
    fetchTraffic,
    searchTraffic,
    selectEntry,
    setFilter,
    clearFilter,
    addEntry: handleNewEntry,
  };
}
