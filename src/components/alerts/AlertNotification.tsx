/**
 * Alert notification component - popup notifications for new alerts
 */

import { useEffect, useState } from 'react';
import { createPortal } from 'react-dom';
import { cn, getSeverityColor } from '@/lib/utils';
import type { Alert } from '@/types';

export interface AlertNotificationProps {
  alert: Alert;
  onDismiss: () => void;
  onClick?: () => void;
  duration?: number;
}

export function AlertNotification({
  alert,
  onDismiss,
  onClick,
  duration = 10000,
}: AlertNotificationProps) {
  const [isVisible, setIsVisible] = useState(false);
  const [isLeaving, setIsLeaving] = useState(false);

  useEffect(() => {
    // Enter animation
    requestAnimationFrame(() => setIsVisible(true));

    // Auto dismiss
    const timer = setTimeout(() => {
      handleDismiss();
    }, duration);

    return () => clearTimeout(timer);
  }, [duration]);

  const handleDismiss = () => {
    setIsLeaving(true);
    setTimeout(onDismiss, 300);
  };

  // Play sound for critical alerts
  useEffect(() => {
    if (alert.severity === 'critical') {
      // Browser notification sound
      try {
        const audio = new Audio('/notification.mp3');
        audio.volume = 0.5;
        audio.play().catch(() => {});
      } catch {}
    }
  }, [alert.severity]);

  const severityStyles = {
    critical: 'border-red-500 bg-red-950',
    high: 'border-orange-500 bg-orange-950',
    medium: 'border-yellow-500 bg-yellow-950',
    low: 'border-blue-500 bg-blue-950',
  };

  const notification = (
    <div
      className={cn(
        'fixed top-4 right-4 z-[100] w-96 max-w-[calc(100vw-2rem)]',
        'transform transition-all duration-300',
        isVisible && !isLeaving
          ? 'translate-x-0 opacity-100'
          : 'translate-x-full opacity-0'
      )}
    >
      <div
        className={cn(
          'rounded-xl border-l-4 shadow-2xl backdrop-blur-sm',
          severityStyles[alert.severity],
          onClick && 'cursor-pointer'
        )}
        onClick={onClick}
      >
        {/* Critical alerts have pulsing border */}
        {alert.severity === 'critical' && (
          <div className="absolute inset-0 rounded-xl border-2 border-red-500 animate-pulse" />
        )}

        <div className="relative p-4">
          {/* Header */}
          <div className="flex items-start justify-between gap-3">
            <div className="flex items-center gap-3">
              <div className={cn('flex-shrink-0', getSeverityColor(alert.severity))}>
                {alert.severity === 'critical' ? (
                  <svg className="w-6 h-6 animate-pulse" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                  </svg>
                ) : (
                  <svg className="w-6 h-6" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                  </svg>
                )}
              </div>
              <div>
                <p className={cn('font-semibold', getSeverityColor(alert.severity))}>
                  {alert.severity === 'critical' ? 'CRITICAL ALERT' : 'Alert'}
                </p>
                <h4 className="font-medium text-white">{alert.title}</h4>
              </div>
            </div>
            <button
              onClick={(e) => {
                e.stopPropagation();
                handleDismiss();
              }}
              className="p-1 text-gray-400 hover:text-white rounded transition-colors"
            >
              <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                <path
                  fillRule="evenodd"
                  d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z"
                  clipRule="evenodd"
                />
              </svg>
            </button>
          </div>

          {/* Description */}
          <p className="mt-2 text-sm text-gray-300">{alert.description}</p>

          {/* Matched keywords */}
          {alert.matchedKeywords && alert.matchedKeywords.length > 0 && (
            <div className="flex flex-wrap gap-1 mt-2">
              {alert.matchedKeywords.slice(0, 3).map((kw, i) => (
                <span
                  key={i}
                  className="px-1.5 py-0.5 rounded bg-red-900/50 text-red-300 text-xs"
                >
                  {kw}
                </span>
              ))}
              {alert.matchedKeywords.length > 3 && (
                <span className="text-xs text-gray-500">
                  +{alert.matchedKeywords.length - 3} more
                </span>
              )}
            </div>
          )}

          {/* Progress bar */}
          <div className="mt-3 h-1 bg-gray-700 rounded-full overflow-hidden">
            <div
              className={cn(
                'h-full transition-all ease-linear',
                alert.severity === 'critical' && 'bg-red-500',
                alert.severity === 'high' && 'bg-orange-500',
                alert.severity === 'medium' && 'bg-yellow-500',
                alert.severity === 'low' && 'bg-blue-500'
              )}
              style={{
                animation: `shrink ${duration}ms linear forwards`,
              }}
            />
          </div>
        </div>
      </div>

      <style>{`
        @keyframes shrink {
          from { width: 100%; }
          to { width: 0%; }
        }
      `}</style>
    </div>
  );

  return createPortal(notification, document.body);
}

// Container for managing multiple notifications
export interface AlertNotificationContainerProps {
  alerts: Alert[];
  onDismiss: (id: string) => void;
  onClick?: (alert: Alert) => void;
  maxVisible?: number;
}

export function AlertNotificationContainer({
  alerts,
  onDismiss,
  onClick,
  maxVisible = 3,
}: AlertNotificationContainerProps) {
  const visibleAlerts = alerts.slice(0, maxVisible);

  return (
    <>
      {visibleAlerts.map((alert, index) => (
        <div
          key={alert.id}
          style={{ transform: `translateY(${index * 10}px)` }}
        >
          <AlertNotification
            alert={alert}
            onDismiss={() => onDismiss(alert.id)}
            onClick={onClick ? () => onClick(alert) : undefined}
          />
        </div>
      ))}
    </>
  );
}
