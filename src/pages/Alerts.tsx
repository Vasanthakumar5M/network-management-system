import { useState } from 'react';
import { 
  AlertTriangle, 
  AlertCircle, 
  Info, 
  Bell,
  Check,
  Trash2,
  ExternalLink,
  Clock,
  Tag
} from 'lucide-react';
import { cn, formatRelativeTime, getSeverityColor, getSeverityBg } from '@/lib/utils';
import type { Alert } from '@/types';

const mockAlerts: Alert[] = [
  {
    id: '1',
    timestamp: '2025-02-07T12:30:00Z',
    deviceId: '1',
    severity: 'critical',
    category: 'self_harm',
    title: 'Self-harm keywords detected',
    description: 'Concerning search query detected on device iPhone-Alex',
    url: 'https://google.com/search?q=...',
    matchedKeywords: ['hurt myself', 'self harm'],
    isRead: false,
    isResolved: false,
  },
  {
    id: '2',
    timestamp: '2025-02-07T11:15:00Z',
    deviceId: '2',
    severity: 'high',
    category: 'vpn_detected',
    title: 'VPN usage detected',
    description: 'Attempt to access VPN service from Gaming-PC',
    url: 'https://nordvpn.com/download',
    isRead: false,
    isResolved: false,
  },
  {
    id: '3',
    timestamp: '2025-02-07T10:00:00Z',
    deviceId: '1',
    severity: 'medium',
    category: 'blocked_attempt',
    title: 'Blocked site access attempt',
    description: 'Attempted to access adult content site',
    url: 'https://blocked-site.example.com',
    isRead: true,
    isResolved: false,
  },
  {
    id: '4',
    timestamp: '2025-02-06T22:30:00Z',
    deviceId: '3',
    severity: 'high',
    category: 'predator_grooming',
    title: 'Suspicious conversation detected',
    description: 'Potentially concerning phrases detected in chat',
    matchedKeywords: ['secret', 'dont tell'],
    isRead: true,
    isResolved: true,
  },
  {
    id: '5',
    timestamp: '2025-02-06T18:00:00Z',
    deviceId: '2',
    severity: 'low',
    category: 'new_device',
    title: 'New device connected',
    description: 'Unknown device joined the network',
    isRead: true,
    isResolved: true,
  },
];

const severityIcons = {
  critical: AlertTriangle,
  high: AlertCircle,
  medium: Info,
  low: Bell,
};

export default function Alerts() {
  const [alerts, setAlerts] = useState(mockAlerts);
  const [filter, setFilter] = useState<'all' | 'unread' | 'unresolved'>('all');
  const [selectedAlert, setSelectedAlert] = useState<Alert | null>(null);

  const filteredAlerts = alerts.filter(alert => {
    if (filter === 'unread') return !alert.isRead;
    if (filter === 'unresolved') return !alert.isResolved;
    return true;
  });

  const unreadCount = alerts.filter(a => !a.isRead).length;
  const unresolvedCount = alerts.filter(a => !a.isResolved).length;

  const markAsRead = (id: string) => {
    setAlerts(alerts.map(a => 
      a.id === id ? { ...a, isRead: true } : a
    ));
  };

  const resolveAlert = (id: string) => {
    setAlerts(alerts.map(a => 
      a.id === id ? { ...a, isResolved: true, isRead: true } : a
    ));
  };

  const deleteAlert = (id: string) => {
    setAlerts(alerts.filter(a => a.id !== id));
    if (selectedAlert?.id === id) {
      setSelectedAlert(null);
    }
  };

  const markAllRead = () => {
    setAlerts(alerts.map(a => ({ ...a, isRead: true })));
  };

  return (
    <div className="p-6 h-full flex flex-col">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold">Alerts</h1>
          <p className="text-dark-400">
            {unreadCount} unread, {unresolvedCount} unresolved
          </p>
        </div>
        <button 
          onClick={markAllRead}
          className="flex items-center gap-2 px-4 py-2 bg-dark-700 rounded-lg text-sm hover:bg-dark-600"
        >
          <Check className="w-4 h-4" />
          Mark All Read
        </button>
      </div>

      {/* Filters */}
      <div className="flex gap-2 mb-4">
        {[
          { id: 'all', label: 'All', count: alerts.length },
          { id: 'unread', label: 'Unread', count: unreadCount },
          { id: 'unresolved', label: 'Unresolved', count: unresolvedCount },
        ].map(f => (
          <button
            key={f.id}
            onClick={() => setFilter(f.id as typeof filter)}
            className={cn(
              "flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-colors",
              filter === f.id
                ? "bg-primary-600 text-white"
                : "bg-dark-700 text-dark-300 hover:bg-dark-600"
            )}
          >
            {f.label}
            <span className={cn(
              "px-1.5 py-0.5 rounded text-xs",
              filter === f.id ? "bg-white/20" : "bg-dark-600"
            )}>
              {f.count}
            </span>
          </button>
        ))}
      </div>

      {/* Content */}
      <div className="flex-1 flex gap-4 min-h-0">
        {/* Alert List */}
        <div className="flex-1 space-y-2 overflow-auto">
          {filteredAlerts.length === 0 ? (
            <div className="card p-8 text-center text-dark-400">
              <Bell className="w-12 h-12 mx-auto mb-4 opacity-50" />
              <p>No alerts to show</p>
            </div>
          ) : (
            filteredAlerts.map(alert => (
              <AlertCard
                key={alert.id}
                alert={alert}
                isSelected={selectedAlert?.id === alert.id}
                onClick={() => {
                  setSelectedAlert(alert);
                  markAsRead(alert.id);
                }}
              />
            ))
          )}
        </div>

        {/* Detail Panel */}
        {selectedAlert && (
          <div className="w-96 card flex flex-col overflow-hidden">
            <AlertDetail 
              alert={selectedAlert}
              onResolve={() => resolveAlert(selectedAlert.id)}
              onDelete={() => deleteAlert(selectedAlert.id)}
            />
          </div>
        )}
      </div>
    </div>
  );
}

