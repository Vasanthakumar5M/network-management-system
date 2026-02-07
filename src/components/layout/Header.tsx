/**
 * Header component for the application
 */

import { cn } from '@/lib/utils';
import { Button } from '@/components/common/Button';

export interface HeaderProps {
  title: string;
  subtitle?: string;
  isMonitoring: boolean;
  unreadAlerts: number;
  onToggleMonitoring: () => void;
  onViewAlerts: () => void;
  className?: string;
}

export function Header({
  title,
  subtitle,
  isMonitoring,
  unreadAlerts,
  onToggleMonitoring,
  onViewAlerts,
  className,
}: HeaderProps) {
  return (
    <header className={cn('flex items-center justify-between px-6 py-4 border-b border-gray-800', className)}>
      {/* Title area */}
      <div>
        <h1 className="text-xl font-bold text-white">{title}</h1>
        {subtitle && <p className="text-sm text-gray-400">{subtitle}</p>}
      </div>

      {/* Actions */}
      <div className="flex items-center gap-3">
        {/* Alerts button */}
        <button
          onClick={onViewAlerts}
          className="relative p-2 text-gray-400 hover:text-white hover:bg-gray-800 rounded-lg transition-colors"
        >
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
          </svg>
          {unreadAlerts > 0 && (
            <span className="absolute -top-1 -right-1 w-5 h-5 flex items-center justify-center text-xs font-bold text-white bg-red-500 rounded-full">
              {unreadAlerts > 9 ? '9+' : unreadAlerts}
            </span>
          )}
        </button>

        {/* Monitoring toggle button */}
        <Button
          variant={isMonitoring ? 'danger' : 'primary'}
          onClick={onToggleMonitoring}
          leftIcon={
            isMonitoring ? (
              <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8 7a1 1 0 00-1 1v4a1 1 0 001 1h4a1 1 0 001-1V8a1 1 0 00-1-1H8z" clipRule="evenodd" />
              </svg>
            ) : (
              <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM9.555 7.168A1 1 0 008 8v4a1 1 0 001.555.832l3-2a1 1 0 000-1.664l-3-2z" clipRule="evenodd" />
              </svg>
            )
          }
        >
          {isMonitoring ? 'Stop Monitoring' : 'Start Monitoring'}
        </Button>
      </div>
    </header>
  );
}
