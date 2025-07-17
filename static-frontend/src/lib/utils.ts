// UIコンポーネント用のクラス名結合ユーティリティ
// 複数のクラス名を受け取り、真偽値でフィルタして空白区切りの文字列として返す
// 例: cn('a', false && 'b', 'c') → 'a c'
export function cn(...classes: (string | undefined | null | false)[]): string {
  return classes.filter(Boolean).join(' ');
} 