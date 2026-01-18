import { describe, it, expect, vi } from 'vitest';

import { getMyHistory, getMySpending } from './users';

vi.mock('./api', () => {
  return {
    apiRequest: vi.fn(async () => ({ ok: true })),
  };
});

describe('users service', () => {
  it('calls spending with bearer token', async () => {
    const { apiRequest } = await import('./api');
    await getMySpending('t1');
    expect(apiRequest).toHaveBeenCalledWith('/users/me/spending', {
      headers: { authorization: 'Bearer t1' },
    });
  });

  it('calls history with bearer token', async () => {
    const { apiRequest } = await import('./api');
    await getMyHistory('t2');
    expect(apiRequest).toHaveBeenCalledWith('/users/me/history', {
      headers: { authorization: 'Bearer t2' },
    });
  });
});
