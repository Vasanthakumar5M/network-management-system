import { useState } from 'react';
import { 
  Shield, 
  Plus, 
  Clock, 
  Globe, 
  Tag,
  Trash2,
  ToggleLeft,
  ToggleRight,
  Search
} from 'lucide-react';
import { cn } from '@/lib/utils';
import type { BlockCategory, Schedule } from '@/types';

const mockCategories: BlockCategory[] = [
  { id: 'adult', name: 'Adult Content', description: 'Pornography and explicit material', domainCount: 15000, isEnabled: true, icon: '18+' },
  { id: 'gambling', name: 'Gambling', description: 'Online casinos and betting sites', domainCount: 3200, isEnabled: true, icon: 'dice' },
  { id: 'social_media', name: 'Social Media', description: 'Instagram, TikTok, Snapchat, etc.', domainCount: 450, isEnabled: false, icon: 'users' },
  { id: 'gaming', name: 'Gaming', description: 'Online games and game stores', domainCount: 2100, isEnabled: false, icon: 'gamepad' },
  { id: 'streaming', name: 'Streaming', description: 'Netflix, YouTube, Twitch, etc.', domainCount: 380, isEnabled: false, icon: 'play' },
  { id: 'vpn_proxy', name: 'VPN & Proxy', description: 'VPN services and proxy sites', domainCount: 8900, isEnabled: true, icon: 'shield' },
  { id: 'malware', name: 'Malware & Phishing', description: 'Dangerous and malicious sites', domainCount: 50000, isEnabled: true, icon: 'alert' },
  { id: 'drugs', name: 'Drugs', description: 'Drug-related content', domainCount: 1200, isEnabled: true, icon: 'pill' },
];

const mockSchedules: Schedule[] = [
  {
    id: '1',
    name: 'School Hours',
    description: 'Block distractions during school',
    isEnabled: true,
    days: ['monday', 'tuesday', 'wednesday', 'thursday', 'friday'],
    startTime: '08:00',
    endTime: '15:00',
    categoriesToBlock: ['social_media', 'gaming', 'streaming'],
  },
  {
    id: '2',
    name: 'Bedtime',
    description: 'Block entertainment before bed',
    isEnabled: true,
    days: ['sunday', 'monday', 'tuesday', 'wednesday', 'thursday'],
    startTime: '21:00',
    endTime: '07:00',
    categoriesToBlock: ['social_media', 'gaming', 'streaming', 'forums'],
  },
  {
    id: '3',
    name: 'Homework Time',
    description: 'Focus time after school',
    isEnabled: false,
    days: ['monday', 'tuesday', 'wednesday', 'thursday', 'friday'],
    startTime: '16:00',
    endTime: '18:00',
    categoriesToBlock: ['social_media', 'gaming'],
  },
];

export default function Blocking() {
  const [activeTab, setActiveTab] = useState<'categories' | 'schedules' | 'custom'>('categories');
  const [categories, setCategories] = useState(mockCategories);
  const [schedules, setSchedules] = useState(mockSchedules);

  const toggleCategory = (id: string) => {
    setCategories(cats => 
      cats.map(c => c.id === id ? { ...c, isEnabled: !c.isEnabled } : c)
    );
  };

  const toggleSchedule = (id: string) => {
    setSchedules(scheds => 
      scheds.map(s => s.id === id ? { ...s, isEnabled: !s.isEnabled } : s)
    );
  };

  return (
    <div className="p-6 h-full flex flex-col">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold">Blocking</h1>
          <p className="text-dark-400">Manage website blocking rules</p>
        </div>
        <button className="flex items-center gap-2 px-4 py-2 bg-primary-600 rounded-lg text-sm hover:bg-primary-700">
          <Plus className="w-4 h-4" />
          Add Rule
        </button>
      </div>

      {/* Tabs */}
      <div className="flex gap-2 mb-6">
        {[
          { id: 'categories', label: 'Categories', icon: Tag },
          { id: 'schedules', label: 'Schedules', icon: Clock },
          { id: 'custom', label: 'Custom Rules', icon: Globe },
        ].map(tab => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id as typeof activeTab)}
            className={cn(
              "flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-colors",
              activeTab === tab.id
                ? "bg-primary-600 text-white"
                : "bg-dark-700 text-dark-300 hover:bg-dark-600"
            )}
          >
            <tab.icon className="w-4 h-4" />
            {tab.label}
          </button>
        ))}
      </div>

      {/* Content */}
      <div className="flex-1 overflow-auto">
        {activeTab === 'categories' && (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {categories.map(category => (
              <CategoryCard
                key={category.id}
                category={category}
                onToggle={() => toggleCategory(category.id)}
              />
            ))}
          </div>
        )}

        {activeTab === 'schedules' && (
          <div className="space-y-4">
            {schedules.map(schedule => (
              <ScheduleCard
                key={schedule.id}
                schedule={schedule}
                onToggle={() => toggleSchedule(schedule.id)}
              />
            ))}
          </div>
        )}

        {activeTab === 'custom' && (
          <CustomRules />
        )}
      </div>
    </div>
  );
}

