/**
 * Individual traffic row component
 */

import { memo } from 'react';
import { cn, getMethodClass, getStatusCodeClass, formatBytes, formatDuration, truncateUrl } from '@/lib/utils';
import type { TrafficEntry } from '@/types';

export interface TrafficRowProps {
  entry: TrafficEntry;
  isSelected: boolean;
  onSelect: () => void;
  formatTime: (timestamp: string) => string;
}

export const TrafficRow = memo(function TrafficRow({
  entry,
  isSelected,
  onSelect,
  formatTime,
}: TrafficRowProps) {
  return (
    <div
      className={cn(
        'flex items-center px-3 py-2 text-sm cursor-pointer transition-colors',
        'border-b border-gray-800/50 hover:bg-gray-800/50',
        isSelected && 'bg-blue-900/30 border-l-2 border-l-blue-500',
        entry.isBlocked && 'bg-red-900/10',
        entry.hasAlert && 'bg-yellow-900/10'
      )}
      onClick={onSelect}
    >
      {/* Timestamp */}
      <div className="w-[100px] text-gray-400 font-mono text-xs">
        {formatTime(entry.timestamp)}
      </div>

      {/* Method */}
      <div className="w-[70px] text-center">
        <span className={cn('px-1.5 py-0.5 rounded text-xs font-medium', getMethodClass(entry.method))}>
          {entry.method}
        </span>
      </div>

      {/* Status */}
      <div className="w-[60px] text-center">
        <span className={cn('font-mono text-xs', getStatusCodeClass(entry.statusCode))}>
          {entry.statusCode}
        </span>
      </div>

      {/* Host */}
      <div className="w-[200px] truncate text-gray-300" title={entry.host}>
        {entry.host}
      </div>

      {/* Path */}
      <div className="flex-1 min-w-0 truncate text-gray-400 font-mono text-xs" title={entry.path}>
        {truncateUrl(entry.path, 60)}
      </div>

      {/* Size */}
      <div className="w-[80px] text-right text-gray-400 text-xs">
        {formatBytes(entry.requestSize + entry.responseSize)}
      </div>

      {/* Duration */}
      <div className="w-[70px] text-right text-gray-400 text-xs">
        {formatDuration(entry.duration)}
      </div>

      {/* Indicators */}
      <div className="w-[60px] flex items-center justify-end gap-1">
        {entry.isBlocked && (
          <span className="text-red-500" title="Blocked">
            <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
              <path
                fillRule="evenodd"
                d="M13.477 14.89A6 6 0 015.11 6.524l8.367 8.368zm1.414-1.414L6.524 5.11a6 6 0 018.367 8.367zM18 10a8 8 0 11-16 0 8 8 0 0116 0z"
                clipRule="evenodd"
              />
            </svg>
          </span>
        )}
        {entry.hasAlert && (
          <span className="text-yellow-500" title="Alert triggered">
            <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
              <path
                fillRule="evenodd"
                d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z"
                clipRule="evenodd"
              />
            </svg>
          </span>
        )}
        {entry.category && (
          <span
            className="text-gray-500"
            title={`Category: ${entry.category}`}
          >
            <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
              <path
                fillRule="evenodd"
                d="M17.707 9.293a1 1 0 010 1.414l-7 7a1 1 0 01-1.414 0l-7-7A.997.997 0 012 10V5a3 3 0 013-3h5c.256 0 .512.098.707.293l7 7zM5 6a1 1 0 100-2 1 1 0 000 2z"
                clipRule="evenodd"
              />
            </svg>
          </span>
        )}
      </div>
    </div>
  );
});
