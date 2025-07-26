import { Horse } from '../types/horse';

export type MissingField = {
  field: string;
  label: string;
  severity: 'error' | 'warning' | 'info';
};

export const checkMissingData = (horse: Horse): MissingField[] => {
  const missingFields: MissingField[] = [];
  
  // Required fields that should always be present
  const requiredFields: Array<{
    key: keyof Horse;
    label: string;
    severity: 'error' | 'warning' | 'info';
  }> = [
    { key: 'name', label: '馬名', severity: 'error' },
    { key: 'sex', label: '性別', severity: 'error' },
    { key: 'age', label: '年齢', severity: 'error' },
    { key: 'sire', label: '父', severity: 'warning' },
    { key: 'dam', label: '母', severity: 'warning' },
    { key: 'dam_sire', label: '母父', severity: 'warning' },
    { key: 'weight', label: '馬体重', severity: 'warning' },
    { key: 'total_prize_latest', label: '獲得賞金', severity: 'info' },
    { key: 'comment', label: 'コメント', severity: 'info' },
  ];

  // Check each required field
  requiredFields.forEach(({ key, label, severity }) => {
    const value = horse[key as keyof Horse];
    let isMissing = false;

    if (value === null || value === undefined) {
      isMissing = true;
    } else if (Array.isArray(value)) {
      isMissing = value.length === 0 || value.every(item => !item);
    } else if (typeof value === 'string') {
      isMissing = value.trim() === '';
    } else if (typeof value === 'number') {
      isMissing = value <= 0;
    }

    if (isMissing) {
      missingFields.push({ field: key, label, severity });
    }
  });

  return missingFields;
};

export const getMissingDataSummary = (horses: Horse[]) => {
  const summary = {
    totalHorses: horses.length,
    missingFields: {
      name: 0,
      sex: 0,
      age: 0,
      sire: 0,
      dam: 0,
      dam_sire: 0,
      weight: 0,
      total_prize_latest: 0,
      comment: 0,
    },
    horsesWithMissingData: new Set<number>(),
  };

  horses.forEach((horse) => {
    const missingFields = checkMissingData(horse);
    if (missingFields.length > 0) {
      summary.horsesWithMissingData.add(horse.id);
      missingFields.forEach(({ field }) => {
        summary.missingFields[field as keyof typeof summary.missingFields]++;
      });
    }
  });

  return {
    ...summary,
    horsesWithMissingData: Array.from(summary.horsesWithMissingData),
  };
};
