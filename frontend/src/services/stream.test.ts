import { describe, it, expect, beforeEach, vi } from 'vitest';

import { getStreamPlaybackUrl, X402PaymentRequiredError } from './stream';

beforeEach(() => {
  vi.restoreAllMocks();
});

describe('getStreamPlaybackUrl', () => {
  it('returns playback url on 200', async () => {
    vi.spyOn(globalThis, 'fetch').mockResolvedValue(
      new Response(JSON.stringify({ playback_url: 'http://x/y' }), {
        status: 200,
        headers: { 'content-type': 'application/json', 'Payment-Response': 'abc' },
      }),
    );

    const resp = await getStreamPlaybackUrl('t', 'c');
    expect(resp.playbackUrl).toBe('http://x/y');
    expect(resp.paymentResponseHeader).toBe('abc');
  });

  it('throws X402PaymentRequiredError on 402', async () => {
    vi.spyOn(globalThis, 'fetch').mockResolvedValue(
      new Response(
        JSON.stringify({
          x402Version: 2,
          resource: 'http://localhost/resource',
          description: 'Stream',
          mimeType: 'application/json',
          accepts: [
            {
              scheme: 'exact',
              asset: '0x0',
              amount: '10',
              network: 'arc-testnet',
              payTo: '0xabc',
            },
          ],
        }),
        {
          status: 402,
          headers: { 'content-type': 'application/json' },
        },
      ),
    );

    await expect(getStreamPlaybackUrl('t', 'c')).rejects.toBeInstanceOf(X402PaymentRequiredError);
  });
});
