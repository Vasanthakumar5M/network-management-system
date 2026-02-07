/**
 * Traffic filters component for filtering traffic entries
 */

import { Input } from '@/components/common/Input';
import { Dropdown } from '@/components/common/Dropdown';
import { Button } from '@/components/common/Button';

export interface TrafficFilters {
  search: string;
  method: string | null;
  statusCode: string | null;
  deviceId: string | null;
  isBlocked: boolean | null;
  hasAlert: boolean | null;
}

export interface TrafficFiltersProps {
  filters: TrafficFilters;
  onChange: (filters: Partial<TrafficFilters>) => void;
  onClear: () => void;
  devices?: { id: string; hostname: string }[];
}

export function TrafficFilters({
  filters,
  onChange,
  onClear,
  devices = [],
}: TrafficFiltersProps) {
  const methodOptions = [
    { value: '', label: 'All Methods' },
    { value: 'GET', label: 'GET' },
    { value: 'POST', label: 'POST' },
    { value: 'PUT', label: 'PUT' },
    { value: 'DELETE', label: 'DELETE' },
    { value: 'PATCH', label: 'PATCH' },
    { value: 'OPTIONS', label: 'OPTIONS' },
    { value: 'HEAD', label: 'HEAD' },
  ];

  const statusOptions = [
    { value: '', label: 'All Status' },
    { value: '2xx', label: '2xx Success' },
    { value: '3xx', label: '3xx Redirect' },
    { value: '4xx', label: '4xx Client Error' },
    { value: '5xx', label: '5xx Server Error' },
  ];

  const deviceOptions = [
    { value: '', label: 'All Devices' },
    ...devices.map((d) => ({ value: d.id, label: d.hostname })),
  ];

  const hasActiveFilters =
    filters.search ||
    filters.method ||
    filters.statusCode ||
    filters.deviceId ||
    filters.isBlocked !== null ||
    filters.hasAlert !== null;

  return (
    <div className="bg-gray-800/50 rounded-lg p-4 space-y-4">
      {/* Search */}
      <div className="flex items-center gap-4">
        <div className="flex-1">
          <Input
            placeholder="Search URL, host, or path..."
            value={filters.search}
            onChange={(e) => onChange({ search: e.target.value })}
            leftIcon={
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
                />
              </svg>
            }
            rightIcon={
              filters.search && (
                <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                  <path
                    fillRule="evenodd"
                    d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z"
                    clipRule="evenodd"
                  />
                </svg>
              )
            }
            onRightIconClick={() => onChange({ search: '' })}
          />
        </div>

        {hasActiveFilters && (
          <Button variant="ghost" size="sm" onClick={onClear}>
            Clear filters
          </Button>
        )}
      </div>

      {/* Filter row */}
      <div className="flex flex-wrap items-center gap-4">
        {/* Method filter */}
        <div className="w-36">
          <Dropdown
            options={methodOptions}
            value={filters.method || ''}
            onChange={(value) => onChange({ method: value || null })}
            placeholder="Method"
          />
        </div>

        {/* Status filter */}
        <div className="w-36">
          <Dropdown
            options={statusOptions}
            value={filters.statusCode || ''}
            onChange={(value) => onChange({ statusCode: value || null })}
            placeholder="Status"
          />
        </div>

        {/* Device filter */}
        {devices.length > 0 && (
          <div className="w-44">
            <Dropdown
              options={deviceOptions}
              value={filters.deviceId || ''}
              onChange={(value) => onChange({ deviceId: value || null })}
              placeholder="Device"
              searchable
            />
          </div>
        )}

        {/* Divider */}
        <div className="h-6 w-px bg-gray-700" />

        {/* Blocked filter */}
        <label className="flex items-center gap-2 cursor-pointer">
          <input
            type="checkbox"
            className="rounded border-gray-600 bg-gray-700 text-blue-500 focus:ring-blue-500 focus:ring-offset-gray-900"
            checked={filters.isBlocked === true}
            onChange={(e) =>
              onChange({ isBlocked: e.target.checked ? true : null })
            }
          />
          <span className="text-sm text-gray-300">Blocked only</span>
        </label>

        {/* Alert filter */}
        <label className="flex items-center gap-2 cursor-pointer">
          <input
            type="checkbox"
            className="rounded border-gray-600 bg-gray-700 text-yellow-500 focus:ring-yellow-500 focus:ring-offset-gray-900"
            checked={filters.hasAlert === true}
            onChange={(e) =>
              onChange({ hasAlert: e.target.checked ? true : null })
            }
          />
          <span className="text-sm text-gray-300">With alerts</span>
        </label>
      </div>
    </div>
  );
}
