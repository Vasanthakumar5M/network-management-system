// Device types
export interface Device {
  id: string;
  mac: string;
  ip: string;
  hostname: string;
  vendor: string;
  deviceType: string;
  firstSeen: string;
  lastSeen: string;
  isOnline: boolean;
  isMonitored: boolean;
  totalBytes: number;
  blockedRequests: number;
  alerts: number;
}

// Traffic types
export interface TrafficEntry {
  id: string;
  timestamp: string;
  deviceId: string;
  deviceIp: string;
  method: 'GET' | 'POST' | 'PUT' | 'DELETE' | 'PATCH' | 'OPTIONS' | 'HEAD';
  url: string;
  host: string;
  path: string;
  statusCode: number;
  contentType: string;
  requestSize: number;
  responseSize: number;
  duration: number;
  isBlocked: boolean;
  hasAlert: boolean;
  category: string;
  requestHeaders?: Record<string, string>;
  responseHeaders?: Record<string, string>;
  requestBody?: string;
  responseBody?: string;
}

// DNS types
export interface DNSQuery {
  id: string;
  timestamp: string;
  deviceId: string;
  deviceIp: string;
  queryType: string;
  domain: string;
  resolvedIps: string[];
  isBlocked: boolean;
  responseTime: number;
}

// Alert types
export type AlertSeverity = 'critical' | 'high' | 'medium' | 'low';
export type AlertCategory = 
  | 'self_harm'
  | 'suicide'
  | 'predator_grooming'
  | 'bullying'
  | 'drugs'
  | 'violence'
  | 'adult_content'
  | 'vpn_detected'
  | 'blocked_attempt'
  | 'new_device';

export interface Alert {
  id: string;
  timestamp: string;
  deviceId: string;
  severity: AlertSeverity;
  category: AlertCategory;
  title: string;
  description: string;
  url?: string;
  matchedKeywords?: string[];
  isRead: boolean;
  isResolved: boolean;
}

// Blocking types
export interface BlockRule {
  id: string;
  type: 'domain' | 'category' | 'keyword' | 'ip';
  value: string;
  isEnabled: boolean;
  deviceIds?: string[]; // empty = all devices
  scheduleId?: string;
  createdAt: string;
}

export interface BlockCategory {
  id: string;
  name: string;
  description: string;
  domainCount: number;
  isEnabled: boolean;
  icon: string;
}

export interface Schedule {
  id: string;
  name: string;
  description: string;
  isEnabled: boolean;
  days: string[];
  startTime: string;
  endTime: string;
  categoriesToBlock: string[];
}

// Stats types
export interface DashboardStats {
  totalDevices: number;
  onlineDevices: number;
  totalRequests: number;
  blockedRequests: number;
  totalAlerts: number;
  unresolvedAlerts: number;
  totalBandwidth: number;
  topDomains: { domain: string; count: number }[];
  trafficByHour: { hour: number; requests: number }[];
  alertsByCategory: { category: string; count: number }[];
}

// Monitoring status
export interface MonitoringStatus {
  isRunning: boolean;
  arpSpoofing: boolean;
  httpsProxy: boolean;
  dnsCapture: boolean;
  stealthMode: boolean;
  currentProfile: string;
  uptime: number;
  errors: string[];
}

// Settings types
export interface AppSettings {
  theme: 'dark' | 'light' | 'system';
  language: string;
  refreshInterval: number;
  showRawData: boolean;
  blurPasswords: boolean;
  hidesSensitiveData: boolean;
  notifications: {
    desktop: boolean;
    sound: boolean;
    email: boolean;
  };
  stealth: {
    enabled: boolean;
    deviceProfile: string;
    changeMac: boolean;
    changeHostname: boolean;
  };
}
