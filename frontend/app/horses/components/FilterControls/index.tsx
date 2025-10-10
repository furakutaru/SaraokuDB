import React from 'react';

// シンプルなボタンコンポーネント
const Button: React.FC<React.ButtonHTMLAttributes<HTMLButtonElement> & { 
  variant?: 'outline' | 'solid';
  size?: 'sm' | 'md' | 'lg';
}> = ({ 
  children, 
  className = '', 
  variant = 'solid',
  size = 'md',
  ...props 
}) => {
  const baseStyles = 'rounded-md font-medium focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500';
  const variantStyles = variant === 'outline' 
    ? 'border border-gray-300 bg-white text-gray-700 hover:bg-gray-50' 
    : 'bg-blue-600 text-white hover:bg-blue-700';
  const sizeStyles = size === 'sm' 
    ? 'px-3 py-1.5 text-xs' 
    : size === 'lg' 
      ? 'px-6 py-3 text-base' 
      : 'px-4 py-2 text-sm';

  return (
    <button
      className={`${baseStyles} ${variantStyles} ${sizeStyles} ${className}`}
      {...props}
    >
      {children}
    </button>
  );
};

// シンプルなチェックボックスコンポーネント
const Checkbox: React.FC<{
  id: string;
  checked: boolean;
  onCheckedChange: (checked: boolean) => void;
  className?: string;
}> = ({ id, checked, onCheckedChange, className = '' }) => (
  <div className={`flex items-center ${className}`}>
    <input
      id={id}
      type="checkbox"
      className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
      checked={checked}
      onChange={(e) => onCheckedChange(e.target.checked)}
    />
  </div>
);

// シンプルなスライダーコンポーネント
const Slider: React.FC<{
  min: number;
  max: number;
  step: number;
  value: [number, number];
  onValueChange: (value: [number, number]) => void;
  minStepsBetweenThumbs?: number;
  className?: string;
}> = ({ 
  min, 
  max, 
  step, 
  value, 
  onValueChange, 
  minStepsBetweenThumbs = 1,
  className = '' 
}) => (
  <div className={`w-full ${className}`}>
    <div className="relative">
      <input
        type="range"
        min={min}
        max={max}
        step={step}
        value={value[0]}
        onChange={(e) => onValueChange([parseInt(e.target.value, 10), value[1]])}
        className="w-full absolute z-10"
        style={{
          pointerEvents: value[1] === max ? 'auto' : 'none',
          opacity: value[1] === max ? 1 : 0.5,
        }}
      />
      <input
        type="range"
        min={min}
        max={max}
        step={step}
        value={value[1]}
        onChange={(e) => onValueChange([value[0], parseInt(e.target.value, 10)])}
        className="w-full relative z-20"
      />
      <div 
        className="absolute top-1/2 h-1 bg-blue-200 rounded-full -translate-y-1/2 z-0"
        style={{
          left: `${((value[0] - min) / (max - min)) * 100}%`,
          right: `${100 - ((value[1] - min) / (max - min)) * 100}%`,
        }}
      />
    </div>
    <div className="flex justify-between text-xs text-gray-500 mt-1">
      <span>{value[0]}歳</span>
      <span>{value[1]}歳</span>
    </div>
  </div>
);

// シンプルなラベルコンポーネント
const Label: React.FC<{ htmlFor: string; className?: string; children: React.ReactNode }> = ({
  htmlFor,
  children,
  className = '',
}) => (
  <label
    htmlFor={htmlFor}
  >
    {children}
  </label>
);

interface FilterControlsProps {
  sexFilter: {
    male: boolean;
    female: boolean;
    gelding: boolean;
  };
  ageRange: [number, number];
  onSexFilterChange: (filter: { male: boolean; female: boolean; gelding: boolean }) => void;
  onAgeRangeChange: (range: [number, number]) => void;
  className?: string;
}
const FilterControls: React.FC<FilterControlsProps> = ({
  sexFilter,
  ageRange,
  onSexFilterChange,
  onAgeRangeChange,
  className = '',
}) => {
  const handleAgeRangeChange = (newRange: number[]) => {
    if (newRange.length === 2) {
      onAgeRangeChange([newRange[0], newRange[1]]);
    }
  };

  return (
    <div className={`space-y-4 ${className}`}>
      <div>
        <h3 className="text-sm font-medium text-gray-700 mb-2">性別</h3>
        <div className="space-y-2">
          {[
            { id: 'male', label: '牡' },
            { id: 'female', label: '牝' },
            { id: 'gelding', label: 'セ' },
          ].map(({ id, label }) => (
            <div key={id} className="flex items-center">
              <Checkbox
                id={id}
                checked={sexFilter[id as keyof typeof sexFilter]}
                onCheckedChange={(checked) =>
                  onSexFilterChange({
                    ...sexFilter,
                    [id]: checked,
                  })
                }
              />
              <Label htmlFor={id} className="ml-2 text-sm text-gray-700">
                {label}
              </Label>
            </div>
          ))}
        </div>
      </div>

      <div>
        <h3 className="text-sm font-medium text-gray-700 mb-2">年齢</h3>
        <Slider
          min={0}
          max={10}
          step={1}
          value={ageRange}
          onValueChange={handleAgeRangeChange}
          minStepsBetweenThumbs={1}
          className="w-full"
        />
      </div>

      <Button
        variant="outline"
        size="sm"
        className="w-full mt-4"
        onClick={() => {
          onSexFilterChange({ male: true, female: true, gelding: true });
          onAgeRangeChange([0, 10]);
        }}
      >
        フィルターをリセット
      </Button>
    </div>
  );
};

export default FilterControls;
