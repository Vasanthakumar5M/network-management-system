/**
 * MAC Spoofer component for manual MAC address changes
 */

import { useState } from 'react';
import { Button } from '@/components/common/Button';
import { Input } from '@/components/common/Input';
import { Modal } from '@/components/common/Modal';
import { Dropdown } from '@/components/common/Dropdown';
import { Card } from '@/components/common/Card';

export interface NetworkInterface {
  name: string;
  ip: string;
  mac: string;
  isDefault: boolean;
}

export interface MacSpooferProps {
  interfaces: NetworkInterface[];
  selectedInterface?: string;
  onSelectInterface: (name: string) => void;
  onChangeMac: (mac: string) => Promise<void>;
  onRandomize: () => Promise<string>;
  onRestore: () => Promise<void>;
  isLoading?: boolean;
}

export function MacSpoofer({
  interfaces,
  selectedInterface,
  onSelectInterface,
  onChangeMac,
  onRandomize,
  onRestore,
  isLoading = false,
}: MacSpooferProps) {
  const [customMac, setCustomMac] = useState('');
  const [isAdvancedOpen, setIsAdvancedOpen] = useState(false);
  const [error, setError] = useState('');

  const currentInterface = interfaces.find((i) => i.name === selectedInterface);

  const interfaceOptions = interfaces.map((iface) => ({
    value: iface.name,
    label: iface.name,
    description: `${iface.ip} - ${iface.mac}${iface.isDefault ? ' (Default)' : ''}`,
  }));

  // Format MAC address as user types
  const handleMacChange = (value: string) => {
    // Remove all non-hex characters
    const cleaned = value.replace(/[^0-9A-Fa-f]/g, '').toUpperCase();
    
    // Add colons every 2 characters
    let formatted = '';
    for (let i = 0; i < cleaned.length && i < 12; i++) {
      if (i > 0 && i % 2 === 0) formatted += ':';
      formatted += cleaned[i];
    }
    
    setCustomMac(formatted);
    setError('');
  };

  // Validate MAC address
  const validateMac = (mac: string): boolean => {
    const macRegex = /^([0-9A-Fa-f]{2}:){5}[0-9A-Fa-f]{2}$/;
    return macRegex.test(mac);
  };

  const handleApplyCustom = async () => {
    if (!validateMac(customMac)) {
      setError('Invalid MAC address format (XX:XX:XX:XX:XX:XX)');
      return;
    }

    try {
      await onChangeMac(customMac);
      setIsAdvancedOpen(false);
      setCustomMac('');
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to change MAC address');
    }
  };

  const handleRandomize = async () => {
    try {
      const newMac = await onRandomize();
      setCustomMac(newMac);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to generate random MAC');
    }
  };

  return (
    <div className="space-y-4">
      {/* Interface selector */}
      <Card>
        <div className="flex items-center justify-between mb-4">
          <div>
            <h3 className="font-medium text-white">Network Interface</h3>
            <p className="text-sm text-gray-400">Select interface to modify</p>
          </div>
        </div>

        <Dropdown
          options={interfaceOptions}
          value={selectedInterface || ''}
          onChange={onSelectInterface}
          placeholder="Select network interface"
        />

        {currentInterface && (
          <div className="mt-4 p-3 bg-gray-800/50 rounded-lg">
            <div className="grid grid-cols-2 gap-4 text-sm">
              <div>
                <p className="text-gray-500 mb-1">Current MAC</p>
                <p className="font-mono text-gray-200">{currentInterface.mac}</p>
              </div>
              <div>
                <p className="text-gray-500 mb-1">IP Address</p>
                <p className="font-mono text-gray-200">{currentInterface.ip}</p>
              </div>
            </div>
          </div>
        )}
      </Card>

      {/* Quick actions */}
      <Card>
        <h3 className="font-medium text-white mb-4">Quick Actions</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
          <Button
            variant="secondary"
            onClick={handleRandomize}
            isLoading={isLoading}
            disabled={!selectedInterface}
            className="w-full"
          >
            <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
            </svg>
            Random MAC
          </Button>
          
          <Button
            variant="secondary"
            onClick={() => setIsAdvancedOpen(true)}
            disabled={!selectedInterface}
            className="w-full"
          >
            <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
            </svg>
            Custom MAC
          </Button>
          
          <Button
            variant="outline"
            onClick={onRestore}
            isLoading={isLoading}
            disabled={!selectedInterface}
            className="w-full"
          >
            <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 10h10a8 8 0 018 8v2M3 10l6 6m-6-6l6-6" />
            </svg>
            Restore Original
          </Button>
        </div>
      </Card>

      {/* Vendor prefixes */}
      <Card>
        <h3 className="font-medium text-white mb-2">Common Vendor Prefixes</h3>
        <p className="text-sm text-gray-400 mb-4">
          Click to use a vendor's MAC prefix
        </p>
        <div className="flex flex-wrap gap-2">
          {vendorPrefixes.map((vendor) => (
            <button
              key={vendor.prefix}
              type="button"
              onClick={() => {
                handleMacChange(vendor.prefix);
                setIsAdvancedOpen(true);
              }}
              className="px-3 py-1.5 text-sm bg-gray-700/50 hover:bg-gray-700 text-gray-300 rounded-lg transition-colors"
              title={vendor.name}
            >
              {vendor.name}
            </button>
          ))}
        </div>
      </Card>

      {/* Custom MAC modal */}
      <Modal
        isOpen={isAdvancedOpen}
        onClose={() => setIsAdvancedOpen(false)}
        title="Custom MAC Address"
        size="sm"
        footer={
          <>
            <Button variant="ghost" onClick={() => setIsAdvancedOpen(false)}>
              Cancel
            </Button>
            <Button onClick={handleApplyCustom} isLoading={isLoading}>
              Apply
            </Button>
          </>
        }
      >
        <div className="space-y-4">
          <Input
            label="MAC Address"
            value={customMac}
            onChange={(e) => handleMacChange(e.target.value)}
            placeholder="XX:XX:XX:XX:XX:XX"
            error={error}
            className="font-mono"
          />
          
          <div className="flex items-center gap-2">
            <Button variant="ghost" size="sm" onClick={handleRandomize}>
              Generate Random
            </Button>
          </div>

          <div className="p-3 bg-yellow-900/20 border border-yellow-800/50 rounded-lg">
            <p className="text-sm text-yellow-200">
              Changing your MAC address requires Administrator privileges and will temporarily disconnect you from the network.
            </p>
          </div>
        </div>
      </Modal>
    </div>
  );
}

// Common vendor MAC prefixes
const vendorPrefixes = [
  { name: 'Apple', prefix: '00:1C:B3' },
  { name: 'Samsung', prefix: 'F4:7B:09' },
  { name: 'HP', prefix: '00:1E:0B' },
  { name: 'Dell', prefix: '00:14:22' },
  { name: 'Sony', prefix: '00:1A:80' },
  { name: 'LG', prefix: '00:1E:75' },
  { name: 'Roku', prefix: 'DC:3A:5E' },
  { name: 'Amazon', prefix: '74:C2:46' },
  { name: 'Google', prefix: 'F4:F5:D8' },
  { name: 'Xiaomi', prefix: '64:CC:2E' },
];
