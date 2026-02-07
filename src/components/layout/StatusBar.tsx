/**
 * Status bar component showing monitoring status
 */

import { cn } from '@/lib/utils';
import type { MonitoringStatus } from '@/types';

export interface StatusBarProps {
  status: MonitoringStatus;
  className?: string;
}

export function StatusBar({ status, className }: StatusBarProps) {
  // Format uptime
  const formatUptime = (seconds: number): string => {
    const hrs = Math.floor(seconds / 3600);
    const mins = Math.floor((seconds % 3600) / 60);
    const secs = seconds % 60;
    return [hrs, mins, secs]
      .map((v) => v.toString().padStart(2, '0'))
      .join(':');
  };

  const services = [
    { key: 'arpSpoofing', label: 'ARP Spoof', active: status.arpSpoofing },
    { key: 'httpsProxy', label: 'HTTPS Proxy', active: status.httpsProxy },
    { key: 'dnsCapture', label: 'DNS Capture', active: status.dnsCapture },
    { key: 'stealthMode', label: 'Stealth', active: status.stealthMode },
  ];

  return (
    <footer
      className={cn(
        'flex items-center justify-between px-4 py-2 bg-gray-900 border-t border-gray-800 text-xs',
        className
      )}
    >
      {/* Left side - Status indicator */}
      <div className="flex items-center gap-4">
        <div className="flex items-center gap-2">
          <span
            className={cn(
              'w-2 h-2 rounded-full',
              status.isRunning ? 'bg-green-500 animate-pulse' : 'bg-gray-500'
            )}
          />
          <span className={cn(status.isRunning ? 'text-green-400' : 'text-gray-500')}>
            {status.isRunning ? 'Monitoring Active' : 'Monitoring Stopped'}
          </span>
        </div>

        {status.isRunning && (
          <>
            <span className="text-gray-600">|</span>
            <span className="text-gray-400">
              Uptime: <span className="font-mono">{formatUptime(status.uptime)}</span>
            </span>
          </>
        )}
      </div>

      {/* Center - Services status */}
      <div className="flex items-center gap-3">
        {services.map((service) => (
          <div key={service.key} className="flex items-center gap-1.5">
            <span
              className={cn(
                'w-1.5 h-1.5 rounded-full',
                service.active ? 'bg-green-500' : 'bg-gray-600'
              )}
            />
            <span className={cn(service.active ? 'text-gray-300' : 'text-gray-600')}>
              {service.label}
            </span>
          </div>
        ))}
      </div>

      {/* Right side - Profile and errors */}
      <div className="flex items-center gap-4">
        {status.stealthMode && (
          <span className="text-gray-400">
            Profile: <span className="text-blue-400">{status.currentProfile}</span>
          </span>
        )}

        {status.errors.length > 0 && (
          <div className="flex items-center gap-1 text-red-400">
            <svg className="w-3.5 h-3.5" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
            </svg>
            <span>{status.errors.length} error{status.errors.length > 1 ? 's' : ''}</span>
          </div>
        )}
      </div>
    </footer>
  );
}

// Compact version for sidebar footer
export interface StatusIndicatorProps {
  isRunning: boolean;
  uptime: number;
  onClick?: () => void;
}

export function StatusIndicator({ isRunning, uptime, onClick }: StatusIndicatorProps) {
  const formatUptime = (seconds: number): string => {
    const hrs = Math.floor(seconds / 3600);
    const mins = Math.floor((seconds % 3600) / 60);
    const secs = seconds % 60;
    return [hrs, mins, secs]
      .map((v) => v.toString().padStart(2, '0'))
      .join(':');
  };

  return (
    <button
      type="button"
      onClick={onClick}
      className={cn(
        'w-full flex items-center gap-3 px-3 py-2 rounded-lg transition-colors',
        isRunning
          ? 'bg-green-900/20 hover:bg-green-900/30'
          : 'bg-gray-800/50 hover:bg-gray-800'
      )}
    >
      <span
        className={cn(
          'w-3 h-3 rounded-full flex-shrink-0',
          isRunning ? 'bg-green-500 animate-pulse' : 'bg-gray-500'
        )}
      />
      <div className="flex-1 text-left">
        <p className={cn('text-sm font-medium', isRunning ? 'text-green-400' : 'text-gray-400')}>
          {isRunning ? 'Active' : 'Stopped'}
        </p>
        {isRunning && (
          <p className="text-xs text-gray-500 font-mono">{formatUptime(uptime)}</p>
        )}
      </div>
    </button>
  );
}
