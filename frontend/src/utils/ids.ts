export function normalizeId(input: unknown): string {
  return String(input ?? '').trim();
}

export function isNumericId(id: string): boolean {
  return /^\d+$/.test(id);
}

export function normalizeName(s: unknown): string {
  return String(s ?? '')
    .toLowerCase()
    .replace(/[\s\u3000]/g, '');
}

export function matchHorseCandidate(
  horse: any,
  targetId: string,
  baseName?: string,
  baseAge?: number | string | null
): boolean {
  const idMatch = String(horse?.id) === targetId;
  const auctionMatch = horse?.auction_id && String(horse.auction_id) === targetId;
  if (idMatch || auctionMatch) return true;

  if (baseName) {
    const nameOk = normalizeName(horse?.name) === normalizeName(baseName);
    if (!nameOk) return false;
    if (baseAge === undefined || baseAge === null || baseAge === '') return nameOk;
    const ageNum = Number(horse?.age);
    const baseAgeNum = Number(baseAge);
    if (!Number.isNaN(ageNum) && !Number.isNaN(baseAgeNum)) {
      return nameOk && ageNum === baseAgeNum;
    }
    return nameOk;
  }

  return false;
}
