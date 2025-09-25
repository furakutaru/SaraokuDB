export function normalizeImageUrl(baseUrl: string | undefined, url: string | null | undefined): string {
  const src = url || '';
  if (!src) return '';
  if (src.startsWith('http') || src.startsWith('data:')) return src;
  const base = baseUrl || 'http://localhost:8001';
  return `${base}${src.startsWith('/') ? '' : '/'}${src}`;
}
