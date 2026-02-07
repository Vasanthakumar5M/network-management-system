import { useState } from 'react';
import { 
  Settings as SettingsIcon,
  Eye,
  Shield,
  Bell,
  Database,
  Palette,
  Key,
  Wifi,
  Save,
  RotateCcw
} from 'lucide-react';
import { cn } from '@/lib/utils';

interface SettingsSection {
  id: string;
  label: string;
  icon: React.ElementType;
}

const sections: SettingsSection[] = [
  { id: 'general', label: 'General', icon: SettingsIcon },
  { id: 'stealth', label: 'Stealth Mode', icon: Eye },
  { id: 'blocking', label: 'Blocking', icon: Shield },
  { id: 'alerts', label: 'Alerts & Notifications', icon: Bell },
  { id: 'database', label: 'Database', icon: Database },
  { id: 'appearance', label: 'Appearance', icon: Palette },
  { id: 'certificates', label: 'Certificates', icon: Key },
  { id: 'network', label: 'Network', icon: Wifi },
];

export default function Settings() {
  const [activeSection, setActiveSection] = useState('general');
  const [hasChanges, setHasChanges] = useState(false);

  const handleChange = () => {
    setHasChanges(true);
  };

  const handleSave = () => {
    // TODO: Save settings
    setHasChanges(false);
  };

  const handleReset = () => {
    // TODO: Reset to defaults
    setHasChanges(false);
  };

  return (
    <div className="p-6 h-full flex flex-col">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold">Settings</h1>
          <p className="text-dark-400">Configure application settings</p>
        </div>
        {hasChanges && (
          <div className="flex gap-2">
            <button 
              onClick={handleReset}
              className="flex items-center gap-2 px-4 py-2 bg-dark-700 rounded-lg text-sm hover:bg-dark-600"
            >
              <RotateCcw className="w-4 h-4" />
              Reset
            </button>
            <button 
              onClick={handleSave}
              className="flex items-center gap-2 px-4 py-2 bg-primary-600 rounded-lg text-sm hover:bg-primary-700"
            >
              <Save className="w-4 h-4" />
              Save Changes
            </button>
          </div>
        )}
      </div>

      {/* Content */}
      <div className="flex-1 flex gap-6 min-h-0">
        {/* Sidebar */}
        <div className="w-56 space-y-1">
          {sections.map(section => (
            <button
              key={section.id}
              onClick={() => setActiveSection(section.id)}
              className={cn(
                "w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors text-left",
                activeSection === section.id
                  ? "bg-primary-600 text-white"
                  : "text-dark-300 hover:bg-dark-700"
              )}
            >
              <section.icon className="w-5 h-5" />
              {section.label}
            </button>
          ))}
        </div>

        {/* Settings Panel */}
        <div className="flex-1 card p-6 overflow-auto">
          {activeSection === 'general' && <GeneralSettings onChange={handleChange} />}
          {activeSection === 'stealth' && <StealthSettings onChange={handleChange} />}
          {activeSection === 'blocking' && <BlockingSettings onChange={handleChange} />}
          {activeSection === 'alerts' && <AlertSettings onChange={handleChange} />}
          {activeSection === 'database' && <DatabaseSettings />}
          {activeSection === 'appearance' && <AppearanceSettings onChange={handleChange} />}
          {activeSection === 'certificates' && <CertificateSettings />}
          {activeSection === 'network' && <NetworkSettings />}
        </div>
      </div>
    </div>
  );
}

function GeneralSettings({ onChange }: { onChange: () => void }) {
  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-lg font-semibold mb-4">General Settings</h2>
        <div className="space-y-4">
          <ToggleSetting
            label="Run on startup"
            description="Start Network Monitor when Windows starts"
            defaultChecked={false}
            onChange={onChange}
          />
          <ToggleSetting
            label="Minimize to tray"
            description="Keep running in system tray when closed"
            defaultChecked={true}
            onChange={onChange}
          />
          <ToggleSetting
            label="Check for updates"
            description="Automatically check for new versions"
            defaultChecked={false}
            onChange={onChange}
          />
        </div>
      </div>

      <div>
        <h3 className="font-medium mb-3">Privacy</h3>
        <div className="space-y-4">
          <ToggleSetting
            label="Blur passwords"
            description="Hide password fields in captured traffic"
            defaultChecked={true}
            onChange={onChange}
          />
          <ToggleSetting
            label="Hide sensitive data"
            description="Mask credit card numbers, SSN, etc."
            defaultChecked={true}
            onChange={onChange}
          />
          <ToggleSetting
            label="Local only"
            description="Never send data to external servers"
            defaultChecked={true}
            onChange={onChange}
          />
        </div>
      </div>
    </div>
  );
}

