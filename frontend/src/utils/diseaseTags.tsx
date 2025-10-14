import React, { ReactElement } from 'react';

/**
 * 疾病タグをレンダリングするためのユーティリティ関数
 * @param tags 表示するタグ（文字列または文字列の配列）
 * @param className 追加のCSSクラス（オプション）
 * @returns レンダリングされたタグ要素
 */
export function renderDiseaseTags(tags: string | string[] | undefined, className: string = ''): ReactElement | null {
  if (!tags) return null;
  
  const tagList = Array.isArray(tags) ? tags : [tags];
  if (tagList.length === 0) return null;
  
  return (
    <div className={`flex flex-wrap gap-2 ${className}`}>
      {tagList.map((tag, index) => (
        <span 
          key={index} 
          className="px-2 py-1 text-xs font-medium rounded-full bg-red-100 text-red-800"
        >
          {tag}
        </span>
      ))}
    </div>
  );
}

/**
 * コメントから疾病タグを抽出する関数
 * @param comment 抽出元のコメント
 * @param existingTags 既存のタグ（オプション）
 * @returns 抽出された疾病タグの配列
 */
export function extractDiseaseTags(comment: string | null | undefined, existingTags: string[] = []): string[] {
  if (!comment) return [];
  
  // 疾病に関連するキーワード（必要に応じて追加可能）
  const DISEASE_KEYWORDS = [
    // 既存のキーワード
    '屈腱炎', '骨折', '腫れ', '熱感', '骨瘤', 'ソエ', 
    '管骨瘤', '飛節炎', '球節炎', '靭帯炎', '骨膜炎',
    '跛行', '跛る', '腫脹', '炎症', '裂離', '亀裂',
    '変形', '捻挫', '脱臼', '断裂', '損傷',
    '関節炎', '腱鞘炎', '筋肉痛', '肉離れ', '神経痛',
    
    // 以前に追加したキーワード
    '大腸炎', '下痢', '食欲不振', '肝機能障害', '腎機能障害',
    '疝痛', '横紋筋融解症', 'こり症', '筋肉炎', '蹄葉炎',
    '裂蹄', '挫跖', '蹄中隔炎', '蹄の亀裂', '蹄不安',
    '寝ちがい', '蹄傷', '蹄底負傷', '蹄球損傷', '蹄内出血',
    '旋回癖', '神経麻痺', 'さく癖', '打撲', '擦過傷',
    '裂傷', '創傷', '皮膚炎', '外傷性鼻出血', '角膜炎',
    '白内障', '視力低下', '眼球損傷', 'ウイルス性疾患', '鶏跛',
    '感染症', '発熱', '熱発', 'コズミ', 'インフルエンザ',
    '皮膚病', '疥癬', '水腫', '腹水', '寄生虫',
    
    // 新たに追加するキーワード
    'ボーンシスト', '蟻洞', 'フレグモーネ', 'エクイロックス', 'DDSP',
    '脚部不安', '繋靭帯炎', '脛骨骨折', '脛骨疲労骨折', '膝関節炎',
    '骨片除去手術', '骨片', '骨膜肥厚', '脚元不安', '深屈腱炎',
    '浅屈腱炎', '前膝腱炎', '腱不全', '腱損傷', 'じん帯損傷',
    '喉鳴り', '喘鳴症', '喉頭蓋エントラップメント', '喉頭蓋炎', '鼻出血',
    '気管支炎', '肺出血', '呼吸器不安', '上気道炎', '腸捻転', '鼓腸症', '胃潰瘍'
  ];

  // 既存のタグをセットに追加
  const foundTags = new Set([...existingTags]);

  // コメントからキーワードを検索
  DISEASE_KEYWORDS.forEach(keyword => {
    if (comment.includes(keyword)) {
      foundTags.add(keyword);
    }
  });

  return Array.from(foundTags);
}

/**
 * 疾病タグをレンダリングするためのコンポーネント
 */
interface DiseaseTagsProps {
  tags: string | string[] | undefined;
  className?: string;
}


export const DiseaseTags: React.FC<DiseaseTagsProps> = ({
  tags,
  className = ''
}): ReactElement | null => {
  if (!tags) return null;
  
  const tagList = Array.isArray(tags) ? tags : [tags];
  
  if (tagList.length === 0) return null;
  
  return (
    <div className={`flex flex-wrap gap-2 ${className}`}>
      {tagList.map((tag: string, index: number) => (
        <span 
          key={index} 
          className="px-2 py-1 text-xs font-medium rounded-full bg-red-100 text-red-800"
        >
          {tag}
        </span>
      ))}
    </div>
  );
};
