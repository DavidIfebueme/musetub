import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';

import { PaymentStreamSession } from './streamSession';

const { X402PaymentRequiredError } = vi.hoisted(() => {
  class X402PaymentRequiredError extends Error {
    constructor(readonly body: any) {
      super('Payment required');
    }
  }
  return { X402PaymentRequiredError };
});

vi.mock('./stream', () => {
  return {
    getStreamPlaybackUrl: vi.fn(async () => ({ playbackUrl: 'http://x/y' })),
    X402PaymentRequiredError,
  };
});

describe('PaymentStreamSession', () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it('ticks on interval', async () => {
    const onTick = vi.fn();
    const onError = vi.fn();
    const onPaymentRequired = vi.fn();

    const session = new PaymentStreamSession({
      token: 't',
      contentId: 'c',
      pricePerSecondMinor: 2,
      onTick,
      onError,
      onPaymentRequired,
    });

    await session.start();
    expect(onError).not.toHaveBeenCalled();
    expect(onTick).not.toHaveBeenCalled();

    await vi.advanceTimersByTimeAsync(10_000);
    expect(onTick).toHaveBeenCalledWith(20);
    expect(onTick).toHaveBeenCalledTimes(1);

    await session.stop();
  });

  it('stops and surfaces paywall on 402', async () => {
    const stream = await import('./stream');
    (stream.getStreamPlaybackUrl as unknown as ReturnType<typeof vi.fn>).mockRejectedValueOnce(
      new X402PaymentRequiredError({
        x402Version: 2,
        resource: { url: 'u', description: 'd', mimeType: 'application/json' },
        accepts: [],
      } as any),
    );

    const onTick = vi.fn();
    const onError = vi.fn();
    const onPaymentRequired = vi.fn();

    const session = new PaymentStreamSession({
      token: 't',
      contentId: 'c',
      pricePerSecondMinor: 2,
      onTick,
      onError,
      onPaymentRequired,
    });

    await session.start();
    await vi.advanceTimersByTimeAsync(10_000);

    expect(onPaymentRequired).toHaveBeenCalledTimes(1);
    expect(onTick).not.toHaveBeenCalled();
  });
});
