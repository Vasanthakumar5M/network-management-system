import { useState } from 'react';
import { 
  Monitor, 
  Smartphone, 
  Laptop, 
  Tv, 
  Tablet,
  Printer,
  Speaker,
  Gamepad,
  MoreHorizontal,
  Eye,
  EyeOff,
  Ban,
  Activity,
  Clock,
  AlertTriangle
} from 'lucide-react';
import { cn, formatBytes, formatRelativeTime } from '@/lib/utils';
import type { Device } from '@/types';

const deviceIcons: Record<string, React.ElementType> = {
  phone: Smartphone,
  laptop: Laptop,
  desktop: Monitor,
  tv: Tv,
  tablet: Tablet,
  printer: Printer,
  speaker: Speaker,
  gaming: Gamepad,
  default: Monitor,
};

// Mock devices for now
const mockDevices: Device[] = [
  {
    id: '1',
    mac: 'AA:BB:CC:DD:EE:01',
    ip: '192.168.1.101',
    hostname: 'iPhone-Alex',
    vendor: 'Apple Inc.',
    deviceType: 'phone',
    firstSeen: '2025-01-15T10:00:00Z',
    lastSeen: '2025-02-07T12:30:00Z',
    isOnline: true,
    isMonitored: true,
    totalBytes: 2.5 * 1024 * 1024 * 1024,
    blockedRequests: 45,
    alerts: 3,
  },
  {
    id: '2',
    mac: 'AA:BB:CC:DD:EE:02',
    ip: '192.168.1.102',
    hostname: 'Gaming-PC',
    vendor: 'Intel Corporation',
    deviceType: 'desktop',
    firstSeen: '2025-01-10T08:00:00Z',
    lastSeen: '2025-02-07T11:00:00Z',
    isOnline: true,
    isMonitored: true,
    totalBytes: 15 * 1024 * 1024 * 1024,
    blockedRequests: 120,
    alerts: 8,
  },
  {
    id: '3',
    mac: 'AA:BB:CC:DD:EE:03',
    ip: '192.168.1.103',
    hostname: 'Samsung-Tab',
    vendor: 'Samsung Electronics',
    deviceType: 'tablet',
    firstSeen: '2025-01-20T14:00:00Z',
    lastSeen: '2025-02-06T22:00:00Z',
    isOnline: false,
    isMonitored: true,
    totalBytes: 800 * 1024 * 1024,
    blockedRequests: 12,
    alerts: 0,
  },
  {
    id: '4',
    mac: 'AA:BB:CC:DD:EE:04',
    ip: '192.168.1.104',
    hostname: 'Smart-TV',
    vendor: 'LG Electronics',
    deviceType: 'tv',
    firstSeen: '2025-01-01T00:00:00Z',
    lastSeen: '2025-02-07T13:00:00Z',
    isOnline: true,
    isMonitored: false,
    totalBytes: 50 * 1024 * 1024 * 1024,
    blockedRequests: 0,
    alerts: 0,
  },
];

export default function Devices() {
  const [selectedDevice, setSelectedDevice] = useState<Device | null>(null);
  const [filter, setFilter] = useState<'all' | 'online' | 'monitored'>('all');

  const filteredDevices = mockDevices.filter(device => {
    if (filter === 'online') return device.isOnline;
    if (filter === 'monitored') return device.isMonitored;
    return true;
  });

  const onlineCount = mockDevices.filter(d => d.isOnline).length;
  const monitoredCount = mockDevices.filter(d => d.isMonitored).length;

  return (
    <div className="p-6 h-full flex flex-col">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold">Devices</h1>
          <p className="text-dark-400">
            {onlineCount} online, {monitoredCount} monitored
          </p>
        </div>
        
        {/* Filters */}
        <div className="flex gap-2">
          {(['all', 'online', 'monitored'] as const).map((f) => (
            <button
              key={f}
              onClick={() => setFilter(f)}
              className={cn(
                "px-4 py-2 rounded-lg text-sm font-medium transition-colors",
                filter === f
                  ? "bg-primary-600 text-white"
                  : "bg-dark-700 text-dark-300 hover:bg-dark-600"
              )}
            >
              {f.charAt(0).toUpperCase() + f.slice(1)}
            </button>
          ))}
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 flex gap-6 min-h-0">
        {/* Device List */}
        <div className="flex-1 space-y-3 overflow-auto">
          {filteredDevices.map((device) => (
            <DeviceCard
              key={device.id}
              device={device}
              isSelected={selectedDevice?.id === device.id}
              onClick={() => setSelectedDevice(device)}
            />
          ))}
        </div>

        {/* Detail Panel */}
        {selectedDevice && (
          <div className="w-96 card p-4 overflow-auto">
            <DeviceDetail device={selectedDevice} />
          </div>
        )}
      </div>
    </div>
  );
}

