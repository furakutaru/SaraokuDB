import React from 'react';
import { Alert, AlertTitle, Button, Collapse, Box } from '@mui/material';
import { MissingField } from '../utils/dataValidation';

interface MissingDataAlertProps {
  missingFields: MissingField[];
  horseName: string;
  onFixClick?: () => void;
  showFixButton?: boolean;
}

export const MissingDataAlert: React.FC<MissingDataAlertProps> = ({
  missingFields,
  horseName,
  onFixClick,
  showFixButton = true,
}) => {
  if (missingFields.length === 0) return null;

  // Group fields by severity
  const errorFields = missingFields.filter(f => f.severity === 'error');
  const warningFields = missingFields.filter(f => f.severity === 'warning');
  const infoFields = missingFields.filter(f => f.severity === 'info');

  // Determine overall alert severity
  const overallSeverity = 
    errorFields.length > 0 ? 'error' : 
    warningFields.length > 0 ? 'warning' : 'info';

  // Format field list
  const formatFieldList = (fields: MissingField[]) => 
    fields.map(f => f.label).join(', ');

  return (
    <Alert 
      severity={overallSeverity}
      sx={{ mb: 2 }}
      action={
        showFixButton && onFixClick && (
          <Button 
            color="inherit" 
            size="small"
            onClick={onFixClick}
          >
            修正する
          </Button>
        )
      }
    >
      <AlertTitle>
        {horseName} のデータに不足があります
      </AlertTitle>
      
      {errorFields.length > 0 && (
        <Box component="div" mt={1}>
          <strong>必須データ:</strong> {formatFieldList(errorFields)}
        </Box>
      )}
      
      {warningFields.length > 0 && (
        <Box component="div" mt={1}>
          <strong>推奨データ:</strong> {formatFieldList(warningFields)}
        </Box>
      )}
      
      {infoFields.length > 0 && (
        <Box component="div" mt={1}>
          <strong>補足データ:</strong> {formatFieldList(infoFields)}
        </Box>
      )}
    </Alert>
  );
};

// Dashboard summary alert component
interface MissingDataSummaryAlertProps {
  summary: ReturnType<typeof import('../utils/dataValidation').getMissingDataSummary>;
  onViewDetails?: () => void;
}

export const MissingDataSummaryAlert: React.FC<MissingDataSummaryAlertProps> = ({
  summary,
  onViewDetails,
}) => {
  const { totalHorses, missingFields, horsesWithMissingData } = summary;
  const missingCount = horsesWithMissingData.length;
  const missingPercentage = Math.round((missingCount / totalHorses) * 100);

  if (missingCount === 0) {
    return (
      <Alert severity="success" sx={{ mb: 3 }}>
        すべての馬の必須データが揃っています！
      </Alert>
    );
  }

  return (
    <Alert 
      severity="warning" 
      sx={{ mb: 3 }}
      action={
        onViewDetails && (
          <Button color="inherit" size="small" onClick={onViewDetails}>
            詳細を表示
          </Button>
        )
      }
    >
      <AlertTitle>
        {missingCount}/{totalHorses} 頭 ({missingPercentage}%) の馬に不足データがあります
      </AlertTitle>
      
      <Box component="div" mt={1}>
        <strong>不足している主なデータ:</strong>
        <Box component="ul" pl={2} mt={0.5}>
          {Object.entries(missingFields)
            .filter(([_, count]) => count > 0)
            .sort((a, b) => b[1] - a[1])
            .map(([field, count]) => (
              <li key={field}>
                {getFieldLabel(field)}: {count}頭
              </li>
            ))}
        </Box>
      </Box>
    </Alert>
  );
};

// Helper function to get field labels
const getFieldLabel = (field: string): string => {
  const labels: Record<string, string> = {
    name: '馬名',
    sex: '性別',
    age: '年齢',
    sire: '父',
    dam: '母',
    dam_sire: '母父',
    weight: '馬体重',
    total_prize_latest: '獲得賞金',
    comment: 'コメント',
  };
  
  return labels[field] || field;
};