function AlertCard({ 
  alert, 
  isSelected,
  onClick 
}: { 
  alert: Alert; 
  isSelected: boolean;
  onClick: () => void;
}) {
  const Icon = severityIcons[alert.severity];

  return (
    <div
      onClick={onClick}
      className={cn(
        "card-hover p-4 cursor-pointer border-l-4",
        isSelected && "border-primary-500 bg-primary-500/5",
        !isSelected && getSeverityBg(alert.severity),
        !alert.isRead && "bg-dark-700/50"
      )}
    >
      <div className="flex items-start gap-3">
        <div className={cn(
          "w-10 h-10 rounded-lg flex items-center justify-center",
          `bg-${alert.severity === 'critical' ? 'red' : alert.severity === 'high' ? 'orange' : alert.severity === 'medium' ? 'yellow' : 'blue'}-500/20`
        )}>
          <Icon className={cn("w-5 h-5", getSeverityColor(alert.severity))} />
        </div>
        
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <h3 className={cn(
              "font-medium truncate",
              !alert.isRead && "font-semibold"
            )}>
              {alert.title}
            </h3>
            {!alert.isRead && (
              <span className="w-2 h-2 rounded-full bg-primary-500" />
            )}
            {alert.isResolved && (
              <span className="bg-green-500/20 text-green-400 text-xs px-1.5 rounded">
                Resolved
              </span>
            )}
          </div>
          <p className="text-sm text-dark-400 truncate mt-0.5">
            {alert.description}
          </p>
          <div className="flex items-center gap-3 mt-2 text-xs text-dark-500">
            <span className="flex items-center gap-1">
              <Clock className="w-3 h-3" />
              {formatRelativeTime(alert.timestamp)}
            </span>
            <span className="flex items-center gap-1">
              <Tag className="w-3 h-3" />
              {alert.category.replace('_', ' ')}
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}

function AlertDetail({ 
  alert,
  onResolve,
  onDelete
}: { 
  alert: Alert;
  onResolve: () => void;
  onDelete: () => void;
}) {
  const Icon = severityIcons[alert.severity];

  return (
    <>
      <div className="p-4 border-b border-dark-700">
        <div className="flex items-center gap-3">
          <div className={cn(
            "w-12 h-12 rounded-lg flex items-center justify-center",
            getSeverityBg(alert.severity)
          )}>
            <Icon className={cn("w-6 h-6", getSeverityColor(alert.severity))} />
          </div>
          <div>
            <span className={cn(
              "text-xs font-medium uppercase",
              getSeverityColor(alert.severity)
            )}>
              {alert.severity}
            </span>
            <h2 className="font-semibold">{alert.title}</h2>
          </div>
        </div>
      </div>

      <div className="flex-1 overflow-auto p-4 space-y-4">
        <div>
          <label className="text-xs text-dark-400 uppercase">Description</label>
          <p className="mt-1">{alert.description}</p>
        </div>

        <div className="grid grid-cols-2 gap-3">
          <div className="bg-dark-700/50 rounded-lg p-3">
            <div className="text-xs text-dark-400">Category</div>
            <div className="mt-1">{alert.category.replace('_', ' ')}</div>
          </div>
          <div className="bg-dark-700/50 rounded-lg p-3">
            <div className="text-xs text-dark-400">Time</div>
            <div className="mt-1 text-sm">
              {new Date(alert.timestamp).toLocaleString()}
            </div>
          </div>
        </div>

        {alert.url && (
          <div>
            <label className="text-xs text-dark-400 uppercase">URL</label>
            <div className="mt-1 flex items-center gap-2">
              <code className="text-sm break-all flex-1 text-primary-400">
                {alert.url}
              </code>
              <a 
                href={alert.url}
                target="_blank"
                rel="noopener noreferrer"
                className="p-1.5 hover:bg-dark-700 rounded"
              >
                <ExternalLink className="w-4 h-4 text-dark-400" />
              </a>
            </div>
          </div>
        )}

        {alert.matchedKeywords && alert.matchedKeywords.length > 0 && (
          <div>
            <label className="text-xs text-dark-400 uppercase">Matched Keywords</label>
            <div className="mt-2 flex flex-wrap gap-2">
              {alert.matchedKeywords.map(kw => (
                <span 
                  key={kw}
                  className="bg-red-500/20 text-red-400 px-2 py-1 rounded text-sm"
                >
                  {kw}
                </span>
              ))}
            </div>
          </div>
        )}
      </div>

      <div className="p-4 border-t border-dark-700 flex gap-2">
        {!alert.isResolved && (
          <button 
            onClick={onResolve}
            className="flex-1 flex items-center justify-center gap-2 py-2 bg-green-600 rounded-lg text-sm hover:bg-green-700"
          >
            <Check className="w-4 h-4" />
            Resolve
          </button>
        )}
        <button 
          onClick={onDelete}
          className="flex items-center justify-center gap-2 px-4 py-2 bg-dark-700 rounded-lg text-sm hover:bg-red-600"
        >
          <Trash2 className="w-4 h-4" />
        </button>
      </div>
    </>
  );
}