function StealthSettings({ onChange }: { onChange: () => void }) {
  const profiles = [
    { id: 'hp_printer', name: 'HP Printer', mac: '3C:D9:2B:XX:XX:XX' },
    { id: 'samsung_tv', name: 'Samsung Smart TV', mac: '8C:79:F5:XX:XX:XX' },
    { id: 'roku', name: 'Roku Streaming', mac: 'D8:31:34:XX:XX:XX' },
    { id: 'nest', name: 'Nest Thermostat', mac: '64:16:66:XX:XX:XX' },
    { id: 'sonos', name: 'Sonos Speaker', mac: '78:28:CA:XX:XX:XX' },
  ];

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-lg font-semibold mb-4">Stealth Mode</h2>
        <p className="text-dark-400 mb-4">
          Disguise this computer as a different device on the network.
        </p>
        
        <ToggleSetting
          label="Enable stealth mode"
          description="Change MAC address and hostname to appear as a different device"
          defaultChecked={true}
          onChange={onChange}
        />
      </div>

      <div>
        <h3 className="font-medium mb-3">Device Profile</h3>
        <div className="space-y-2">
          {profiles.map(profile => (
            <label 
              key={profile.id}
              className="flex items-center gap-3 p-3 bg-dark-700/50 rounded-lg cursor-pointer hover:bg-dark-700"
            >
              <input
                type="radio"
                name="profile"
                value={profile.id}
                defaultChecked={profile.id === 'hp_printer'}
                onChange={onChange}
                className="w-4 h-4 text-primary-600"
              />
              <div>
                <p className="font-medium">{profile.name}</p>
                <p className="text-xs text-dark-400 font-mono">{profile.mac}</p>
              </div>
            </label>
          ))}
        </div>
      </div>

      <div className="space-y-4">
        <ToggleSetting
          label="Change MAC address"
          description="Spoof the network adapter MAC address"
          defaultChecked={true}
          onChange={onChange}
        />
        <ToggleSetting
          label="Change hostname"
          description="Change the computer's network name"
          defaultChecked={true}
          onChange={onChange}
        />
        <ToggleSetting
          label="Randomize on start"
          description="Use a random profile each time the app starts"
          defaultChecked={false}
          onChange={onChange}
        />
      </div>
    </div>
  );
}

function BlockingSettings({ onChange }: { onChange: () => void }) {
  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-lg font-semibold mb-4">Blocking Settings</h2>
        
        <div className="space-y-4">
          <ToggleSetting
            label="Enable blocking"
            description="Block access to configured sites and categories"
            defaultChecked={true}
            onChange={onChange}
          />
          <ToggleSetting
            label="Log blocked requests"
            description="Record all blocked access attempts"
            defaultChecked={true}
            onChange={onChange}
          />
          <ToggleSetting
            label="Show block page"
            description="Display a custom page when access is blocked"
            defaultChecked={true}
            onChange={onChange}
          />
        </div>
      </div>

      <div>
        <label className="block text-sm font-medium mb-2">Block page message</label>
        <textarea
          className="w-full px-3 py-2 bg-dark-700 border border-dark-600 rounded-lg text-sm resize-none"
          rows={3}
          defaultValue="This website is not available."
          onChange={onChange}
        />
      </div>
    </div>
  );
}

