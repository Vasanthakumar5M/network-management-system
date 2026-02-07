/**
 * Block rule editor component for creating/editing block rules
 */

import { useState } from 'react';
import { Button } from '@/components/common/Button';
import { Input } from '@/components/common/Input';
import { Dropdown, MultiDropdown } from '@/components/common/Dropdown';
import { Modal } from '@/components/common/Modal';
import type { BlockRule, Device, Schedule } from '@/types';

export interface BlockRuleEditorProps {
  rule?: BlockRule;
  devices: Device[];
  schedules: Schedule[];
  isOpen: boolean;
  onClose: () => void;
  onSave: (rule: Omit<BlockRule, 'id' | 'createdAt'>) => void;
}

export function BlockRuleEditor({
  rule,
  devices,
  schedules,
  isOpen,
  onClose,
  onSave,
}: BlockRuleEditorProps) {
  const [type, setType] = useState<BlockRule['type']>(rule?.type || 'domain');
  const [value, setValue] = useState(rule?.value || '');
  const [isEnabled, setIsEnabled] = useState(rule?.isEnabled ?? true);
  const [selectedDevices, setSelectedDevices] = useState<string[]>(rule?.deviceIds || []);
  const [scheduleId, setScheduleId] = useState(rule?.scheduleId || '');
  const [error, setError] = useState('');

  const typeOptions = [
    { value: 'domain', label: 'Domain', description: 'Block specific domain (e.g., facebook.com)' },
    { value: 'keyword', label: 'Keyword', description: 'Block URLs containing keyword' },
    { value: 'category', label: 'Category', description: 'Block entire category' },
    { value: 'ip', label: 'IP Address', description: 'Block specific IP address' },
  ];

  const deviceOptions = devices.map((d) => ({
    value: d.id,
    label: d.hostname || d.ip,
    description: d.ip,
  }));

  const scheduleOptions = [
    { value: '', label: 'Always active' },
    ...schedules.map((s) => ({
      value: s.id,
      label: s.name,
      description: `${s.days.join(', ')} ${s.startTime}-${s.endTime}`,
    })),
  ];

  const validateRule = (): boolean => {
    if (!value.trim()) {
      setError('Value is required');
      return false;
    }

    if (type === 'domain') {
      // Basic domain validation
      const domainRegex = /^[a-zA-Z0-9][a-zA-Z0-9-_.]*[a-zA-Z0-9]$/;
      if (!domainRegex.test(value)) {
        setError('Invalid domain format');
        return false;
      }
    }

    if (type === 'ip') {
      // Basic IP validation
      const ipRegex = /^(\d{1,3}\.){3}\d{1,3}$/;
      if (!ipRegex.test(value)) {
        setError('Invalid IP address format');
        return false;
      }
    }

    setError('');
    return true;
  };

  const handleSave = () => {
    if (!validateRule()) return;

    onSave({
      type,
      value: value.trim(),
      isEnabled,
      deviceIds: selectedDevices.length > 0 ? selectedDevices : undefined,
      scheduleId: scheduleId || undefined,
    });

    onClose();
  };

  const getPlaceholder = (): string => {
    switch (type) {
      case 'domain': return 'example.com';
      case 'keyword': return 'Enter keyword to block';
      case 'category': return 'Select a category';
      case 'ip': return '192.168.1.100';
      default: return '';
    }
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={rule ? 'Edit Block Rule' : 'Add Block Rule'}
      size="md"
      footer={
        <>
          <Button variant="ghost" onClick={onClose}>
            Cancel
          </Button>
          <Button onClick={handleSave}>
            {rule ? 'Update Rule' : 'Add Rule'}
          </Button>
        </>
      }
    >
      <div className="space-y-4">
        {/* Rule type */}
        <Dropdown
          label="Rule Type"
          options={typeOptions}
          value={type}
          onChange={(v) => setType(v as BlockRule['type'])}
        />

        {/* Value */}
        <Input
          label="Value"
          value={value}
          onChange={(e) => setValue(e.target.value)}
          placeholder={getPlaceholder()}
          error={error}
        />

        {/* Apply to devices */}
        <MultiDropdown
          label="Apply to Devices"
          options={deviceOptions}
          value={selectedDevices}
          onChange={setSelectedDevices}
          placeholder="All devices"
        />

        {/* Schedule */}
        <Dropdown
          label="Schedule"
          options={scheduleOptions}
          value={scheduleId}
          onChange={setScheduleId}
        />

        {/* Enable toggle */}
        <label className="flex items-center gap-3 cursor-pointer">
          <input
            type="checkbox"
            checked={isEnabled}
            onChange={(e) => setIsEnabled(e.target.checked)}
            className="rounded border-gray-600 bg-gray-700 text-blue-500 focus:ring-blue-500"
          />
          <span className="text-sm text-gray-300">Enable rule immediately</span>
        </label>
      </div>
    </Modal>
  );
}
