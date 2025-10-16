import React from 'react';

interface SexBadgeProps {
  sex: string | string[] | null | undefined;
  age?: number | null;
  className?: string;
}

const SexBadge: React.FC<SexBadgeProps> = ({ 
  sex, 
  age,
  className = ''
}) => {
  const getSexInfo = (sexData: string | string[] | null | undefined) => {
    console.log('Raw sex data:', sexData);
    
    if (!sexData) return { label: '-', color: 'bg-gray-100 text-gray-800' };
    
    let sexStr = '';
    
    try {
      // 文字列の場合
      if (typeof sexData === 'string') {
        // すでに「牡」「牝」「セ」が含まれている場合はそのまま使用
        if (sexData.includes('牡') || sexData.includes('牝') || sexData.includes('セ')) {
          sexStr = sexData;
        } 
        // JSON文字列の場合
        else if (sexData.startsWith('[') || sexData.startsWith('"')) {
          // エスケープされた引用符を処理
          const cleanStr = sexData.replace(/\\"/g, '"');
          // JSONパースを試みる
          try {
            const parsed = JSON.parse(cleanStr);
            sexStr = Array.isArray(parsed) ? parsed[0] : parsed;
          } catch (e) {
            console.error('JSON parse error:', e);
            sexStr = sexData;
          }
        } else {
          sexStr = sexData;
        }
      } 
      // 配列の場合
      else if (Array.isArray(sexData)) {
        sexStr = sexData[0] || '';
      }
      
      // ユニコードエスケープシーケンスをデコード
      if (typeof sexStr === 'string') {
        sexStr = sexStr.replace(/\\u([\dA-F]{4})/gi, (match, grp) => {
          return String.fromCharCode(parseInt(grp, 16));
        });
      }
      
      console.log('Processed sex string:', sexStr);
      
      // 性別の判定
      if (sexStr.includes('牡')) {
        return { label: '牡', color: 'bg-blue-100 text-blue-800' };
      } else if (sexStr.includes('牝')) {
        return { label: '牝', color: 'bg-pink-100 text-pink-800' };
      } else if (sexStr.includes('セ')) {
        return { label: 'セ', color: 'bg-green-100 text-green-800' };
      }
    } catch (e) {
      console.error('性別データの処理エラー:', e, '元の値:', sexData);
    }
    
    return { 
      label: sexStr || '-', 
      color: 'bg-gray-100 text-gray-800' 
    };
  };

  const sexInfo = getSexInfo(sex);
  const ageText = age ? `${age}歳` : '';

  return (
    <div className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${sexInfo.color} ${className}`}>
      {sexInfo.label} {ageText}
    </div>
  );
};

export default SexBadge;
