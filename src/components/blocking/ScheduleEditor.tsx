/**
 * Schedule editor component for time-based blocking
 */

import { useState } from 'react';
import { Button } from '@/components/common/Button';
import { Input } from '@/components/common/Input';
import { Modal } from '@/components/common/Modal';
import { MultiDropdown } from '@/components/common/Dropdown';
import { Toggle } from '@/components/common/Toggle';
import { cn } from '@/lib/utils';
import type { Schedule, BlockCategory } from '@/types';

export interface ScheduleEditorProps {
  schedule?: Schedule;
  categories: BlockCategory[];
  isOpen: boolean;
  onClose: () => void;
  onSave: (schedule: Omit<Schedule, 'id'>) => void;
}

const DAYS = [
  { value: 'monday', label: 'Mon' },
  { value: 'tuesday', label: 'Tue' },
  { value: 'wednesday', label: 'Wed' },
  { value: 'thursday', label: 'Thu' },
  { value: 'friday', label: 'Fri' },
  { value: 'saturday', label: 'Sat' },
  { value: 'sunday', label: 'Sun' },
];

export function ScheduleEditor({
  schedule,
  categories,
  isOpen,
  onClose,
  onSave,
}: ScheduleEditorProps) {
  const [name, setName] = useState(schedule?.name || '');
  const [description, setDescription] = useState(schedule?.description || '');
  const [isEnabled, setIsEnabled] = useState(schedule?.isEnabled ?? true);
  const [selectedDays, setSelectedDays] = useState<string[]>(schedule?.days || []);
  const [startTime, setStartTime] = useState(schedule?.startTime || '09:00');
  const [endTime, setEndTime] = useState(schedule?.endTime || '21:00');
  const [selectedCategories, setSelectedCategories] = useState<string[]>(
    schedule?.categoriesToBlock || []
  );
  const [error, setError] = useState('');

  const categoryOptions = categories.map((c) => ({
    value: c.id,
    label: c.name,
    description: `${c.domainCount} domains`,
  }));

  const toggleDay = (day: string) => {
    setSelectedDays((prev) =>
      prev.includes(day) ? prev.filter((d) => d !== day) : [...prev, day]
    );
  };

  const selectWeekdays = () => {
    setSelectedDays(['monday', 'tuesday', 'wednesday', 'thursday', 'friday']);
  };

  const selectWeekend = () => {
    setSelectedDays(['saturday', 'sunday']);
  };

  const selectAll = () => {
    setSelectedDays(DAYS.map((d) => d.value));
  };

  const handleSave = () => {
    if (!name.trim()) {
      setError('Name is required');
      return;
    }
    if (selectedDays.length === 0) {
      setError('Select at least one day');
      return;
    }
    if (startTime >= endTime) {
      setError('End time must be after start time');
      return;
    }

    onSave({
      name: name.trim(),
      description: description.trim(),
      isEnabled,
      days: selectedDays,
      startTime,
      endTime,
      categoriesToBlock: selectedCategories,
    });

    onClose();
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={schedule ? 'Edit Schedule' : 'Create Schedule'}
      size="lg"
      footer={
        <>
          <Button variant="ghost" onClick={onClose}>
            Cancel
          </Button>
          <Button onClick={handleSave}>
            {schedule ? 'Update Schedule' : 'Create Schedule'}
          </Button>
        </>
      }
    >
      <div className="space-y-6">
        {/* Name and description */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <Input
            label="Schedule Name"
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="e.g., School Hours"
            error={error && !name ? error : undefined}
          />
          <Input
            label="Description (optional)"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            placeholder="e.g., Block during school"
          />
        </div>

        {/* Days selection */}
        <div>
          <label className="block text-sm font-medium text-gray-300 mb-2">
            Active Days
          </label>
          <div className="flex flex-wrap gap-2 mb-2">
            {DAYS.map((day) => (
              <button
                key={day.value}
                type="button"
                onClick={() => toggleDay(day.value)}
                className={cn(
                  'px-3 py-2 rounded-lg font-medium text-sm transition-colors',
                  selectedDays.includes(day.value)
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
                )}
              >
                {day.label}
              </button>
            ))}
          </div>
          <div className="flex gap-2">
            <button
              type="button"
              onClick={selectWeekdays}
              className="text-xs text-blue-400 hover:text-blue-300"
            >
              Weekdays
            </button>
            <button
              type="button"
              onClick={selectWeekend}
              className="text-xs text-blue-400 hover:text-blue-300"
            >
              Weekend
            </button>
            <button
              type="button"
              onClick={selectAll}
              className="text-xs text-blue-400 hover:text-blue-300"
            >
              Every day
            </button>
          </div>
        </div>

        {/* Time range */}
        <div>
          <label className="block text-sm font-medium text-gray-300 mb-2">
            Active Hours
          </label>
          <div className="flex items-center gap-4">
            <div className="flex-1">
              <input
                type="time"
                value={startTime}
                onChange={(e) => setStartTime(e.target.value)}
                className="w-full px-4 py-2 bg-gray-800 border border-gray-700 rounded-lg text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
              <span className="text-xs text-gray-500 mt-1 block">Start time</span>
            </div>
            <span className="text-gray-500">to</span>
            <div className="flex-1">
              <input
                type="time"
                value={endTime}
                onChange={(e) => setEndTime(e.target.value)}
                className="w-full px-4 py-2 bg-gray-800 border border-gray-700 rounded-lg text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
              <span className="text-xs text-gray-500 mt-1 block">End time</span>
            </div>
          </div>
        </div>

        {/* Categories to block */}
        <MultiDropdown
          label="Categories to Block"
          options={categoryOptions}
          value={selectedCategories}
          onChange={setSelectedCategories}
          placeholder="Select categories..."
        />

        {/* Enable toggle */}
        <div className="flex items-center justify-between p-4 bg-gray-800/50 rounded-lg">
          <div>
            <p className="font-medium text-white">Enable Schedule</p>
            <p className="text-sm text-gray-400">
              Schedule will be active when enabled
            </p>
          </div>
          <Toggle checked={isEnabled} onChange={(e) => setIsEnabled(e.target.checked)} />
        </div>

        {/* Error display */}
        {error && (
          <p className="text-sm text-red-400">{error}</p>
        )}
      </div>
    </Modal>
  );
}

// Schedule card for display
export interface ScheduleCardProps {
  schedule: Schedule;
  onEdit: () => void;
  onDelete: () => void;
  onToggle: (enabled: boolean) => void;
}

export function ScheduleCard({
  schedule,
  onEdit,
  onDelete,
  onToggle,
}: ScheduleCardProps) {
  const formatDays = (days: string[]): string => {
    if (days.length === 7) return 'Every day';
    if (
      days.length === 5 &&
      days.includes('monday') &&
      days.includes('friday') &&
      !days.includes('saturday')
    ) {
      return 'Weekdays';
    }
    if (days.length === 2 && days.includes('saturday') && days.includes('sunday')) {
      return 'Weekends';
    }
    return days.map((d) => d.slice(0, 3)).join(', ');
  };

  return (
    <div
      className={cn(
        'p-4 rounded-xl border transition-all duration-200',
        schedule.isEnabled
          ? 'bg-blue-900/20 border-blue-800/50'
          : 'bg-gray-800/50 border-gray-700/50'
      )}
    >
      <div className="flex items-start justify-between gap-4">
        <div className="flex-1">
          <div className="flex items-center gap-2">
            <h3 className="font-medium text-white">{schedule.name}</h3>
            {schedule.isEnabled && (
              <span className="w-2 h-2 rounded-full bg-blue-500 animate-pulse" />
            )}
          </div>
          {schedule.description && (
            <p className="text-sm text-gray-400 mt-0.5">{schedule.description}</p>
          )}
          <div className="flex items-center gap-4 mt-2 text-sm text-gray-500">
            <span>{formatDays(schedule.days)}</span>
            <span>
              {schedule.startTime} - {schedule.endTime}
            </span>
            <span>
              {schedule.categoriesToBlock.length} categories
            </span>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <Toggle
            checked={schedule.isEnabled}
            onChange={(e) => onToggle(e.target.checked)}
            size="sm"
          />
          <button
            onClick={onEdit}
            className="p-2 text-gray-400 hover:text-white hover:bg-gray-700 rounded-lg transition-colors"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
            </svg>
          </button>
          <button
            onClick={onDelete}
            className="p-2 text-gray-400 hover:text-red-400 hover:bg-red-900/20 rounded-lg transition-colors"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
            </svg>
          </button>
        </div>
      </div>
    </div>
  );
}
