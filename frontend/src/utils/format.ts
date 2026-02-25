// Utility functions for formatting
export const formatPrize = (prize: number, raceRecords?: any): string => {
  const totalRaces = raceRecords?.total_races ?? 0;

  if (!prize || prize === 0) {
    if (totalRaces > 0) {
      return '0万円';
    }
    return '未出走';
  }
  return `${(prize / 10000).toLocaleString()}万円`;
};
