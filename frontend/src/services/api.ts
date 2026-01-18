export class ApiError extends Error {
  constructor(
    message: string,
    readonly status: number,
  ) {
    super(message);
  }
}

const baseUrl = (import.meta.env.VITE_API_BASE_URL as string | undefined) ?? 'http://localhost:8000/api/v1';

export async function apiRequest<T>(path: string, init?: RequestInit): Promise<T> {
  const url = `${baseUrl}${path}`;
  const resp = await fetch(url, init);

  const contentType = resp.headers.get('content-type') ?? '';
  const isJson = contentType.includes('application/json');
  const data = isJson ? await resp.json().catch(() => null) : await resp.text().catch(() => null);

  if (!resp.ok) {
    const msg = typeof data === 'string' ? data : (data?.detail ?? data?.error ?? resp.statusText);
    throw new ApiError(String(msg), resp.status);
  }

  return data as T;
}
