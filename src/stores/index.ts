import { create } from 'zustand';
import type { 
  Device, 
  TrafficEntry, 
  Alert, 
  MonitoringStatus,
  DashboardStats 
} from '@/types';

// ============================================
// Monitoring Store
// ============================================
interface MonitoringStore {
  status: MonitoringStatus;
  setStatus: (status: Partial<MonitoringStatus>) => void;
  start: () => Promise<void>;
  stop: () => Promise<void>;
}

export const useMonitoringStore = create<MonitoringStore>((set) => ({
  status: {
    isRunning: false,
    arpSpoofing: false,
    httpsProxy: false,
    dnsCapture: false,
    stealthMode: false,
    currentProfile: 'hp_printer',
    uptime: 0,
    errors: [],
  },
  setStatus: (newStatus) => set((state) => ({ 
    status: { ...state.status, ...newStatus } 
  })),
  start: async () => {
    // TODO: Call Tauri command to start monitoring
    set((state) => ({
      status: {
        ...state.status,
        isRunning: true,
        arpSpoofing: true,
        httpsProxy: true,
        dnsCapture: true,
      }
    }));
  },
  stop: async () => {
    // TODO: Call Tauri command to stop monitoring
    set((state) => ({
      status: {
        ...state.status,
        isRunning: false,
        arpSpoofing: false,
        httpsProxy: false,
        dnsCapture: false,
      }
    }));
  },
}));

// ============================================
// Devices Store
// ============================================
interface DevicesStore {
  devices: Device[];
  selectedDeviceId: string | null;
  isLoading: boolean;
  setDevices: (devices: Device[]) => void;
  addDevice: (device: Device) => void;
  updateDevice: (id: string, data: Partial<Device>) => void;
  selectDevice: (id: string | null) => void;
  refresh: () => Promise<void>;
}

export const useDevicesStore = create<DevicesStore>((set) => ({
  devices: [],
  selectedDeviceId: null,
  isLoading: false,
  setDevices: (devices) => set({ devices }),
  addDevice: (device) => set((state) => ({ 
    devices: [...state.devices, device] 
  })),
  updateDevice: (id, data) => set((state) => ({
    devices: state.devices.map((d) => 
      d.id === id ? { ...d, ...data } : d
    ),
  })),
  selectDevice: (id) => set({ selectedDeviceId: id }),
  refresh: async () => {
    set({ isLoading: true });
    // TODO: Call Tauri command to get devices
    set({ isLoading: false });
  },
}));

// ============================================
// Traffic Store
// ============================================
interface TrafficStore {
  entries: TrafficEntry[];
  selectedEntryId: string | null;
  filter: {
    search: string;
    method: string | null;
    statusCode: string | null;
    deviceId: string | null;
    isBlocked: boolean | null;
    hasAlert: boolean | null;
  };
  isLoading: boolean;
  setEntries: (entries: TrafficEntry[]) => void;
  addEntry: (entry: TrafficEntry) => void;
  selectEntry: (id: string | null) => void;
  setFilter: (filter: Partial<TrafficStore['filter']>) => void;
  clearFilter: () => void;
  refresh: () => Promise<void>;
}

export const useTrafficStore = create<TrafficStore>((set) => ({
  entries: [],
  selectedEntryId: null,
  filter: {
    search: '',
    method: null,
    statusCode: null,
    deviceId: null,
    isBlocked: null,
    hasAlert: null,
  },
  isLoading: false,
  setEntries: (entries) => set({ entries }),
  addEntry: (entry) => set((state) => ({ 
    entries: [entry, ...state.entries].slice(0, 1000) // Keep last 1000
  })),
  selectEntry: (id) => set({ selectedEntryId: id }),
  setFilter: (newFilter) => set((state) => ({
    filter: { ...state.filter, ...newFilter }
  })),
  clearFilter: () => set({
    filter: {
      search: '',
      method: null,
      statusCode: null,
      deviceId: null,
      isBlocked: null,
      hasAlert: null,
    }
  }),
  refresh: async () => {
    set({ isLoading: true });
    // TODO: Call Tauri command to get traffic
    set({ isLoading: false });
  },
}));

// ============================================
// Alerts Store
// ============================================
interface AlertsStore {
  alerts: Alert[];
  unreadCount: number;
  isLoading: boolean;
  setAlerts: (alerts: Alert[]) => void;
  addAlert: (alert: Alert) => void;
  markAsRead: (id: string) => void;
  markAllAsRead: () => void;
  resolveAlert: (id: string) => void;
  deleteAlert: (id: string) => void;
  refresh: () => Promise<void>;
}

export const useAlertsStore = create<AlertsStore>((set) => ({
  alerts: [],
  unreadCount: 0,
  isLoading: false,
  setAlerts: (alerts) => set({ 
    alerts,
    unreadCount: alerts.filter(a => !a.isRead).length 
  }),
  addAlert: (alert) => set((state) => {
    const newAlerts = [alert, ...state.alerts];
    return { 
      alerts: newAlerts,
      unreadCount: newAlerts.filter(a => !a.isRead).length
    };
  }),
  markAsRead: (id) => set((state) => {
    const alerts = state.alerts.map((a) =>
      a.id === id ? { ...a, isRead: true } : a
    );
    return { 
      alerts,
      unreadCount: alerts.filter(a => !a.isRead).length
    };
  }),
  markAllAsRead: () => set((state) => ({
    alerts: state.alerts.map((a) => ({ ...a, isRead: true })),
    unreadCount: 0,
  })),
  resolveAlert: (id) => set((state) => ({
    alerts: state.alerts.map((a) =>
      a.id === id ? { ...a, isResolved: true } : a
    ),
  })),
  deleteAlert: (id) => set((state) => {
    const alerts = state.alerts.filter((a) => a.id !== id);
    return {
      alerts,
      unreadCount: alerts.filter(a => !a.isRead).length,
    };
  }),
  refresh: async () => {
    set({ isLoading: true });
    // TODO: Call Tauri command to get alerts
    set({ isLoading: false });
  },
}));

// ============================================
// Dashboard Store
// ============================================
interface DashboardStore {
  stats: DashboardStats | null;
  isLoading: boolean;
  refresh: () => Promise<void>;
}

export const useDashboardStore = create<DashboardStore>((set) => ({
  stats: null,
  isLoading: false,
  refresh: async () => {
    set({ isLoading: true });
    // TODO: Call Tauri command to get stats
    // For now, use mock data
    set({
      stats: {
        totalDevices: 8,
        onlineDevices: 5,
        totalRequests: 15420,
        blockedRequests: 342,
        totalAlerts: 12,
        unresolvedAlerts: 3,
        totalBandwidth: 2.5 * 1024 * 1024 * 1024,
        topDomains: [
          { domain: 'youtube.com', count: 1234 },
          { domain: 'instagram.com', count: 987 },
          { domain: 'tiktok.com', count: 756 },
          { domain: 'google.com', count: 654 },
          { domain: 'discord.com', count: 432 },
        ],
        trafficByHour: Array.from({ length: 24 }, (_, i) => ({
          hour: i,
          requests: Math.floor(Math.random() * 1000),
        })),
        alertsByCategory: [
          { category: 'adult_content', count: 5 },
          { category: 'social_media', count: 3 },
          { category: 'gaming', count: 2 },
          { category: 'vpn_detected', count: 2 },
        ],
      },
      isLoading: false,
    });
  },
}));
