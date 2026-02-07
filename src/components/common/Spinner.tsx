import { cn } from '@/lib/utils';

export interface SpinnerProps {
  size?: 'sm' | 'md' | 'lg' | 'xl';
  className?: string;
  label?: string;
}

export function Spinner({ size = 'md', className, label }: SpinnerProps) {
  const sizes = {
    sm: 'w-4 h-4',
    md: 'w-6 h-6',
    lg: 'w-8 h-8',
    xl: 'w-12 h-12',
  };

  return (
    <div className={cn('inline-flex items-center gap-2', className)} role="status">
      <svg
        className={cn('animate-spin text-blue-500', sizes[size])}
        xmlns="http://www.w3.org/2000/svg"
        fill="none"
        viewBox="0 0 24 24"
        aria-hidden="true"
      >
        <circle
          className="opacity-25"
          cx="12"
          cy="12"
          r="10"
          stroke="currentColor"
          strokeWidth="4"
        />
        <path
          className="opacity-75"
          fill="currentColor"
          d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
        />
      </svg>
      {label && <span className="text-gray-400 text-sm">{label}</span>}
      <span className="sr-only">{label || 'Loading...'}</span>
    </div>
  );
}

// Full page loading spinner
export interface LoadingOverlayProps {
  isLoading: boolean;
  label?: string;
  blur?: boolean;
}

export function LoadingOverlay({
  isLoading,
  label = 'Loading...',
  blur = true,
}: LoadingOverlayProps) {
  if (!isLoading) return null;

  return (
    <div
      className={cn(
        'absolute inset-0 z-50 flex items-center justify-center',
        'bg-gray-900/80',
        blur && 'backdrop-blur-sm'
      )}
    >
      <div className="flex flex-col items-center gap-3">
        <Spinner size="lg" />
        <p className="text-gray-300 text-sm">{label}</p>
      </div>
    </div>
  );
}

// Skeleton loader for content placeholders
export interface SkeletonProps {
  className?: string;
  variant?: 'text' | 'circular' | 'rectangular';
  width?: string | number;
  height?: string | number;
  animate?: boolean;
}

export function Skeleton({
  className,
  variant = 'text',
  width,
  height,
  animate = true,
}: SkeletonProps) {
  const variants = {
    text: 'rounded-md',
    circular: 'rounded-full',
    rectangular: 'rounded-lg',
  };

  const defaultDimensions = {
    text: { width: '100%', height: '1rem' },
    circular: { width: '2.5rem', height: '2.5rem' },
    rectangular: { width: '100%', height: '4rem' },
  };

  return (
    <div
      className={cn(
        'bg-gray-700',
        variants[variant],
        animate && 'animate-pulse',
        className
      )}
      style={{
        width: width ?? defaultDimensions[variant].width,
        height: height ?? defaultDimensions[variant].height,
      }}
      aria-hidden="true"
    />
  );
}
