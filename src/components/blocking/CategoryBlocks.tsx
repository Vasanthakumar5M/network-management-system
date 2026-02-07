/**
 * Category blocks component for managing block categories
 */

import { cn } from '@/lib/utils';
import { Toggle } from '@/components/common/Toggle';
import { Badge } from '@/components/common/Badge';
import type { BlockCategory } from '@/types';

export interface CategoryBlocksProps {
  categories: BlockCategory[];
  onToggle: (categoryId: string, enabled: boolean) => void;
}

// Category icons mapping
const categoryIcons: Record<string, React.ReactNode> = {
  adult: (
    <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
      <path fillRule="evenodd" d="M13.477 14.89A6 6 0 015.11 6.524l8.367 8.368zm1.414-1.414L6.524 5.11a6 6 0 018.367 8.367zM18 10a8 8 0 11-16 0 8 8 0 0116 0z" clipRule="evenodd" />
    </svg>
  ),
  social_media: (
    <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
      <path d="M13 6a3 3 0 11-6 0 3 3 0 016 0zM18 8a2 2 0 11-4 0 2 2 0 014 0zM14 15a4 4 0 00-8 0v3h8v-3zM6 8a2 2 0 11-4 0 2 2 0 014 0zM16 18v-3a5.972 5.972 0 00-.75-2.906A3.005 3.005 0 0119 15v3h-3zM4.75 12.094A5.973 5.973 0 004 15v3H1v-3a3 3 0 013.75-2.906z" />
    </svg>
  ),
  gaming: (
    <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
      <path d="M10 2a8 8 0 100 16 8 8 0 000-16zM6.5 9a1.5 1.5 0 100-3 1.5 1.5 0 000 3zm7 0a1.5 1.5 0 100-3 1.5 1.5 0 000 3zM5.5 12a.5.5 0 01.5-.5h8a.5.5 0 010 1H6a.5.5 0 01-.5-.5z" />
    </svg>
  ),
  gambling: (
    <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
      <path d="M10 2a8 8 0 100 16 8 8 0 000-16zm1 11H9v-1h2v1zm0-3H9V6h2v4z" />
    </svg>
  ),
  streaming: (
    <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
      <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM9.555 7.168A1 1 0 008 8v4a1 1 0 001.555.832l3-2a1 1 0 000-1.664l-3-2z" clipRule="evenodd" />
    </svg>
  ),
  drugs: (
    <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
      <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" />
    </svg>
  ),
  violence: (
    <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
      <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
    </svg>
  ),
  vpn: (
    <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
      <path fillRule="evenodd" d="M2.166 4.999A11.954 11.954 0 0010 1.944 11.954 11.954 0 0017.834 5c.11.65.166 1.32.166 2.001 0 5.225-3.34 9.67-8 11.317C5.34 16.67 2 12.225 2 7c0-.682.057-1.35.166-2.001zm11.541 3.708a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
    </svg>
  ),
  default: (
    <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
      <path fillRule="evenodd" d="M17.707 9.293a1 1 0 010 1.414l-7 7a1 1 0 01-1.414 0l-7-7A.997.997 0 012 10V5a3 3 0 013-3h5c.256 0 .512.098.707.293l7 7zM5 6a1 1 0 100-2 1 1 0 000 2z" clipRule="evenodd" />
    </svg>
  ),
};

export function CategoryBlocks({ categories, onToggle }: CategoryBlocksProps) {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      {categories.map((category) => (
        <CategoryCard
          key={category.id}
          category={category}
          onToggle={(enabled) => onToggle(category.id, enabled)}
        />
      ))}
    </div>
  );
}

interface CategoryCardProps {
  category: BlockCategory;
  onToggle: (enabled: boolean) => void;
}

function CategoryCard({ category, onToggle }: CategoryCardProps) {
  const icon = categoryIcons[category.id] || categoryIcons.default;

  return (
    <div
      className={cn(
        'p-4 rounded-xl border transition-all duration-200',
        category.isEnabled
          ? 'bg-red-900/20 border-red-800/50'
          : 'bg-gray-800/50 border-gray-700/50 hover:bg-gray-800/70'
      )}
    >
      <div className="flex items-start justify-between gap-4">
        <div className="flex items-start gap-3">
          <div
            className={cn(
              'p-2 rounded-lg',
              category.isEnabled
                ? 'bg-red-900/30 text-red-400'
                : 'bg-gray-700/50 text-gray-400'
            )}
          >
            {icon}
          </div>
          <div>
            <h3 className="font-medium text-white">{category.name}</h3>
            <p className="text-sm text-gray-400 mt-0.5">{category.description}</p>
            <div className="flex items-center gap-2 mt-2">
              <Badge variant={category.isEnabled ? 'danger' : 'default'} size="sm">
                {category.domainCount.toLocaleString()} domains
              </Badge>
              {category.isEnabled && (
                <Badge variant="danger" size="sm" dot>
                  Blocking
                </Badge>
              )}
            </div>
          </div>
        </div>
        <Toggle
          checked={category.isEnabled}
          onChange={(e) => onToggle(e.target.checked)}
          size="sm"
        />
      </div>
    </div>
  );
}
