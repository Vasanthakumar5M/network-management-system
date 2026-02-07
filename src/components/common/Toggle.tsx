import { forwardRef, type InputHTMLAttributes } from 'react';
import { cn } from '@/lib/utils';

export interface ToggleProps
  extends Omit<InputHTMLAttributes<HTMLInputElement>, 'type' | 'size'> {
  label?: string;
  description?: string;
  size?: 'sm' | 'md' | 'lg';
}

const Toggle = forwardRef<HTMLInputElement, ToggleProps>(
  ({ className, label, description, size = 'md', id, ...props }, ref) => {
    const toggleId = id || `toggle-${Math.random().toString(36).slice(2, 9)}`;

    const sizes = {
      sm: {
        track: 'w-8 h-4',
        thumb: 'w-3 h-3',
        translate: 'translate-x-4',
      },
      md: {
        track: 'w-11 h-6',
        thumb: 'w-5 h-5',
        translate: 'translate-x-5',
      },
      lg: {
        track: 'w-14 h-7',
        thumb: 'w-6 h-6',
        translate: 'translate-x-7',
      },
    };

    const sizeConfig = sizes[size];

    return (
      <label
        htmlFor={toggleId}
        className={cn(
          'inline-flex items-center gap-3 cursor-pointer',
          props.disabled && 'opacity-50 cursor-not-allowed',
          className
        )}
      >
        <div className="relative">
          <input
            ref={ref}
            type="checkbox"
            id={toggleId}
            className="sr-only peer"
            {...props}
          />
          <div
            className={cn(
              'rounded-full transition-colors duration-200',
              'bg-gray-700 peer-checked:bg-blue-600',
              'peer-focus:ring-2 peer-focus:ring-blue-500 peer-focus:ring-offset-2 peer-focus:ring-offset-gray-900',
              sizeConfig.track
            )}
          />
          <div
            className={cn(
              'absolute top-0.5 left-0.5 bg-white rounded-full transition-transform duration-200',
              'peer-checked:' + sizeConfig.translate,
              sizeConfig.thumb
            )}
          />
        </div>
        {(label || description) && (
          <div className="flex flex-col">
            {label && (
              <span className="text-sm font-medium text-gray-200">{label}</span>
            )}
            {description && (
              <span className="text-xs text-gray-500">{description}</span>
            )}
          </div>
        )}
      </label>
    );
  }
);

Toggle.displayName = 'Toggle';

export { Toggle };
