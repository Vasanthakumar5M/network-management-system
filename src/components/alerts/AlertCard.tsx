/**
 * Alert card component for displaying individual alerts
 */

import { cn, formatRelativeTime, getSeverityColor, getSeverityBg } from '@/lib/utils';
import { Badge } from '@/components/common/Badge';
import type { Alert, AlertSeverity, AlertCategory } from '@/types';

export interface AlertCardProps {
  alert: Alert;
  onMarkAsRead?: () => void;
  onResolve?: () => void;
  onDelete?: () => void;
  onClick?: () => void;
}

// Category labels
const categoryLabels: Record<AlertCategory, string> = {
  self_harm: 'Self Harm',
  suicide: 'Suicide',
  predator_grooming: 'Predator/Grooming',
  bullying: 'Bullying',
  drugs: 'Drugs',
  violence: 'Violence',
  adult_content: 'Adult Content',
  vpn_detected: 'VPN Detected',
  blocked_attempt: 'Block Bypass',
  new_device: 'New Device',
};

// Severity icons
const severityIcons: Record<AlertSeverity, React.ReactNode> = {
  critical: (
    <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
      <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
    </svg>
  ),
  high: (
    <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
      <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
    </svg>
  ),
  medium: (
    <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
      <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
    </svg>
  ),
  low: (
    <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
      <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
    </svg>
  ),
};

export function AlertCard({
  alert,
  onMarkAsRead,
  onResolve,
  onDelete,
  onClick,
}: AlertCardProps) {
  return (
    <div
      className={cn(
        'p-4 rounded-xl border transition-all duration-200',
        getSeverityBg(alert.severity),
        !alert.isRead && 'ring-1 ring-offset-1 ring-offset-gray-900',
        alert.severity === 'critical' && !alert.isRead && 'ring-red-500',
        alert.severity === 'high' && !alert.isRead && 'ring-orange-500',
        alert.severity === 'medium' && !alert.isRead && 'ring-yellow-500',
        alert.severity === 'low' && !alert.isRead && 'ring-blue-500',
        onClick && 'cursor-pointer hover:bg-opacity-20'
      )}
      onClick={onClick}
    >
      <div className="flex items-start gap-4">
        {/* Severity icon */}
        <div className={cn('flex-shrink-0 mt-0.5', getSeverityColor(alert.severity))}>
          {severityIcons[alert.severity]}
        </div>

        {/* Content */}
        <div className="flex-1 min-w-0">
          <div className="flex items-start justify-between gap-2">
            <div>
              <h3 className="font-medium text-white">{alert.title}</h3>
              <p className="text-sm text-gray-400 mt-0.5">{alert.description}</p>
            </div>
            <span className="text-xs text-gray-500 flex-shrink-0">
              {formatRelativeTime(alert.timestamp)}
            </span>
          </div>

          {/* URL if present */}
          {alert.url && (
            <p className="mt-2 text-xs text-gray-500 font-mono truncate" title={alert.url}>
              {alert.url}
            </p>
          )}

          {/* Matched keywords */}
          {alert.matchedKeywords && alert.matchedKeywords.length > 0 && (
            <div className="flex flex-wrap gap-1 mt-2">
              {alert.matchedKeywords.map((keyword, i) => (
                <Badge key={i} variant="danger" size="sm">
                  {keyword}
                </Badge>
              ))}
            </div>
          )}

          {/* Meta and actions */}
          <div className="flex items-center justify-between mt-3 pt-3 border-t border-gray-700/30">
            <div className="flex items-center gap-2">
              <Badge variant="outline" size="sm">
                {categoryLabels[alert.category] || alert.category}
              </Badge>
              {alert.isResolved && (
                <Badge variant="success" size="sm">
                  Resolved
                </Badge>
              )}
              {!alert.isRead && (
                <span className="w-2 h-2 rounded-full bg-blue-500" />
              )}
            </div>

            <div className="flex items-center gap-1">
              {!alert.isRead && onMarkAsRead && (
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    onMarkAsRead();
                  }}
                  className="p-1.5 text-gray-400 hover:text-white hover:bg-gray-700/50 rounded transition-colors"
                  title="Mark as read"
                >
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                  </svg>
                </button>
              )}
              {!alert.isResolved && onResolve && (
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    onResolve();
                  }}
                  className="p-1.5 text-gray-400 hover:text-green-400 hover:bg-green-900/20 rounded transition-colors"
                  title="Resolve"
                >
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                </button>
              )}
              {onDelete && (
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    onDelete();
                  }}
                  className="p-1.5 text-gray-400 hover:text-red-400 hover:bg-red-900/20 rounded transition-colors"
                  title="Delete"
                >
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                  </svg>
                </button>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