function DeviceCard({ 
  device, 
  isSelected, 
  onClick 
}: { 
  device: Device; 
  isSelected: boolean;
  onClick: () => void;
}) {
  const Icon = deviceIcons[device.deviceType] || deviceIcons.default;

  return (
    <div
      onClick={onClick}
      className={cn(
        "card-hover p-4 cursor-pointer",
        isSelected && "border-primary-500 bg-primary-500/5"
      )}
    >
      <div className="flex items-center gap-4">
        {/* Icon */}
        <div className={cn(
          "w-12 h-12 rounded-lg flex items-center justify-center",
          device.isOnline ? "bg-green-500/10" : "bg-dark-700"
        )}>
          <Icon className={cn(
            "w-6 h-6",
            device.isOnline ? "text-green-500" : "text-dark-500"
          )} />
        </div>

        {/* Info */}
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <h3 className="font-medium truncate">{device.hostname}</h3>
            {device.isMonitored && (
              <Eye className="w-4 h-4 text-primary-500" />
            )}
            {device.alerts > 0 && (
              <span className="bg-red-500 text-white text-xs px-1.5 py-0.5 rounded">
                {device.alerts}
              </span>
            )}
          </div>
          <div className="flex items-center gap-2 text-sm text-dark-400">
            <span>{device.ip}</span>
            <span>•</span>
            <span>{device.vendor}</span>
          </div>
        </div>

        {/* Status */}
        <div className="text-right">
          <div className={cn(
            "text-sm font-medium",
            device.isOnline ? "text-green-500" : "text-dark-500"
          )}>
            {device.isOnline ? 'Online' : 'Offline'}
          </div>
          <div className="text-xs text-dark-400">
            {formatRelativeTime(device.lastSeen)}
          </div>
        </div>
      </div>
    </div>
  );
}

function DeviceDetail({ device }: { device: Device }) {
  const Icon = deviceIcons[device.deviceType] || deviceIcons.default;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-4">
        <div className={cn(
          "w-16 h-16 rounded-xl flex items-center justify-center",
          device.isOnline ? "bg-green-500/10" : "bg-dark-700"
        )}>
          <Icon className={cn(
            "w-8 h-8",
            device.isOnline ? "text-green-500" : "text-dark-500"
          )} />
        </div>
        <div>
          <h2 className="text-xl font-bold">{device.hostname}</h2>
          <p className="text-dark-400">{device.vendor}</p>
        </div>
      </div>

      {/* Quick Actions */}
      <div className="flex gap-2">
        <button className={cn(
          "flex-1 py-2 rounded-lg text-sm font-medium flex items-center justify-center gap-2",
          device.isMonitored
            ? "bg-primary-600 text-white"
            : "bg-dark-700 text-dark-300"
        )}>
          {device.isMonitored ? <Eye className="w-4 h-4" /> : <EyeOff className="w-4 h-4" />}
          {device.isMonitored ? 'Monitoring' : 'Not Monitored'}
        </button>
        <button className="p-2 rounded-lg bg-dark-700 text-dark-300 hover:bg-dark-600">
          <MoreHorizontal className="w-5 h-5" />
        </button>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 gap-3">
        <StatBox
          label="Traffic"
          value={formatBytes(device.totalBytes)}
          icon={<Activity className="w-4 h-4 text-primary-500" />}
        />
        <StatBox
          label="Blocked"
          value={device.blockedRequests.toString()}
          icon={<Ban className="w-4 h-4 text-red-500" />}
        />
        <StatBox
          label="Alerts"
          value={device.alerts.toString()}
          icon={<AlertTriangle className="w-4 h-4 text-yellow-500" />}
        />
        <StatBox
          label="First Seen"
          value={formatRelativeTime(device.firstSeen)}
          icon={<Clock className="w-4 h-4 text-dark-400" />}
        />
      </div>

      {/* Details */}
      <div className="space-y-3">
        <h3 className="font-medium text-dark-300">Details</h3>
        <DetailRow label="IP Address" value={device.ip} />
        <DetailRow label="MAC Address" value={device.mac} />
        <DetailRow label="Device Type" value={device.deviceType} />
        <DetailRow 
          label="Last Seen" 
          value={new Date(device.lastSeen).toLocaleString()} 
        />
      </div>
    </div>
  );
}

function StatBox({ 
  label, 
  value, 
  icon 
}: { 
  label: string; 
  value: string; 
  icon: React.ReactNode;
}) {
  return (
    <div className="bg-dark-700/50 rounded-lg p-3">
      <div className="flex items-center gap-2 mb-1">
        {icon}
        <span className="text-xs text-dark-400">{label}</span>
      </div>
      <p className="font-semibold">{value}</p>
    </div>
  );
}

function DetailRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-center justify-between text-sm">
      <span className="text-dark-400">{label}</span>
      <span className="font-mono">{value}</span>
    </div>
  );
}
