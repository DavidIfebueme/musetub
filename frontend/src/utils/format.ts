export function formatUsdcMinor(value: number | string | null | undefined, decimals = 4): string {
  if (value === null || value === undefined) return '—';
  const num = typeof value === 'string' ? Number(value) : value;
  if (!Number.isFinite(num)) return '—';
  return (num / 1_000_000).toFixed(decimals);
}

export function formatUsdcDecimal(value: number | string | null | undefined, decimals = 4): string {
  if (value === null || value === undefined) return '—';
  const num = typeof value === 'string' ? Number(value) : value;
  if (!Number.isFinite(num)) return '—';
  return num.toFixed(decimals);
}
