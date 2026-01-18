import { describe, it, expect, vi } from 'vitest';

import { fundTestnet } from './wallets';

vi.mock('./api', () => {
  return {
    apiRequest: vi.fn(async () => ({ ok: true })),
  };
});

describe('wallets service', () => {
  it('calls fund-testnet with bearer token', async () => {
    const { apiRequest } = await import('./api');
    await fundTestnet('t1');
    expect(apiRequest).toHaveBeenCalledWith('/wallets/fund-testnet', {
      method: 'POST',
      headers: { authorization: 'Bearer t1' },
    });
  });
});
