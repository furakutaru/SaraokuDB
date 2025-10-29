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
  onReset?: () => void;
  className?: string;
}
const FilterControls: React.FC<FilterControlsProps> = ({
  sexFilter: initialSexFilter,
  ageRange,
  onSexFilterChange,
  onAgeRangeChange,
  onReset,
  className = '',
}) => {
  // 内部状態として性別フィルターを管理
  const [sexFilter, setSexFilter] = React.useState(initialSexFilter);
  
  // 親コンポーネントから渡されたpropsが変更されたら、内部状態を更新
  React.useEffect(() => {
    setSexFilter(initialSexFilter);
  }, [initialSexFilter]);

  const handleAgeRangeChange = (newRange: number[]) => {
    if (newRange.length === 2) {
      onAgeRangeChange([newRange[0], newRange[1]]);
    }
  };

  // 性別フィルターの変更を処理
  const handleSexFilterChange = (id: 'male' | 'female' | 'gelding', checked: boolean) => {
    const newSexFilter = {
      ...sexFilter,
      [id]: checked,
    };
    setSexFilter(newSexFilter);
    onSexFilterChange(newSexFilter);
  };

  return (
    <div className={`space-y-4 ${className}`}>
      <div>
        <h3 className="text-sm font-medium text-gray-700 mb-2">性別</h3>
        <div className="flex space-x-4">
          {[
            { id: 'male' as const, label: '牡' },
            { id: 'female' as const, label: '牝' },
            { id: 'gelding' as const, label: 'セ' },
          ].map(({ id, label }) => (
            <div key={id} className="flex items-center">
              <Checkbox
                id={id}
                checked={sexFilter[id]}
                onCheckedChange={(checked) => handleSexFilterChange(id, checked)}
              />
              <Label htmlFor={id} className="ml-1 text-sm text-gray-700">
                {label}
              </Label>
            </div>
          ))}
        </div>
      </div>

      <div>
        <h3 className="text-sm font-medium text-gray-700 mb-2">年齢</h3>
        <div className="flex items-center space-x-2">
          <div className="flex-1">
            <label htmlFor="minAge" className="block text-xs text-gray-500 mb-1">最小</label>
            <div className="relative rounded-md shadow-sm">
              <input
                type="number"
                id="minAge"
                min={0}
                max={ageRange[1]}
                value={ageRange[0]}
                onChange={(e) => {
                  const value = parseInt(e.target.value, 10) || 0;
                  onAgeRangeChange([Math.min(value, ageRange[1]), ageRange[1]]);
                }}
                className="block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm pr-8"
              />
              <div className="absolute inset-y-0 right-0 flex items-center pr-3 pointer-events-none">
                <span className="text-gray-500 sm:text-sm">歳</span>
              </div>
            </div>
          </div>
          <div className="flex items-center pt-5">
            <span className="text-gray-500">〜</span>
          </div>
          <div className="flex-1">
            <label htmlFor="maxAge" className="block text-xs text-gray-500 mb-1">最大</label>
            <div className="relative rounded-md shadow-sm">
              <input
                type="number"
                id="maxAge"
                min={ageRange[0]}
                max={30}
                value={ageRange[1]}
                onChange={(e) => {
                  const value = parseInt(e.target.value, 10) || 0;
                  onAgeRangeChange([ageRange[0], Math.max(value, ageRange[0])]);
                }}
                className="block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm pr-8"
              />
              <div className="absolute inset-y-0 right-0 flex items-center pr-3 pointer-events-none">
                <span className="text-gray-500 sm:text-sm">歳</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <Button
        variant="outline"
        size="sm"
        className="w-full mt-4"
        onClick={() => {
          const resetFilter = { male: true, female: true, gelding: true };
          setSexFilter(resetFilter);
          onSexFilterChange(resetFilter);
          onAgeRangeChange([0, 10]);
          // 検索フィールドもリセット
          if (onReset) {
            onReset();
          }
        }}
      >
        フィルターをリセット
      </Button>
    </div>
  );
};

export default FilterControls;
