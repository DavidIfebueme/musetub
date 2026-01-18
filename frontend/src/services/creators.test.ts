import { describe, it, expect, vi } from 'vitest';

import { getCreatorDashboard, withdrawCreator } from './creators';

vi.mock('./api', () => {
  return {
    apiRequest: vi.fn(async () => ({ ok: true })),
  };
});

describe('creators service', () => {
  it('calls dashboard with bearer token', async () => {
    const { apiRequest } = await import('./api');
    await getCreatorDashboard('t1');
    expect(apiRequest).toHaveBeenCalledWith('/creators/dashboard', {
      headers: { authorization: 'Bearer t1' },
    });
  });

  it('calls withdraw with bearer token', async () => {
    const { apiRequest } = await import('./api');
    await withdrawCreator('t2');
    expect(apiRequest).toHaveBeenCalledWith('/creators/withdraw', {
      method: 'POST',
      headers: { authorization: 'Bearer t2' },
    });
  });
});
