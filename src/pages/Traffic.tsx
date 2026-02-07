import { useState } from 'react';
import { 
  Search, 
  Filter, 
  Download,
  ChevronDown,
  ExternalLink,
  Clock,
  ArrowRight,
  X
} from 'lucide-react';
import { cn, formatBytes, formatDuration, getMethodClass, getStatusCodeClass } from '@/lib/utils';
import type { TrafficEntry } from '@/types';

// Mock traffic data
const mockTraffic: TrafficEntry[] = [
  {
    id: '1',
    timestamp: '2025-02-07T12:30:15Z',
    deviceId: '1',
    deviceIp: '192.168.1.101',
    method: 'GET',
    url: 'https://www.youtube.com/watch?v=dQw4w9WgXcQ',
    host: 'www.youtube.com',
    path: '/watch',
    statusCode: 200,
    contentType: 'text/html',
    requestSize: 1024,
    responseSize: 45678,
    duration: 234,
    isBlocked: false,
    hasAlert: false,
    category: 'streaming',
  },
  {
    id: '2',
    timestamp: '2025-02-07T12:30:10Z',
    deviceId: '1',
    deviceIp: '192.168.1.101',
    method: 'POST',
    url: 'https://api.instagram.com/graphql',
    host: 'api.instagram.com',
    path: '/graphql',
    statusCode: 200,
    contentType: 'application/json',
    requestSize: 2048,
    responseSize: 12345,
    duration: 156,
    isBlocked: false,
    hasAlert: false,
    category: 'social_media',
  },
  {
    id: '3',
    timestamp: '2025-02-07T12:29:55Z',
    deviceId: '2',
    deviceIp: '192.168.1.102',
    method: 'GET',
    url: 'https://store.steampowered.com/app/123456',
    host: 'store.steampowered.com',
    path: '/app/123456',
    statusCode: 200,
    contentType: 'text/html',
    requestSize: 512,
    responseSize: 89012,
    duration: 345,
    isBlocked: false,
    hasAlert: false,
    category: 'gaming',
  },
  {
    id: '4',
    timestamp: '2025-02-07T12:29:30Z',
    deviceId: '1',
    deviceIp: '192.168.1.101',
    method: 'GET',
    url: 'https://blocked-site.example.com/page',
    host: 'blocked-site.example.com',
    path: '/page',
    statusCode: 403,
    contentType: 'text/html',
    requestSize: 256,
    responseSize: 0,
    duration: 5,
    isBlocked: true,
    hasAlert: false,
    category: 'adult',
  },
  {
    id: '5',
    timestamp: '2025-02-07T12:29:00Z',
    deviceId: '2',
    deviceIp: '192.168.1.102',
    method: 'GET',
    url: 'https://discord.com/channels/@me',
    host: 'discord.com',
    path: '/channels/@me',
    statusCode: 200,
    contentType: 'text/html',
    requestSize: 1024,
    responseSize: 34567,
    duration: 189,
    isBlocked: false,
    hasAlert: true,
    category: 'social_media',
  },
];

