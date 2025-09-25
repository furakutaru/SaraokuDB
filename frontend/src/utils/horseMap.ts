export interface HorseHistoryUI {
  auction_date: string;
  name: string;
  sex: string;
  age: string;
  seller: string;
  race_record: string;
  comment: string;
  sold_price: number | null;
  total_prize_start: number;
  unsold?: boolean;
  detail_url?: string;
  primary_image?: string;
  disease_tags?: string;
  weight?: number;
}

export interface HorseUI {
  id: any;
  name: string;
  sex: string;
  age: string;
  color: string;
  birthday: string;
  history: HorseHistoryUI[];
  sire: string;
  dam: string;
  dam_sire: string;
  primary_image: string;
  disease_tags: string;
  jbis_url: string;
  weight?: number;
  unsold_count?: number;
  total_prize_latest: number;
  created_at: string;
  updated_at: string;
  unsold?: boolean;
}

export function buildUIHorse(base: any, fallbackId: string): HorseUI {
  const history: HorseHistoryUI = {
    auction_date: base.auction_date || new Date().toISOString().split('T')[0],
    name: base.name || '不明',
    sex: base.sex || '不明',
    age: String(base.age ?? '0'),
    seller: base.seller || '不明',
    race_record: base.race_record || '未出走',
    comment: base.comment || '',
    sold_price: base.sold_price ?? null,
    total_prize_start: base.total_prize_start ?? 0,
    unsold: (base.unsold ?? false) || (base.is_unsold ?? false) || (base.unsold_count > 0),
    detail_url: base.auction_url || '',
    primary_image: base.primary_image || base.image_url || '',
    disease_tags: Array.isArray(base.disease_tags) ? base.disease_tags.join(',') : (base.disease_tags || ''),
    weight: base.weight,
  };
  return {
    id: base.id ?? fallbackId,
    name: base.name || '不明',
    sex: base.sex || '不明',
    age: String(base.age ?? '0'),
    color: base.color || '不明',
    birthday: base.birthday || '不明',
    history: [history],
    sire: base.sire || '不明',
    dam: base.dam || '不明',
    dam_sire: base.dam_sire || base.damsire || '不明',
    primary_image: base.primary_image || base.image_url || '',
    disease_tags: Array.isArray(base.disease_tags) ? base.disease_tags.join(',') : (base.disease_tags || ''),
    jbis_url: base.jbis_url || '',
    weight: base.weight,
    unsold_count: base.unsold_count || 0,
    total_prize_latest: base.total_prize_latest ?? 0,
    created_at: base.created_at || new Date().toISOString(),
    updated_at: base.updated_at || new Date().toISOString(),
    unsold: (base.unsold ?? false) || (base.is_unsold ?? false) || (base.unsold_count > 0),
  };
}
