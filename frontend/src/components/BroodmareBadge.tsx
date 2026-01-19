import React from 'react';

export type BroodmareBadgeVariant = 'circle' | 'pill' | 'tag';

interface BroodmareBadgeProps {
  label?: string;
  variant?: BroodmareBadgeVariant;
  className?: string;
  ariaLabel?: string;
}

/**
 * 統一された繁殖牝馬バッジ
 */
export const BroodmareBadge: React.FC<BroodmareBadgeProps> = ({
  label = '繁',
  variant = 'circle',
  className = '',
  ariaLabel = '繁殖牝馬'
}) => {
  const base = 'inline-flex items-center justify-center font-semibold text-xs tracking-tight';
  const variantClasses: Record<BroodmareBadgeVariant, string> = {
    circle: 'w-6 h-6 rounded-full bg-rose-50 text-rose-600 border border-rose-100 shadow-sm',
    pill: 'px-2 py-0.5 rounded-full bg-rose-50 text-rose-600 border border-rose-200',
    tag: 'px-2 py-1 rounded-md bg-rose-600 text-white text-[11px] shadow-lg shadow-rose-200'
  };

  return (
    <span
      className={`${base} ${variantClasses[variant]} ${className}`.trim()}
      aria-label={ariaLabel}
    >
      {label}
    </span>
  );
};
