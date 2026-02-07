import type { ReactNode } from 'react';
import { cn } from '@/lib/utils';

export interface BadgeProps {
  children: ReactNode;
  variant?: 'default' | 'success' | 'warning' | 'danger' | 'info' | 'outline';
  size?: 'sm' | 'md' | 'lg';
  className?: string;
  dot?: boolean;
  removable?: boolean;
  onRemove?: () => void;
}

export function Badge({
  children,
  variant = 'default',
  size = 'md',
  className,
  dot = false,
  removable = false,
  onRemove,
}: BadgeProps) {
  const variants = {
    default: 'bg-gray-700 text-gray-300',
    success: 'bg-green-900/50 text-green-400 border border-green-800',
    warning: 'bg-yellow-900/50 text-yellow-400 border border-yellow-800',
    danger: 'bg-red-900/50 text-red-400 border border-red-800',
    info: 'bg-blue-900/50 text-blue-400 border border-blue-800',
    outline: 'bg-transparent border border-gray-600 text-gray-400',
  };

  const sizes = {
    sm: 'px-1.5 py-0.5 text-xs',
    md: 'px-2 py-0.5 text-xs',
    lg: 'px-2.5 py-1 text-sm',
  };

  const dotColors = {
    default: 'bg-gray-400',
    success: 'bg-green-400',
    warning: 'bg-yellow-400',
    danger: 'bg-red-400',
    info: 'bg-blue-400',
    outline: 'bg-gray-400',
  };

  return (
    <span
      className={cn(
        'inline-flex items-center gap-1.5 rounded-full font-medium',
        variants[variant],
        sizes[size],
        className
      )}
    >
      {dot && (
        <span
          className={cn('w-1.5 h-1.5 rounded-full', dotColors[variant])}
          aria-hidden="true"
        />
      )}
      {children}
      {removable && (
        <button
          type="button"
          onClick={onRemove}
          className="ml-0.5 -mr-0.5 p-0.5 rounded-full hover:bg-white/10 transition-colors"
          aria-label="Remove"
        >
          <svg className="w-3 h-3" fill="currentColor" viewBox="0 0 20 20">
            <path
              fillRule="evenodd"
              d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z"
              clipRule="evenodd"
            />
          </svg>
        </button>
      )}
    </span>
  );
}

// Status badge for online/offline indicators
export interface StatusBadgeProps {
  status: 'online' | 'offline' | 'idle' | 'busy';
  label?: string;
  showDot?: boolean;
  className?: string;
}

export function StatusBadge({
  status,
  label,
  showDot = true,
  className,
}: StatusBadgeProps) {
  const statusConfig = {
    online: { color: 'bg-green-500', text: 'Online', textColor: 'text-green-400' },
    offline: { color: 'bg-gray-500', text: 'Offline', textColor: 'text-gray-400' },
    idle: { color: 'bg-yellow-500', text: 'Idle', textColor: 'text-yellow-400' },
    busy: { color: 'bg-red-500', text: 'Busy', textColor: 'text-red-400' },
  };

  const config = statusConfig[status];

  return (
    <span
      className={cn('inline-flex items-center gap-1.5 text-sm', className)}
    >
      {showDot && (
        <span
          className={cn('w-2 h-2 rounded-full', config.color)}
          aria-hidden="true"
        />
      )}
      <span className={config.textColor}>{label || config.text}</span>
    </span>
  );
}
