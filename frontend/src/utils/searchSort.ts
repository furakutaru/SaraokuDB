export type SortOrder = 'asc' | 'desc';

export function filterHorsesByTerm<T extends { name?: string; sire?: string | null; dam?: string | null; damsire?: string | null; seller?: string | null }>(
  horses: T[],
  term: string
): T[] {
  const q = (term || '').toLowerCase();
  if (!q) return [...horses];
  return horses.filter(h => {
    const name = (h.name || '').toLowerCase();
    const sire = (h.sire || '').toLowerCase();
    const dam = (h.dam || '').toLowerCase();
    const damsire = (h.damsire || '').toLowerCase();
    const seller = (h.seller || '').toLowerCase();
    return name.includes(q) || sire.includes(q) || dam.includes(q) || damsire.includes(q) || seller.includes(q);
  });
}

export function sortHorses<T extends Record<string, any>>(
  horses: T[],
  sortBy: 'name' | 'age' | 'auction_date' | 'sold_price' | 'total_prize_latest',
  order: SortOrder
): T[] {
  const arr = [...horses];
  arr.sort((a, b) => {
    let comparison = 0;
    switch (sortBy) {
      case 'name':
        comparison = String(a.name || '').localeCompare(String(b.name || ''));
        break;
      case 'sold_price':
        comparison = Number(a.sold_price || 0) - Number(b.sold_price || 0);
        break;
      case 'age':
        comparison = Number(a.age || 0) - Number(b.age || 0);
        break;
      case 'auction_date':
        const dateA = a.auction_date ? new Date(a.auction_date).getTime() : 0;
        const dateB = b.auction_date ? new Date(b.auction_date).getTime() : 0;
        comparison = dateA - dateB;
        break;
      case 'total_prize_latest':
        comparison = Number(a.total_prize_latest || 0) - Number(b.total_prize_latest || 0);
        break;
    }
    return order === 'asc' ? comparison : -comparison;
  });
  return arr;
}