function AlertSettings({ onChange }: { onChange: () => void }) {
  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-lg font-semibold mb-4">Alerts & Notifications</h2>
        
        <div className="space-y-4">
          <ToggleSetting
            label="Desktop notifications"
            description="Show Windows notifications for alerts"
            defaultChecked={true}
            onChange={onChange}
          />
          <ToggleSetting
            label="Sound alerts"
            description="Play a sound for critical alerts"
            defaultChecked={true}
            onChange={onChange}
          />
          <ToggleSetting
            label="Email notifications"
            description="Send email for critical alerts"
            defaultChecked={false}
            onChange={onChange}
          />
        </div>
      </div>

      <div>
        <h3 className="font-medium mb-3">Alert Categories</h3>
        <div className="space-y-2">
          {[
            { id: 'self_harm', label: 'Self-harm keywords', severity: 'critical' },
            { id: 'predator', label: 'Predator grooming', severity: 'critical' },
            { id: 'bullying', label: 'Bullying keywords', severity: 'high' },
            { id: 'drugs', label: 'Drug-related', severity: 'high' },
            { id: 'vpn', label: 'VPN usage', severity: 'medium' },
          ].map(cat => (
            <div key={cat.id} className="flex items-center justify-between p-3 bg-dark-700/50 rounded-lg">
              <div className="flex items-center gap-3">
                <input
                  type="checkbox"
                  defaultChecked
                  onChange={onChange}
                  className="w-4 h-4 text-primary-600 rounded"
                />
                <span>{cat.label}</span>
              </div>
              <span className={cn(
                "text-xs px-2 py-0.5 rounded",
                cat.severity === 'critical' && "bg-red-500/20 text-red-400",
                cat.severity === 'high' && "bg-orange-500/20 text-orange-400",
                cat.severity === 'medium' && "bg-yellow-500/20 text-yellow-400"
              )}>
                {cat.severity}
              </span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

function DatabaseSettings() {
  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-lg font-semibold mb-4">Database</h2>
        
        <div className="grid grid-cols-2 gap-4 mb-6">
          <div className="bg-dark-700/50 rounded-lg p-4">
            <div className="text-dark-400 text-sm">Database Size</div>
            <div className="text-2xl font-bold mt-1">1.2 GB</div>
          </div>
          <div className="bg-dark-700/50 rounded-lg p-4">
            <div className="text-dark-400 text-sm">Total Records</div>
            <div className="text-2xl font-bold mt-1">45,231</div>
          </div>
        </div>

        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium mb-2">Retention period</label>
            <select className="w-full px-3 py-2 bg-dark-700 border border-dark-600 rounded-lg text-sm">
              <option>30 days</option>
              <option>60 days</option>
              <option>90 days</option>
              <option>180 days</option>
              <option>1 year</option>
              <option>Forever</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium mb-2">Max database size</label>
            <select className="w-full px-3 py-2 bg-dark-700 border border-dark-600 rounded-lg text-sm">
              <option>1 GB</option>
              <option>2 GB</option>
              <option>5 GB</option>
              <option>10 GB</option>
              <option>Unlimited</option>
            </select>
          </div>
        </div>
      </div>

      <div className="flex gap-3">
        <button className="px-4 py-2 bg-dark-700 rounded-lg text-sm hover:bg-dark-600">
          Export Database
        </button>
        <button className="px-4 py-2 bg-dark-700 rounded-lg text-sm hover:bg-dark-600">
          Backup Now
        </button>
        <button className="px-4 py-2 bg-red-600/20 text-red-400 rounded-lg text-sm hover:bg-red-600/30">
          Clear All Data
        </button>
      </div>
    </div>
  );
}

function AppearanceSettings({ onChange }: { onChange: () => void }) {
  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-lg font-semibold mb-4">Appearance</h2>
        
        <div>
          <label className="block text-sm font-medium mb-2">Theme</label>
          <div className="flex gap-3">
            {['dark', 'light', 'system'].map(theme => (
              <label 
                key={theme}
                className="flex-1 flex items-center justify-center gap-2 p-3 bg-dark-700/50 rounded-lg cursor-pointer hover:bg-dark-700"
              >
                <input
                  type="radio"
                  name="theme"
                  value={theme}
                  defaultChecked={theme === 'dark'}
                  onChange={onChange}
                  className="sr-only"
                />
                <span className="capitalize">{theme}</span>
              </label>
            ))}
          </div>
        </div>

        <div className="mt-4">
          <label className="block text-sm font-medium mb-2">Refresh interval</label>
          <select 
            className="w-full px-3 py-2 bg-dark-700 border border-dark-600 rounded-lg text-sm"
            onChange={onChange}
          >
            <option>1 second</option>
            <option>2 seconds</option>
            <option>5 seconds</option>
            <option>10 seconds</option>
          </select>
        </div>
      </div>
    </div>
  );
}

function CertificateSettings() {
  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-lg font-semibold mb-4">Certificates</h2>
        
        <div className="bg-dark-700/50 rounded-lg p-4 mb-4">
          <div className="flex items-center justify-between mb-2">
            <span className="font-medium">Current CA Certificate</span>
            <span className="text-green-500 text-sm">Valid</span>
          </div>
          <div className="text-sm text-dark-400 space-y-1">
            <p>Profile: Google Trust Services LLC</p>
            <p>Expires: Feb 7, 2026</p>
            <p className="font-mono text-xs">SHA256: 3D:2F:...</p>
          </div>
        </div>

        <div className="flex gap-3">
          <button className="px-4 py-2 bg-primary-600 rounded-lg text-sm hover:bg-primary-700">
            Regenerate Certificate
          </button>
          <button className="px-4 py-2 bg-dark-700 rounded-lg text-sm hover:bg-dark-600">
            Export Certificate
          </button>
        </div>
      </div>

      <div>
        <h3 className="font-medium mb-3">Certificate Installer</h3>
        <div className="bg-dark-700/50 rounded-lg p-4">
          <p className="text-sm text-dark-400 mb-3">
            Share this URL with devices to install the certificate:
          </p>
          <div className="flex gap-2">
            <input
              type="text"
              readOnly
              value="http://192.168.1.100:8888"
              className="flex-1 px-3 py-2 bg-dark-800 border border-dark-600 rounded-lg text-sm font-mono"
            />
            <button className="px-4 py-2 bg-dark-700 rounded-lg text-sm hover:bg-dark-600">
              Copy
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

function NetworkSettings() {
  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-lg font-semibold mb-4">Network</h2>
        
        <div className="bg-dark-700/50 rounded-lg p-4 mb-4">
          <div className="text-sm space-y-2">
            <div className="flex justify-between">
              <span className="text-dark-400">Interface</span>
              <span>Ethernet (Intel I219-V)</span>
            </div>
            <div className="flex justify-between">
              <span className="text-dark-400">Local IP</span>
              <span className="font-mono">192.168.1.100</span>
            </div>
            <div className="flex justify-between">
              <span className="text-dark-400">Gateway</span>
              <span className="font-mono">192.168.1.1</span>
            </div>
            <div className="flex justify-between">
              <span className="text-dark-400">MAC Address</span>
              <span className="font-mono">3C:D9:2B:12:34:56</span>
            </div>
          </div>
        </div>

        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium mb-2">Proxy Port</label>
            <input
              type="number"
              defaultValue={8080}
              className="w-32 px-3 py-2 bg-dark-700 border border-dark-600 rounded-lg text-sm"
            />
          </div>
          <div>
            <label className="block text-sm font-medium mb-2">Certificate Installer Port</label>
            <input
              type="number"
              defaultValue={8888}
              className="w-32 px-3 py-2 bg-dark-700 border border-dark-600 rounded-lg text-sm"
            />
          </div>
        </div>
      </div>
    </div>
  );
}

function ToggleSetting({ 
  label, 
  description, 
  defaultChecked,
  onChange
}: { 
  label: string; 
  description: string; 
  defaultChecked: boolean;
  onChange: () => void;
}) {
  const [checked, setChecked] = useState(defaultChecked);

  return (
    <div className="flex items-center justify-between">
      <div>
        <p className="font-medium">{label}</p>
        <p className="text-sm text-dark-400">{description}</p>
      </div>
      <button
        onClick={() => {
          setChecked(!checked);
          onChange();
        }}
        className="relative"
      >
        <div className={cn(
          "w-12 h-6 rounded-full transition-colors",
          checked ? "bg-primary-600" : "bg-dark-600"
        )}>
          <div className={cn(
            "absolute top-1 w-4 h-4 rounded-full bg-white transition-transform",
            checked ? "translate-x-7" : "translate-x-1"
          )} />
        </div>
      </button>
    </div>
  );
}
