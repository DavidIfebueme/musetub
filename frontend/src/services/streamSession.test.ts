import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';

import { PaymentStreamSession } from './streamSession';

vi.mock('./payments', () => {
  return {
    openChannel: vi.fn(async () => ({ id: 'ch_1' })),
    tickChannel: vi.fn(async () => ({ tick_seconds: 10 })),
    closeChannel: vi.fn(async () => ({ tick_seconds: 0 })),
  };
});

describe('PaymentStreamSession', () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it('ticks immediately and on interval', async () => {
    const onTick = vi.fn();
    const onError = vi.fn();

    const session = new PaymentStreamSession({
      token: 't',
      contentId: 'c',
      pricePerSecondMinor: 2,
      onTick,
      onError,
    });

    await session.start();
    expect(onError).not.toHaveBeenCalled();
    expect(onTick).toHaveBeenCalledWith(20);

    await vi.advanceTimersByTimeAsync(10_000);
    expect(onTick).toHaveBeenCalledTimes(2);

    await session.stop();
  });
});
