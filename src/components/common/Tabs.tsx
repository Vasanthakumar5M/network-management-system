import { useState, type ReactNode } from 'react';
import { cn } from '@/lib/utils';

export interface Tab {
  id: string;
  label: string;
  icon?: ReactNode;
  disabled?: boolean;
  badge?: string | number;
}

export interface TabsProps {
  tabs: Tab[];
  activeTab: string;
  onChange: (tabId: string) => void;
  variant?: 'default' | 'pills' | 'underline';
  size?: 'sm' | 'md' | 'lg';
  className?: string;
  fullWidth?: boolean;
}

export function Tabs({
  tabs,
  activeTab,
  onChange,
  variant = 'default',
  size = 'md',
  className,
  fullWidth = false,
}: TabsProps) {
  const baseTabStyles =
    'inline-flex items-center justify-center gap-2 font-medium transition-all duration-200 focus:outline-none';

  const variants = {
    default: {
      container: 'bg-gray-800/50 rounded-lg p-1',
      tab: 'rounded-md',
      active: 'bg-gray-700 text-white shadow-sm',
      inactive: 'text-gray-400 hover:text-white hover:bg-gray-700/50',
    },
    pills: {
      container: 'gap-2',
      tab: 'rounded-full',
      active: 'bg-blue-600 text-white',
      inactive: 'text-gray-400 hover:text-white hover:bg-gray-700',
    },
    underline: {
      container: 'border-b border-gray-700 gap-4',
      tab: 'border-b-2 -mb-px',
      active: 'text-blue-400 border-blue-400',
      inactive: 'text-gray-400 border-transparent hover:text-white hover:border-gray-500',
    },
  };

  const sizes = {
    sm: 'px-3 py-1.5 text-xs',
    md: 'px-4 py-2 text-sm',
    lg: 'px-5 py-2.5 text-base',
  };

  const variantStyles = variants[variant];

  return (
    <div
      className={cn(
        'flex',
        variantStyles.container,
        fullWidth && 'w-full',
        className
      )}
      role="tablist"
    >
      {tabs.map((tab) => (
        <button
          key={tab.id}
          type="button"
          role="tab"
          aria-selected={activeTab === tab.id}
          aria-disabled={tab.disabled}
          onClick={() => !tab.disabled && onChange(tab.id)}
          className={cn(
            baseTabStyles,
            variantStyles.tab,
            sizes[size],
            activeTab === tab.id ? variantStyles.active : variantStyles.inactive,
            tab.disabled && 'opacity-50 cursor-not-allowed',
            fullWidth && 'flex-1'
          )}
        >
          {tab.icon}
          <span>{tab.label}</span>
          {tab.badge !== undefined && (
            <span
              className={cn(
                'ml-1 px-1.5 py-0.5 rounded-full text-xs font-medium',
                activeTab === tab.id
                  ? 'bg-white/20 text-white'
                  : 'bg-gray-600 text-gray-300'
              )}
            >
              {tab.badge}
            </span>
          )}
        </button>
      ))}
    </div>
  );
}

// Tab panel component for content
export interface TabPanelProps {
  id: string;
  activeTab: string;
  children: ReactNode;
  className?: string;
}

export function TabPanel({ id, activeTab, children, className }: TabPanelProps) {
  if (activeTab !== id) return null;

  return (
    <div
      role="tabpanel"
      aria-labelledby={id}
      className={cn('focus:outline-none', className)}
    >
      {children}
    </div>
  );
}

// Hook for managing tab state
export function useTabs(defaultTab: string) {
  const [activeTab, setActiveTab] = useState(defaultTab);

  return {
    activeTab,
    setActiveTab,
    isActive: (tabId: string) => activeTab === tabId,
  };
}
