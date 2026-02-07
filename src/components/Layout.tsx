import { NavLink, Outlet } from 'react-router-dom';
import { 
  LayoutDashboard, 
  Monitor, 
  Activity, 
  Shield, 
  Bell, 
  Settings,
  Power,
  Wifi,
  WifiOff
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { useMonitoringStore, useAlertsStore } from '@/stores';

const navItems = [
  { path: '/', label: 'Dashboard', icon: LayoutDashboard },
  { path: '/devices', label: 'Devices', icon: Monitor },
  { path: '/traffic', label: 'Traffic', icon: Activity },
  { path: '/blocking', label: 'Blocking', icon: Shield },
  { path: '/alerts', label: 'Alerts', icon: Bell },
  { path: '/settings', label: 'Settings', icon: Settings },
];

export default function Layout() {
  const { status, start, stop } = useMonitoringStore();
  const { unreadCount } = useAlertsStore();

  const toggleMonitoring = async () => {
    if (status.isRunning) {
      await stop();
    } else {
      await start();
    }
  };

  return (
    <div className="flex h-screen bg-dark-900 text-dark-100">
      {/* Sidebar */}
      <aside className="w-64 bg-dark-800 border-r border-dark-700 flex flex-col">
        {/* Logo */}
        <div className="p-4 border-b border-dark-700">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-primary-600 flex items-center justify-center">
              <Activity className="w-6 h-6 text-white" />
            </div>
            <div>
              <h1 className="font-semibold text-white">Network Monitor</h1>
              <p className="text-xs text-dark-400">Stealth Mode</p>
            </div>
          </div>
        </div>

        {/* Status Card */}
        <div className="p-4 border-b border-dark-700">
          <div className={cn(
            "rounded-lg p-3 flex items-center justify-between",
            status.isRunning ? "bg-green-900/30" : "bg-dark-700"
          )}>
            <div className="flex items-center gap-2">
              {status.isRunning ? (
                <Wifi className="w-5 h-5 text-green-400" />
              ) : (
                <WifiOff className="w-5 h-5 text-dark-400" />
              )}
              <div>
                <p className="text-sm font-medium">
                  {status.isRunning ? 'Monitoring' : 'Stopped'}
                </p>
                {status.isRunning && (
                  <p className="text-xs text-dark-400">
                    {status.currentProfile}
                  </p>
                )}
              </div>
            </div>
            <button
              onClick={toggleMonitoring}
              className={cn(
                "p-2 rounded-lg transition-colors",
                status.isRunning 
                  ? "bg-red-600 hover:bg-red-700" 
                  : "bg-green-600 hover:bg-green-700"
              )}
            >
              <Power className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* Navigation */}
        <nav className="flex-1 p-2 space-y-1">
          {navItems.map((item) => (
            <NavLink
              key={item.path}
              to={item.path}
              className={({ isActive }) =>
                cn(
                  "flex items-center gap-3 px-3 py-2.5 rounded-lg transition-colors",
                  isActive
                    ? "bg-primary-600 text-white"
                    : "text-dark-300 hover:bg-dark-700 hover:text-white"
                )
              }
            >
              <item.icon className="w-5 h-5" />
              <span className="font-medium">{item.label}</span>
              {item.path === '/alerts' && unreadCount > 0 && (
                <span className="ml-auto bg-red-500 text-white text-xs font-bold px-2 py-0.5 rounded-full">
                  {unreadCount}
                </span>
              )}
            </NavLink>
          ))}
        </nav>

        {/* Footer */}
        <div className="p-4 border-t border-dark-700">
          <div className="flex items-center gap-2 text-xs text-dark-400">
            <div className={cn(
              "w-2 h-2 rounded-full",
              status.isRunning ? "bg-green-500 animate-pulse" : "bg-dark-500"
            )} />
            <span>
              {status.isRunning ? 'Capturing traffic...' : 'Not monitoring'}
            </span>
          </div>
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 overflow-auto">
        <Outlet />
      </main>
    </div>
  );
}