export default function Traffic() {
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedEntry, setSelectedEntry] = useState<TrafficEntry | null>(null);
  const [showFilters, setShowFilters] = useState(false);

  const filteredTraffic = mockTraffic.filter(entry => 
    entry.url.toLowerCase().includes(searchQuery.toLowerCase()) ||
    entry.host.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <div className="p-6 h-full flex flex-col">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div>
          <h1 className="text-2xl font-bold">Traffic</h1>
          <p className="text-dark-400">HTTP/HTTPS requests captured</p>
        </div>
        <button className="flex items-center gap-2 px-4 py-2 bg-dark-700 rounded-lg text-sm hover:bg-dark-600">
          <Download className="w-4 h-4" />
          Export
        </button>
      </div>

      {/* Search & Filters */}
      <div className="flex gap-3 mb-4">
        <div className="flex-1 relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-dark-400" />
          <input
            type="text"
            placeholder="Search URLs, hosts, paths..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-10 pr-4 py-2.5 bg-dark-800 border border-dark-700 rounded-lg text-sm focus:outline-none focus:border-primary-500"
          />
        </div>
        <button 
          onClick={() => setShowFilters(!showFilters)}
          className={cn(
            "flex items-center gap-2 px-4 py-2 rounded-lg text-sm",
            showFilters ? "bg-primary-600 text-white" : "bg-dark-700 text-dark-300"
          )}
        >
          <Filter className="w-4 h-4" />
          Filters
          <ChevronDown className={cn(
            "w-4 h-4 transition-transform",
            showFilters && "rotate-180"
          )} />
        </button>
      </div>

      {/* Filter Panel */}
      {showFilters && (
        <div className="card p-4 mb-4 flex flex-wrap gap-4">
          <FilterSelect label="Method" options={['All', 'GET', 'POST', 'PUT', 'DELETE']} />
          <FilterSelect label="Status" options={['All', '2xx', '3xx', '4xx', '5xx']} />
          <FilterSelect label="Device" options={['All Devices', '192.168.1.101', '192.168.1.102']} />
          <FilterToggle label="Blocked Only" />
          <FilterToggle label="With Alerts" />
        </div>
      )}

      {/* Content */}
      <div className="flex-1 flex gap-4 min-h-0">
        {/* Traffic Table */}
        <div className="flex-1 card overflow-hidden flex flex-col">
          {/* Table Header */}
          <div className="grid grid-cols-12 gap-2 px-4 py-3 bg-dark-700/50 text-xs text-dark-400 font-medium">
            <div className="col-span-1">Time</div>
            <div className="col-span-1">Method</div>
            <div className="col-span-5">URL</div>
            <div className="col-span-1">Status</div>
            <div className="col-span-2">Size</div>
            <div className="col-span-1">Duration</div>
            <div className="col-span-1">Device</div>
          </div>

          {/* Table Body */}
          <div className="flex-1 overflow-auto">
            {filteredTraffic.map((entry) => (
              <TrafficRow
                key={entry.id}
                entry={entry}
                isSelected={selectedEntry?.id === entry.id}
                onClick={() => setSelectedEntry(entry)}
              />
            ))}
          </div>
        </div>

        {/* Detail Panel */}
        {selectedEntry && (
          <div className="w-96 card flex flex-col overflow-hidden">
            <div className="p-4 border-b border-dark-700 flex items-center justify-between">
              <h3 className="font-semibold">Request Details</h3>
              <button 
                onClick={() => setSelectedEntry(null)}
                className="p-1 hover:bg-dark-700 rounded"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
            <div className="flex-1 overflow-auto p-4">
              <TrafficDetail entry={selectedEntry} />
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

function TrafficRow({ 
  entry, 
  isSelected, 
  onClick 
}: { 
  entry: TrafficEntry; 
  isSelected: boolean;
  onClick: () => void;
}) {
  const time = new Date(entry.timestamp).toLocaleTimeString();
  
  return (
    <div 
      onClick={onClick}
      className={cn(
        "traffic-row grid grid-cols-12 gap-2 px-4 py-2.5 text-sm",
        isSelected && "selected",
        entry.isBlocked && "bg-red-500/5",
        entry.hasAlert && "bg-yellow-500/5"
      )}
    >
      <div className="col-span-1 text-dark-400 font-mono text-xs">{time}</div>
      <div className="col-span-1">
        <span className={cn("method-badge", getMethodClass(entry.method))}>
          {entry.method}
        </span>
      </div>
      <div className="col-span-5 truncate flex items-center gap-2">
        <span className="truncate">{entry.host}</span>
        <span className="text-dark-500 truncate">{entry.path}</span>
        {entry.isBlocked && (
          <span className="bg-red-500/20 text-red-400 text-xs px-1.5 rounded">Blocked</span>
        )}
        {entry.hasAlert && (
          <span className="bg-yellow-500/20 text-yellow-400 text-xs px-1.5 rounded">Alert</span>
        )}
      </div>
      <div className="col-span-1">
        <span className={cn("status-badge", getStatusCodeClass(entry.statusCode))}>
          {entry.statusCode}
        </span>
      </div>
      <div className="col-span-2 text-dark-400 text-xs">
        {formatBytes(entry.responseSize)}
      </div>
      <div className="col-span-1 text-dark-400 text-xs">
        {formatDuration(entry.duration)}
      </div>
      <div className="col-span-1 text-dark-400 text-xs font-mono">
        {entry.deviceIp.split('.').slice(-1)}
      </div>
    </div>
  );
}

function TrafficDetail({ entry }: { entry: TrafficEntry }) {
  return (
    <div className="space-y-4">
      {/* URL */}
      <div>
        <label className="text-xs text-dark-400 uppercase">URL</label>
        <div className="flex items-center gap-2 mt-1">
          <code className="text-sm break-all flex-1">{entry.url}</code>
          <a 
            href={entry.url} 
            target="_blank" 
            rel="noopener noreferrer"
            className="p-1.5 hover:bg-dark-700 rounded"
          >
            <ExternalLink className="w-4 h-4 text-dark-400" />
          </a>
        </div>
      </div>

      {/* Info Grid */}
      <div className="grid grid-cols-2 gap-3">
        <InfoCard label="Method">
          <span className={cn("method-badge", getMethodClass(entry.method))}>
            {entry.method}
          </span>
        </InfoCard>
        <InfoCard label="Status">
          <span className={cn("status-badge", getStatusCodeClass(entry.statusCode))}>
            {entry.statusCode}
          </span>
        </InfoCard>
        <InfoCard label="Request Size">
          {formatBytes(entry.requestSize)}
        </InfoCard>
        <InfoCard label="Response Size">
          {formatBytes(entry.responseSize)}
        </InfoCard>
        <InfoCard label="Duration">
          {formatDuration(entry.duration)}
        </InfoCard>
        <InfoCard label="Content Type">
          {entry.contentType.split(';')[0]}
        </InfoCard>
      </div>

      {/* Flow */}
      <div className="bg-dark-700/50 rounded-lg p-3">
        <div className="flex items-center gap-3 text-sm">
          <span className="font-mono">{entry.deviceIp}</span>
          <ArrowRight className="w-4 h-4 text-dark-400" />
          <span className="font-mono">{entry.host}</span>
        </div>
        <div className="flex items-center gap-2 mt-2 text-xs text-dark-400">
          <Clock className="w-3 h-3" />
          {new Date(entry.timestamp).toLocaleString()}
        </div>
      </div>

      {/* Category */}
      <div>
        <label className="text-xs text-dark-400 uppercase">Category</label>
        <div className="mt-1 inline-block px-2 py-1 bg-dark-700 rounded text-sm">
          {entry.category}
        </div>
      </div>
    </div>
  );
}

function InfoCard({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="bg-dark-700/50 rounded-lg p-2">
      <div className="text-xs text-dark-400 mb-1">{label}</div>
      <div className="text-sm">{children}</div>
    </div>
  );
}

function FilterSelect({ label, options }: { label: string; options: string[] }) {
  return (
    <div>
      <label className="text-xs text-dark-400 block mb-1">{label}</label>
      <select className="bg-dark-700 border border-dark-600 rounded-lg px-3 py-1.5 text-sm">
        {options.map(opt => (
          <option key={opt} value={opt}>{opt}</option>
        ))}
      </select>
    </div>
  );
}

function FilterToggle({ label }: { label: string }) {
  const [checked, setChecked] = useState(false);
  return (
    <label className="flex items-center gap-2 cursor-pointer">
      <input
        type="checkbox"
        checked={checked}
        onChange={(e) => setChecked(e.target.checked)}
        className="w-4 h-4 rounded border-dark-600 bg-dark-700 text-primary-600 focus:ring-primary-500"
      />
      <span className="text-sm">{label}</span>
    </label>
  );
}
