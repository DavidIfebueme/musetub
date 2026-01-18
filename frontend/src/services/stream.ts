import { ApiError, getApiBaseUrl } from './api';

export type StreamResponse = {
  playback_url: string;
};

export type X402Accept = {
  scheme: string;
  asset: string;
  amount: string;
  network: string;
  payTo: string;
  maxTimeoutSeconds?: number;
  extra?: Record<string, unknown>;
};

export type X402PaymentRequiredBody = {
  x402Version: 2;
  error?: string;
  resource: {
    url: string;
    description: string;
    mimeType: string;
  };
  accepts: X402Accept[];
};

export class X402PaymentRequiredError extends Error {
  constructor(readonly body: X402PaymentRequiredBody) {
    super('Payment required');
  }
}

export type StreamResult = {
  playbackUrl: string;
  paymentResponseHeader?: string;
};

export function createPaymentSignature(accepted: X402Accept): string {
  const payload = { accepted };
  const raw = new TextEncoder().encode(JSON.stringify(payload));
  let binary = '';
  raw.forEach((b) => {
    binary += String.fromCharCode(b);
  });
  return btoa(binary);
}

export async function getStreamPlaybackUrl(
  token: string,
  contentId: string,
  paymentSignature?: string,
): Promise<StreamResult> {
  const url = `${getApiBaseUrl()}/content/${encodeURIComponent(contentId)}/stream?access_token=${encodeURIComponent(token)}`;
  const resp = await fetch(url, {
    headers: paymentSignature ? { 'Payment-Signature': paymentSignature } : undefined,
  });

  const contentType = resp.headers.get('content-type') ?? '';
  const isJson = contentType.includes('application/json');

  if (resp.status === 402) {
    const body = (isJson ? await resp.json().catch(() => null) : null) as X402PaymentRequiredBody | null;
    if (!body) {
      throw new ApiError('Payment required', 402);
    }
    throw new X402PaymentRequiredError(body);
  }

  const data = isJson ? await resp.json().catch(() => null) : await resp.text().catch(() => null);
  if (!resp.ok) {
    const msg = typeof data === 'string' ? data : (data?.detail ?? data?.error ?? resp.statusText);
    throw new ApiError(String(msg), resp.status);
  }

  const paymentResponseHeader = resp.headers.get('Payment-Response') ?? undefined;

  return {
    playbackUrl: (data as StreamResponse).playback_url,
    paymentResponseHeader,
  };
}

export async function autoPayStream(token: string, contentId: string): Promise<StreamResult> {
  const url = `${getApiBaseUrl()}/content/${encodeURIComponent(contentId)}/pay?access_token=${encodeURIComponent(token)}`;
  const resp = await fetch(url, { method: 'POST' });

  const contentType = resp.headers.get('content-type') ?? '';
  const isJson = contentType.includes('application/json');
  const data = isJson ? await resp.json().catch(() => null) : await resp.text().catch(() => null);

  if (!resp.ok) {
    const msg = typeof data === 'string' ? data : (data?.detail ?? data?.error ?? resp.statusText);
    throw new ApiError(String(msg), resp.status);
  }

  const paymentResponseHeader = resp.headers.get('Payment-Response') ?? undefined;
  return {
    playbackUrl: (data as StreamResponse).playback_url,
    paymentResponseHeader,
  };
}
