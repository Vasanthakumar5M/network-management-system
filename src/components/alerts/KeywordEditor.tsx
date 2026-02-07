/**
 * Keyword editor component for managing alert keywords
 */

import { useState } from 'react';
import { Button } from '@/components/common/Button';
import { Input } from '@/components/common/Input';
import { Modal } from '@/components/common/Modal';
import { Dropdown } from '@/components/common/Dropdown';
import { cn } from '@/lib/utils';
import type { AlertCategory, AlertSeverity } from '@/types';

export interface Keyword {
  id: string;
  word: string;
  category: AlertCategory;
  severity: AlertSeverity;
  matchVariants: boolean; // Match leetspeak, misspellings
}

export interface KeywordEditorProps {
  keywords: Keyword[];
  onAdd: (keyword: Omit<Keyword, 'id'>) => void;
  onRemove: (id: string) => void;
  onUpdate: (id: string, keyword: Partial<Keyword>) => void;
}

const categoryOptions = [
  { value: 'self_harm', label: 'Self Harm' },
  { value: 'suicide', label: 'Suicide' },
  { value: 'predator_grooming', label: 'Predator/Grooming' },
  { value: 'bullying', label: 'Bullying' },
  { value: 'drugs', label: 'Drugs' },
  { value: 'violence', label: 'Violence' },
  { value: 'adult_content', label: 'Adult Content' },
];

const severityOptions = [
  { value: 'critical', label: 'Critical', description: 'Immediate notification' },
  { value: 'high', label: 'High', description: 'Priority alert' },
  { value: 'medium', label: 'Medium', description: 'Standard alert' },
  { value: 'low', label: 'Low', description: 'Low priority' },
];

export function KeywordEditor({
  keywords,
  onAdd,
  onRemove,
}: KeywordEditorProps) {
  const [isAddModalOpen, setIsAddModalOpen] = useState(false);
  const [newWord, setNewWord] = useState('');
  const [newCategory, setNewCategory] = useState<AlertCategory>('self_harm');
  const [newSeverity, setNewSeverity] = useState<AlertSeverity>('high');
  const [matchVariants, setMatchVariants] = useState(true);
  const [filter, setFilter] = useState<string>('');

  // Group keywords by category
  const groupedKeywords = keywords.reduce<Record<string, Keyword[]>>((acc, kw) => {
    if (!acc[kw.category]) acc[kw.category] = [];
    acc[kw.category].push(kw);
    return acc;
  }, {});

  const handleAdd = () => {
    if (!newWord.trim()) return;

    onAdd({
      word: newWord.trim().toLowerCase(),
      category: newCategory,
      severity: newSeverity,
      matchVariants,
    });

    setNewWord('');
    setIsAddModalOpen(false);
  };

  const filteredKeywords = filter
    ? keywords.filter((kw) => kw.category === filter)
    : keywords;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-lg font-semibold text-white">Alert Keywords</h3>
          <p className="text-sm text-gray-400">
            Keywords that trigger alerts when detected in traffic
          </p>
        </div>
        <Button onClick={() => setIsAddModalOpen(true)}>
          Add Keyword
        </Button>
      </div>

      {/* Filter */}
      <div className="flex items-center gap-4">
        <Dropdown
          options={[{ value: '', label: 'All Categories' }, ...categoryOptions]}
          value={filter}
          onChange={setFilter}
          className="w-48"
        />
        <span className="text-sm text-gray-500">
          {filteredKeywords.length} keywords
        </span>
      </div>

      {/* Keywords list */}
      <div className="space-y-4">
        {Object.entries(groupedKeywords)
          .filter(([cat]) => !filter || cat === filter)
          .map(([category, kws]) => (
            <div key={category} className="space-y-2">
              <h4 className="text-sm font-medium text-gray-400 capitalize">
                {categoryOptions.find((c) => c.value === category)?.label || category}
              </h4>
              <div className="flex flex-wrap gap-2">
                {kws.map((kw) => (
                  <KeywordBadge
                    key={kw.id}
                    keyword={kw}
                    onRemove={() => onRemove(kw.id)}
                  />
                ))}
              </div>
            </div>
          ))}

        {filteredKeywords.length === 0 && (
          <div className="text-center py-8 text-gray-500">
            No keywords configured
          </div>
        )}
      </div>

      {/* Add modal */}
      <Modal
        isOpen={isAddModalOpen}
        onClose={() => setIsAddModalOpen(false)}
        title="Add Alert Keyword"
        size="sm"
        footer={
          <>
            <Button variant="ghost" onClick={() => setIsAddModalOpen(false)}>
              Cancel
            </Button>
            <Button onClick={handleAdd} disabled={!newWord.trim()}>
              Add Keyword
            </Button>
          </>
        }
      >
        <div className="space-y-4">
          <Input
            label="Keyword"
            value={newWord}
            onChange={(e) => setNewWord(e.target.value)}
            placeholder="Enter keyword to detect"
          />

          <Dropdown
            label="Category"
            options={categoryOptions}
            value={newCategory}
            onChange={(v) => setNewCategory(v as AlertCategory)}
          />

          <Dropdown
            label="Severity"
            options={severityOptions}
            value={newSeverity}
            onChange={(v) => setNewSeverity(v as AlertSeverity)}
          />

          <label className="flex items-center gap-3 cursor-pointer">
            <input
              type="checkbox"
              checked={matchVariants}
              onChange={(e) => setMatchVariants(e.target.checked)}
              className="rounded border-gray-600 bg-gray-700 text-blue-500 focus:ring-blue-500"
            />
            <div>
              <span className="text-sm text-gray-300">Match variants</span>
              <p className="text-xs text-gray-500">
                Detect leetspeak and common misspellings
              </p>
            </div>
          </label>
        </div>
      </Modal>
    </div>
  );
}

// Individual keyword badge
interface KeywordBadgeProps {
  keyword: Keyword;
  onRemove: () => void;
}

function KeywordBadge({ keyword, onRemove }: KeywordBadgeProps) {
  const severityColors = {
    critical: 'bg-red-900/50 border-red-700 text-red-300',
    high: 'bg-orange-900/50 border-orange-700 text-orange-300',
    medium: 'bg-yellow-900/50 border-yellow-700 text-yellow-300',
    low: 'bg-blue-900/50 border-blue-700 text-blue-300',
  };

  return (
    <span
      className={cn(
        'inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full border text-sm',
        severityColors[keyword.severity]
      )}
    >
      {keyword.word}
      {keyword.matchVariants && (
        <span className="text-xs opacity-60" title="Matches variants">*</span>
      )}
      <button
        onClick={onRemove}
        className="ml-0.5 p-0.5 rounded-full hover:bg-white/10 transition-colors"
      >
        <svg className="w-3 h-3" fill="currentColor" viewBox="0 0 20 20">
          <path
            fillRule="evenodd"
            d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z"
            clipRule="evenodd"
          />
        </svg>
      </button>
    </span>
  );
}