function CategoryCard({ 
  category, 
  onToggle 
}: { 
  category: BlockCategory; 
  onToggle: () => void;
}) {
  return (
    <div className={cn(
      "card p-4",
      category.isEnabled && "border-primary-500/50"
    )}>
      <div className="flex items-start justify-between">
        <div className="flex items-start gap-3">
          <div className={cn(
            "w-10 h-10 rounded-lg flex items-center justify-center text-lg",
            category.isEnabled ? "bg-primary-500/20" : "bg-dark-700"
          )}>
            <Shield className={cn(
              "w-5 h-5",
              category.isEnabled ? "text-primary-500" : "text-dark-500"
            )} />
          </div>
          <div>
            <h3 className="font-medium">{category.name}</h3>
            <p className="text-sm text-dark-400 mt-0.5">{category.description}</p>
            <p className="text-xs text-dark-500 mt-1">
              {category.domainCount.toLocaleString()} domains
            </p>
          </div>
        </div>
        <button onClick={onToggle}>
          {category.isEnabled ? (
            <ToggleRight className="w-8 h-8 text-primary-500" />
          ) : (
            <ToggleLeft className="w-8 h-8 text-dark-500" />
          )}
        </button>
      </div>
    </div>
  );
}

function ScheduleCard({ 
  schedule, 
  onToggle 
}: { 
  schedule: Schedule; 
  onToggle: () => void;
}) {
  const dayAbbrevs: Record<string, string> = {
    monday: 'Mon',
    tuesday: 'Tue',
    wednesday: 'Wed',
    thursday: 'Thu',
    friday: 'Fri',
    saturday: 'Sat',
    sunday: 'Sun',
  };

  return (
    <div className={cn(
      "card p-4",
      schedule.isEnabled && "border-green-500/50"
    )}>
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <div className="flex items-center gap-3">
            <div className={cn(
              "w-10 h-10 rounded-lg flex items-center justify-center",
              schedule.isEnabled ? "bg-green-500/20" : "bg-dark-700"
            )}>
              <Clock className={cn(
                "w-5 h-5",
                schedule.isEnabled ? "text-green-500" : "text-dark-500"
              )} />
            </div>
            <div>
              <h3 className="font-medium">{schedule.name}</h3>
              <p className="text-sm text-dark-400">{schedule.description}</p>
            </div>
          </div>
          
          <div className="mt-4 flex flex-wrap gap-4">
            <div>
              <span className="text-xs text-dark-400">Days</span>
              <div className="flex gap-1 mt-1">
                {['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday'].map(day => (
                  <span
                    key={day}
                    className={cn(
                      "w-8 h-6 rounded text-xs flex items-center justify-center",
                      schedule.days.includes(day)
                        ? "bg-primary-500/20 text-primary-400"
                        : "bg-dark-700 text-dark-500"
                    )}
                  >
                    {dayAbbrevs[day].charAt(0)}
                  </span>
                ))}
              </div>
            </div>
            
            <div>
              <span className="text-xs text-dark-400">Time</span>
              <p className="text-sm font-mono mt-1">
                {schedule.startTime} - {schedule.endTime}
              </p>
            </div>
            
            <div>
              <span className="text-xs text-dark-400">Blocks</span>
              <div className="flex gap-1 mt-1 flex-wrap">
                {schedule.categoriesToBlock.map(cat => (
                  <span key={cat} className="bg-red-500/20 text-red-400 text-xs px-2 py-0.5 rounded">
                    {cat.replace('_', ' ')}
                  </span>
                ))}
              </div>
            </div>
          </div>
        </div>
        
        <button onClick={onToggle}>
          {schedule.isEnabled ? (
            <ToggleRight className="w-8 h-8 text-green-500" />
          ) : (
            <ToggleLeft className="w-8 h-8 text-dark-500" />
          )}
        </button>
      </div>
    </div>
  );
}

function CustomRules() {
  const [customDomains] = useState([
    'reddit.com',
    'discord.com',
    'twitch.tv',
  ]);

  return (
    <div className="space-y-4">
      {/* Add Domain */}
      <div className="card p-4">
        <div className="flex gap-3">
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-dark-400" />
            <input
              type="text"
              placeholder="Enter domain to block (e.g., example.com)"
              className="w-full pl-10 pr-4 py-2 bg-dark-700 border border-dark-600 rounded-lg text-sm focus:outline-none focus:border-primary-500"
            />
          </div>
          <button className="px-4 py-2 bg-red-600 rounded-lg text-sm hover:bg-red-700">
            Block
          </button>
        </div>
      </div>

      {/* Domain List */}
      <div className="card overflow-hidden">
        <div className="px-4 py-3 bg-dark-700/50 text-sm font-medium text-dark-400">
          Custom Blocked Domains ({customDomains.length})
        </div>
        <div className="divide-y divide-dark-700">
          {customDomains.map(domain => (
            <div key={domain} className="flex items-center justify-between px-4 py-3">
              <div className="flex items-center gap-3">
                <Globe className="w-4 h-4 text-dark-500" />
                <span className="font-mono">{domain}</span>
              </div>
              <button className="p-1.5 hover:bg-dark-700 rounded text-dark-400 hover:text-red-500">
                <Trash2 className="w-4 h-4" />
              </button>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
