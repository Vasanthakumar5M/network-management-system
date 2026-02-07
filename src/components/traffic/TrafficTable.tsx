/**
 * Traffic table component displaying HTTP/HTTPS traffic entries
 */

import { useMemo, useCallback } from 'react';
import type { TrafficEntry } from '@/types';
import { TrafficRow } from './TrafficRow';

export interface TrafficTableProps {
  entries: TrafficEntry[];
  selectedId: string | null;
  onSelect: (entry: TrafficEntry) => void;
  isLoading?: boolean;
  emptyMessage?: string;
}

export function TrafficTable({
  entries,
  selectedId,
  onSelect,
  isLoading = false,
  emptyMessage = 'No traffic data available',
}: TrafficTableProps) {
  // Table columns configuration
  const columns = useMemo(() => [
    { key: 'timestamp', label: 'Time', width: '100px' },
    { key: 'method', label: 'Method', width: '70px' },
    { key: 'status', label: 'Status', width: '60px' },
    { key: 'host', label: 'Host', width: '200px' },
    { key: 'path', label: 'Path', width: 'auto' },
    { key: 'size', label: 'Size', width: '80px' },
    { key: 'duration', label: 'Time', width: '70px' },
    { key: 'indicators', label: '', width: '60px' },
  ], []);

  // Format timestamp for display
  const formatTime = useCallback((timestamp: string) => {
    const date = new Date(timestamp);
    return date.toLocaleTimeString('en-US', {
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
      hour12: false,
    });
  }, []);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64 text-gray-500">
        <div className="flex flex-col items-center gap-2">
          <svg className="animate-spin h-8 w-8" viewBox="0 0 24 24">
            <circle
              className="opacity-25"
              cx="12"
              cy="12"
              r="10"
              stroke="currentColor"
              strokeWidth="4"
              fill="none"
            />
            <path
              className="opacity-75"
              fill="currentColor"
              d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
            />
          </svg>
          <span>Loading traffic data...</span>
        </div>
      </div>
    );
  }

  if (entries.length === 0) {
    return (
      <div className="flex items-center justify-center h-64 text-gray-500">
        <div className="flex flex-col items-center gap-2">
          <svg className="w-12 h-12 opacity-50" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={1.5}
              d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2"
            />
          </svg>
          <span>{emptyMessage}</span>
        </div>
      </div>
    );
  }

  return (
    <div className="relative overflow-hidden rounded-lg border border-gray-700/50">
      {/* Table header */}
      <div className="sticky top-0 z-10 bg-gray-800 border-b border-gray-700">
        <div className="flex items-center px-3 py-2 text-xs font-medium text-gray-400 uppercase tracking-wider">
          <div style={{ width: columns[0].width }}>{columns[0].label}</div>
          <div style={{ width: columns[1].width }} className="text-center">{columns[1].label}</div>
          <div style={{ width: columns[2].width }} className="text-center">{columns[2].label}</div>
          <div style={{ width: columns[3].width }}>{columns[3].label}</div>
          <div className="flex-1 min-w-0">{columns[4].label}</div>
          <div style={{ width: columns[5].width }} className="text-right">{columns[5].label}</div>
          <div style={{ width: columns[6].width }} className="text-right">{columns[6].label}</div>
          <div style={{ width: columns[7].width }}></div>
        </div>
      </div>

      {/* Table body - virtualized would be better for large lists */}
      <div className="overflow-y-auto max-h-[calc(100vh-280px)]">
        {entries.map((entry) => (
          <TrafficRow
            key={entry.id}
            entry={entry}
            isSelected={entry.id === selectedId}
            onSelect={() => onSelect(entry)}
            formatTime={formatTime}
          />
        ))}
      </div>
    </div>
  );
}
