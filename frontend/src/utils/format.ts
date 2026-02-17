// Utility functions for formatting
export const formatPrize = (prize: number, raceRecords?: any): string => {
  if (!prize || prize === 0) return '未出走';
  return `${(prize / 10000).toLocaleString()}万円`;
};
