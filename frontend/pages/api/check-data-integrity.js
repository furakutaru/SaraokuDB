// Simple mock API endpoint for data integrity check
export default function handler(req, res) {
  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  try {
    const data = req.body;
    
    // Basic validation
    if (!Array.isArray(data)) {
      return res.status(400).json({
        error: '無効なデータ形式です: 配列が必要です',
      });
    }

    let totalIssues = 0;
    const issues = [];
    const requiredFields = ['id', 'name', 'sex', 'age', 'sire', 'dam', 'damsire'];
    
    // Check each horse
    data.forEach((horse, index) => {
      const horseIssues = [];
      
      // Check required fields
      requiredFields.forEach(field => {
        if (!(field in horse) || horse[field] === null || horse[field] === '') {
          horseIssues.push({
            field,
            issue: '必須フィールドが不足しています',
            value: horse[field]
          });
          totalIssues++;
        }
      });

      // Check auction history
      if (!horse.auction_history || !Array.isArray(horse.auction_history) || horse.auction_history.length === 0) {
        horseIssues.push({
          field: 'auction_history',
          issue: 'オークション履歴がありません',
          value: horse.auction_history
        });
        totalIssues++;
      } else {
        // Check each auction history entry
        horse.auction_history.forEach((history, historyIndex) => {
          if (!history.auction_date) {
            horseIssues.push({
              field: `auction_history[${historyIndex}].auction_date`,
              issue: 'オークション日が設定されていません',
              value: history.auction_date
            });
            totalIssues++;
          }
        });
      }

      if (horseIssues.length > 0) {
        issues.push({
          id: horse.id || `horse-${index}`,
          name: horse.name || '名前不明',
          issues: horseIssues
        });
      }
    });

    // Prepare response
    const response = {
      summary: {
        total_horses: data.length,
        horses_with_issues: issues.length,
        total_issues: totalIssues
      },
      issues: issues
    };

    return res.status(200).json(response);

  } catch (error) {
    console.error('Error in check-data-integrity:', error);
    return res.status(500).json({
      error: 'データの整合性チェック中にエラーが発生しました',
      details: error.message
    });
  }
}
