/**
 * Stealth panel component for managing device disguise settings
 */

import { useState } from 'react';
import { cn } from '@/lib/utils';
import { Button } from '@/components/common/Button';
import { Toggle } from '@/components/common/Toggle';
import { Badge } from '@/components/common/Badge';
import { Card, CardHeader } from '@/components/common/Card';
import type { DeviceProfile } from '@/lib/api';

export interface StealthPanelProps {
  isActive: boolean;
  currentProfile?: DeviceProfile;
  profiles: DeviceProfile[];
  originalMac?: string;
  currentMac?: string;
  originalHostname?: string;
  currentHostname?: string;
  isLoading?: boolean;
  onToggle: (enabled: boolean) => void;
  onChangeProfile: (profileId: string) => void;
  onApply: () => void;
  onRestore: () => void;
}

export function StealthPanel({
  isActive,
  currentProfile,
  profiles,
  originalMac,
  currentMac,
  originalHostname,
  currentHostname,
  isLoading = false,
  onToggle,
  onChangeProfile,
  onApply,
  onRestore,
}: StealthPanelProps) {
  const [selectedProfileId, setSelectedProfileId] = useState(currentProfile?.id || '');

  // Group profiles by type
  const profilesByType = profiles.reduce<Record<string, DeviceProfile[]>>((acc, p) => {
    if (!acc[p.type]) acc[p.type] = [];
    acc[p.type].push(p);
    return acc;
  }, {});

  const handleProfileSelect = (profileId: string) => {
    setSelectedProfileId(profileId);
    onChangeProfile(profileId);
  };

  return (
    <div className="space-y-6">
      {/* Status card */}
      <Card className={cn(isActive ? 'bg-green-900/20 border-green-800/50' : '')}>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <div className={cn(
              'p-3 rounded-lg',
              isActive ? 'bg-green-900/30 text-green-400' : 'bg-gray-700/50 text-gray-400'
            )}>
              <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M8.111 16.404a5.5 5.5 0 017.778 0M12 20h.01m-7.08-7.071c3.904-3.905 10.236-3.905 14.141 0M1.394 9.393c5.857-5.857 15.355-5.857 21.213 0" />
              </svg>
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h3 className="text-lg font-semibold text-white">Stealth Mode</h3>
                {isActive && (
                  <Badge variant="success" dot>Active</Badge>
                )}
              </div>
              <p className="text-sm text-gray-400">
                {isActive
                  ? `Disguised as ${currentProfile?.name || 'Unknown Device'}`
                  : 'Device identity is visible on network'}
              </p>
            </div>
          </div>
          <Toggle
            checked={isActive}
            onChange={(e) => onToggle(e.target.checked)}
            size="lg"
          />
        </div>

        {/* Current identity info */}
        {isActive && (
          <div className="mt-4 pt-4 border-t border-gray-700/50 grid grid-cols-2 gap-4">
            <div>
              <p className="text-xs text-gray-500 mb-1">MAC Address</p>
              <p className="font-mono text-sm text-gray-300">
                {currentMac || 'Unknown'}
              </p>
              {originalMac && originalMac !== currentMac && (
                <p className="font-mono text-xs text-gray-500 mt-0.5">
                  Original: {originalMac}
                </p>
              )}
            </div>
            <div>
              <p className="text-xs text-gray-500 mb-1">Hostname</p>
              <p className="font-mono text-sm text-gray-300">
                {currentHostname || 'Unknown'}
              </p>
              {originalHostname && originalHostname !== currentHostname && (
                <p className="font-mono text-xs text-gray-500 mt-0.5">
                  Original: {originalHostname}
                </p>
              )}
            </div>
          </div>
        )}
      </Card>

      {/* Profile selector */}
      <Card>
        <CardHeader
          title="Device Profile"
          description="Select how this computer appears on the network"
        />
        <div className="mt-4 space-y-4">
          {Object.entries(profilesByType).map(([type, typeProfiles]) => (
            <div key={type}>
              <h4 className="text-xs font-medium text-gray-500 uppercase tracking-wider mb-2">
                {type.replace('_', ' ')}
              </h4>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                {typeProfiles.map((profile) => (
                  <ProfileCard
                    key={profile.id}
                    profile={profile}
                    isSelected={selectedProfileId === profile.id}
                    isCurrent={currentProfile?.id === profile.id}
                    onSelect={() => handleProfileSelect(profile.id)}
                  />
                ))}
              </div>
            </div>
          ))}
        </div>
      </Card>

      {/* Actions */}
      <div className="flex items-center justify-end gap-3">
        {isActive && (
          <Button variant="outline" onClick={onRestore} isLoading={isLoading}>
            Restore Original
          </Button>
        )}
        <Button
          onClick={onApply}
          isLoading={isLoading}
          disabled={!selectedProfileId}
        >
          {isActive ? 'Update Identity' : 'Apply Stealth Mode'}
        </Button>
      </div>
    </div>
  );
}

// Profile card component
interface ProfileCardProps {
  profile: DeviceProfile;
  isSelected: boolean;
  isCurrent: boolean;
  onSelect: () => void;
}

function ProfileCard({ profile, isSelected, isCurrent, onSelect }: ProfileCardProps) {
  // Device type icons
  const typeIcons: Record<string, React.ReactNode> = {
    printer: (
      <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M17 17h2a2 2 0 002-2v-4a2 2 0 00-2-2H5a2 2 0 00-2 2v4a2 2 0 002 2h2m2 4h6a2 2 0 002-2v-4a2 2 0 00-2-2H9a2 2 0 00-2 2v4a2 2 0 002 2zm8-12V5a2 2 0 00-2-2H9a2 2 0 00-2 2v4h10z" />
      </svg>
    ),
    tv: (
      <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
      </svg>
    ),
    smart_home: (
      <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6" />
      </svg>
    ),
    nas: (
      <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M5 12h14M5 12a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v4a2 2 0 01-2 2M5 12a2 2 0 00-2 2v4a2 2 0 002 2h14a2 2 0 002-2v-4a2 2 0 00-2-2m-2-4h.01M17 16h.01" />
      </svg>
    ),
    default: (
      <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 3v2m6-2v2M9 19v2m6-2v2M5 9H3m2 6H3m18-6h-2m2 6h-2M7 19h10a2 2 0 002-2V7a2 2 0 00-2-2H7a2 2 0 00-2 2v10a2 2 0 002 2zM9 9h6v6H9V9z" />
      </svg>
    ),
  };

  const icon = typeIcons[profile.type] || typeIcons.default;

  return (
    <button
      type="button"
      onClick={onSelect}
      className={cn(
        'flex items-center gap-3 p-3 rounded-lg border text-left transition-all',
        isSelected
          ? 'bg-blue-900/30 border-blue-500/50 ring-1 ring-blue-500/30'
          : 'bg-gray-800/50 border-gray-700/50 hover:bg-gray-800/70 hover:border-gray-600'
      )}
    >
      <div className={cn(
        'p-2 rounded-lg',
        isSelected ? 'bg-blue-900/30 text-blue-400' : 'bg-gray-700/50 text-gray-400'
      )}>
        {icon}
      </div>
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2">
          <span className="font-medium text-white truncate">{profile.name}</span>
          {isCurrent && (
            <Badge variant="success" size="sm">Current</Badge>
          )}
        </div>
        <p className="text-xs text-gray-500 truncate">{profile.vendor}</p>
      </div>
    </button>
  );
}
