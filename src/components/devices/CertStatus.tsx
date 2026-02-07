/**
 * Certificate status indicator component
 */

import { cn } from '@/lib/utils';
import { Button } from '@/components/common/Button';
import { Badge } from '@/components/common/Badge';

export type CertStatusType = 'installed' | 'pending' | 'not_installed' | 'expired';

export interface CertStatusProps {
  status: CertStatusType;
  deviceType?: string;
  onInstall?: () => void;
  onRevoke?: () => void;
  className?: string;
}

export function CertStatus({
  status,
  deviceType,
  onInstall,
  onRevoke,
  className,
}: CertStatusProps) {
  const statusConfig: Record<
    CertStatusType,
    { label: string; variant: 'success' | 'warning' | 'danger' | 'info'; icon: React.ReactNode }
  > = {
    installed: {
      label: 'Certificate Installed',
      variant: 'success',
      icon: (
        <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
          <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
        </svg>
      ),
    },
    pending: {
      label: 'Installation Pending',
      variant: 'warning',
      icon: (
        <svg className="w-5 h-5 animate-spin" fill="none" viewBox="0 0 24 24">
          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
        </svg>
      ),
    },
    not_installed: {
      label: 'Certificate Not Installed',
      variant: 'info',
      icon: (
        <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
          <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
        </svg>
      ),
    },
    expired: {
      label: 'Certificate Expired',
      variant: 'danger',
      icon: (
        <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
          <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
        </svg>
      ),
    },
  };

  const config = statusConfig[status];

  return (
    <div className={cn('p-4 rounded-lg bg-gray-800/50 border border-gray-700/50', className)}>
      <div className="flex items-center gap-3 mb-3">
        <div className={cn(
          'p-2 rounded-lg',
          config.variant === 'success' && 'bg-green-900/20 text-green-400',
          config.variant === 'warning' && 'bg-yellow-900/20 text-yellow-400',
          config.variant === 'danger' && 'bg-red-900/20 text-red-400',
          config.variant === 'info' && 'bg-blue-900/20 text-blue-400',
        )}>
          {config.icon}
        </div>
        <div>
          <p className="font-medium text-white">{config.label}</p>
          {deviceType && (
            <p className="text-sm text-gray-400 capitalize">{deviceType} device</p>
          )}
        </div>
      </div>

      {/* Action buttons */}
      <div className="flex items-center gap-2">
        {(status === 'not_installed' || status === 'expired') && onInstall && (
          <Button size="sm" onClick={onInstall}>
            {status === 'expired' ? 'Reinstall Certificate' : 'Install Certificate'}
          </Button>
        )}
        {status === 'installed' && onRevoke && (
          <Button variant="danger" size="sm" onClick={onRevoke}>
            Revoke Certificate
          </Button>
        )}
        {status === 'pending' && (
          <Badge variant="warning">Waiting for device to complete installation</Badge>
        )}
      </div>

      {/* Help text */}
      {status === 'not_installed' && (
        <p className="mt-3 text-xs text-gray-500">
          HTTPS traffic from this device cannot be decrypted without installing the CA certificate.
        </p>
      )}
    </div>
  );
}
