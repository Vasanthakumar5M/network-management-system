/**
 * Device card component for device list display
 */

import { cn, formatBytes, formatRelativeTime } from '@/lib/utils';
import { StatusBadge } from '@/components/common/Badge';
import type { Device } from '@/types';

export interface DeviceCardProps {
  device: Device;
  isSelected?: boolean;
  onSelect: () => void;
  onToggleMonitoring?: (enabled: boolean) => void;
}

export function DeviceCard({
  device,
  isSelected = false,
  onSelect,
  onToggleMonitoring,
}: DeviceCardProps) {
  // Get device icon based on type
  const getDeviceIcon = () => {
    switch (device.deviceType) {
      case 'phone':
        return (
          <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 18h.01M8 21h8a2 2 0 002-2V5a2 2 0 00-2-2H8a2 2 0 00-2 2v14a2 2 0 002 2z" />
          </svg>
        );
      case 'laptop':
        return (
          <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
          </svg>
        );
      case 'desktop':
        return (
          <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
          </svg>
        );
      case 'tablet':
        return (
          <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 18h.01M7 21h10a2 2 0 002-2V5a2 2 0 00-2-2H7a2 2 0 00-2 2v14a2 2 0 002 2z" />
          </svg>
        );
      case 'tv':
        return (
          <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
          </svg>
        );
      default:
        return (
          <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M8.111 16.404a5.5 5.5 0 017.778 0M12 20h.01m-7.08-7.071c3.904-3.905 10.236-3.905 14.141 0M1.394 9.393c5.857-5.857 15.355-5.857 21.213 0" />
          </svg>
        );
    }
  };

  return (
    <div
      className={cn(
        'p-4 rounded-xl border cursor-pointer transition-all duration-200',
        'bg-gray-800/50 border-gray-700/50',
        'hover:bg-gray-800/70 hover:border-gray-600',
        isSelected && 'bg-blue-900/30 border-blue-500/50 ring-1 ring-blue-500/30'
      )}
      onClick={onSelect}
    >
      <div className="flex items-start gap-4">
        {/* Device icon */}
        <div className={cn(
          'p-3 rounded-lg',
          device.isOnline ? 'bg-green-900/20 text-green-400' : 'bg-gray-700/50 text-gray-500'
        )}>
          {getDeviceIcon()}
        </div>

        {/* Device info */}
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <h3 className="font-medium text-white truncate">{device.hostname || 'Unknown Device'}</h3>
            <StatusBadge status={device.isOnline ? 'online' : 'offline'} showDot />
          </div>
          
          <div className="text-sm text-gray-400 space-y-0.5">
            <p className="font-mono">{device.ip}</p>
            <p className="text-xs text-gray-500">{device.mac}</p>
          </div>

          {/* Vendor */}
          {device.vendor && (
            <p className="text-xs text-gray-500 mt-1 truncate">{device.vendor}</p>
          )}
        </div>

        {/* Monitoring toggle */}
        {onToggleMonitoring && (
          <button
            onClick={(e) => {
              e.stopPropagation();
              onToggleMonitoring(!device.isMonitored);
            }}
            className={cn(
              'p-2 rounded-lg transition-colors',
              device.isMonitored
                ? 'bg-blue-600 text-white hover:bg-blue-700'
                : 'bg-gray-700 text-gray-400 hover:bg-gray-600'
            )}
            title={device.isMonitored ? 'Stop monitoring' : 'Start monitoring'}
          >
            <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
              <path d="M10 12a2 2 0 100-4 2 2 0 000 4z" />
              <path fillRule="evenodd" d="M.458 10C1.732 5.943 5.522 3 10 3s8.268 2.943 9.542 7c-1.274 4.057-5.064 7-9.542 7S1.732 14.057.458 10zM14 10a4 4 0 11-8 0 4 4 0 018 0z" clipRule="evenodd" />
            </svg>
          </button>
        )}
      </div>

      {/* Stats row */}
      <div className="flex items-center gap-4 mt-3 pt-3 border-t border-gray-700/50 text-xs text-gray-500">
        <div className="flex items-center gap-1">
          <svg className="w-3.5 h-3.5" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M3 17a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm3.293-7.707a1 1 0 011.414 0L9 10.586V3a1 1 0 112 0v7.586l1.293-1.293a1 1 0 111.414 1.414l-3 3a1 1 0 01-1.414 0l-3-3a1 1 0 010-1.414z" clipRule="evenodd" />
          </svg>
          <span>{formatBytes(device.totalBytes)}</span>
        </div>

        {device.blockedRequests > 0 && (
          <div className="flex items-center gap-1 text-red-400">
            <svg className="w-3.5 h-3.5" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M13.477 14.89A6 6 0 015.11 6.524l8.367 8.368zm1.414-1.414L6.524 5.11a6 6 0 018.367 8.367zM18 10a8 8 0 11-16 0 8 8 0 0116 0z" clipRule="evenodd" />
            </svg>
            <span>{device.blockedRequests}</span>
          </div>
        )}

        {device.alerts > 0 && (
          <div className="flex items-center gap-1 text-yellow-400">
            <svg className="w-3.5 h-3.5" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
            </svg>
            <span>{device.alerts}</span>
          </div>
        )}

        <span className="ml-auto">
          Last seen: {formatRelativeTime(device.lastSeen)}
        </span>
      </div>
    </div>
  );
}
