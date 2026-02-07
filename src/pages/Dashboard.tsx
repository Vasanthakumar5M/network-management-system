import { useEffect } from 'react';
import { 
  Monitor, 
  Activity, 
  TrendingUp,
  AlertTriangle,
  Wifi,
  Ban,
  Eye
} from 'lucide-react';
import { 
  AreaChart, 
  Area, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  ResponsiveContainer,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell
} from 'recharts';
import { useDashboardStore } from '@/stores';
import { formatBytes } from '@/lib/utils';

const COLORS = ['#ef4444', '#f97316', '#eab308', '#22c55e', '#3b82f6'];

interface StatCardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  icon: React.ReactNode;
  trend?: { value: number; label: string };
  color?: string;
}

function StatCard({ title, value, subtitle, icon, trend, color = 'primary' }: StatCardProps) {
  return (
    <div className="card p-4">
      <div className="flex items-start justify-between">
        <div>
          <p className="text-sm text-dark-400">{title}</p>
          <p className="text-2xl font-bold mt-1">{value}</p>
          {subtitle && (
            <p className="text-xs text-dark-400 mt-1">{subtitle}</p>
          )}
          {trend && (
            <div className="flex items-center gap-1 mt-2">
              <TrendingUp className={`w-3 h-3 ${trend.value >= 0 ? 'text-green-500' : 'text-red-500'}`} />
              <span className={`text-xs ${trend.value >= 0 ? 'text-green-500' : 'text-red-500'}`}>
                {trend.value >= 0 ? '+' : ''}{trend.value}%
              </span>
              <span className="text-xs text-dark-400">{trend.label}</span>
            </div>
          )}
        </div>
        <div className={`p-3 rounded-lg bg-${color}-500/10`}>
          {icon}
        </div>
      </div>
    </div>
  );
}

export default function Dashboard() {
  const { stats, isLoading, refresh } = useDashboardStore();

  useEffect(() => {
    refresh();
    const interval = setInterval(refresh, 5000);
    return () => clearInterval(interval);
  }, [refresh]);

  if (isLoading || !stats) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-500" />
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Dashboard</h1>
          <p className="text-dark-400">Network monitoring overview</p>
        </div>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          title="Devices"
          value={`${stats.onlineDevices}/${stats.totalDevices}`}
          subtitle="online / total"
          icon={<Monitor className="w-5 h-5 text-primary-500" />}
        />
        <StatCard
          title="Requests"
          value={stats.totalRequests.toLocaleString()}
          subtitle="total captured"
          icon={<Activity className="w-5 h-5 text-green-500" />}
          color="green"
        />
        <StatCard
          title="Blocked"
          value={stats.blockedRequests.toLocaleString()}
          subtitle={`${((stats.blockedRequests / stats.totalRequests) * 100).toFixed(1)}% of traffic`}
          icon={<Ban className="w-5 h-5 text-red-500" />}
          color="red"
        />
        <StatCard
          title="Alerts"
          value={stats.unresolvedAlerts}
          subtitle={`${stats.totalAlerts} total`}
          icon={<AlertTriangle className="w-5 h-5 text-yellow-500" />}
          color="yellow"
        />
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* Traffic Over Time */}
        <div className="card p-4">
          <h3 className="font-semibold mb-4">Traffic Over Time</h3>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={stats.trafficByHour}>
                <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                <XAxis 
                  dataKey="hour" 
                  stroke="#64748b"
                  tickFormatter={(h) => `${h}:00`}
                />
                <YAxis stroke="#64748b" />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#1e293b',
                    border: '1px solid #334155',
                    borderRadius: '8px',
                  }}
                />
                <Area
                  type="monotone"
                  dataKey="requests"
                  stroke="#0ea5e9"
                  fill="#0ea5e9"
                  fillOpacity={0.2}
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Top Domains */}
        <div className="card p-4">
          <h3 className="font-semibold mb-4">Top Domains</h3>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={stats.topDomains} layout="vertical">
                <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                <XAxis type="number" stroke="#64748b" />
                <YAxis 
                  type="category" 
                  dataKey="domain" 
                  stroke="#64748b"
                  width={100}
                  tick={{ fontSize: 12 }}
                />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#1e293b',
                    border: '1px solid #334155',
                    borderRadius: '8px',
                  }}
                />
                <Bar dataKey="count" fill="#0ea5e9" radius={[0, 4, 4, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* Bottom Row */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        {/* Bandwidth */}
        <div className="card p-4">
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-semibold">Bandwidth Used</h3>
            <Eye className="w-5 h-5 text-dark-400" />
          </div>
          <div className="text-center py-8">
            <p className="text-4xl font-bold text-primary-500">
              {formatBytes(stats.totalBandwidth)}
            </p>
            <p className="text-dark-400 mt-2">Total traffic captured</p>
          </div>
        </div>

        {/* Alerts by Category */}
        <div className="card p-4">
          <h3 className="font-semibold mb-4">Alerts by Category</h3>
          <div className="h-48">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={stats.alertsByCategory}
                  dataKey="count"
                  nameKey="category"
                  cx="50%"
                  cy="50%"
                  innerRadius={40}
                  outerRadius={70}
                  paddingAngle={2}
                >
                  {stats.alertsByCategory.map((entry, index) => (
                    <Cell key={entry.category} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#1e293b',
                    border: '1px solid #334155',
                    borderRadius: '8px',
                  }}
                />
              </PieChart>
            </ResponsiveContainer>
          </div>
          <div className="flex flex-wrap gap-2 mt-2 justify-center">
            {stats.alertsByCategory.map((item, index) => (
              <div key={item.category} className="flex items-center gap-1 text-xs">
                <div 
                  className="w-2 h-2 rounded-full" 
                  style={{ backgroundColor: COLORS[index % COLORS.length] }}
                />
                <span className="text-dark-400">{item.category.replace('_', ' ')}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Status */}
        <div className="card p-4">
          <h3 className="font-semibold mb-4">Monitoring Status</h3>
          <div className="space-y-3">
            <StatusItem label="ARP Spoofing" active />
            <StatusItem label="HTTPS Proxy" active />
            <StatusItem label="DNS Capture" active />
            <StatusItem label="Stealth Mode" active />
          </div>
          <div className="mt-4 pt-4 border-t border-dark-700">
            <div className="flex items-center gap-2">
              <Wifi className="w-4 h-4 text-green-500" />
              <span className="text-sm text-dark-300">
                Disguised as <strong>HP-LaserJet-Pro</strong>
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

function StatusItem({ label, active }: { label: string; active: boolean }) {
  return (
    <div className="flex items-center justify-between">
      <span className="text-sm text-dark-300">{label}</span>
      <div className={`flex items-center gap-2 ${active ? 'text-green-500' : 'text-dark-500'}`}>
        <div className={`w-2 h-2 rounded-full ${active ? 'bg-green-500' : 'bg-dark-500'}`} />
        <span className="text-xs">{active ? 'Active' : 'Inactive'}</span>
      </div>
    </div>
  );
}
