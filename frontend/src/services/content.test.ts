import { describe, it, expect, vi } from 'vitest';

import { getContent, listContent } from './content';

vi.mock('./api', () => {
  return {
    apiRequest: vi.fn(async () => ({ ok: true })),
    getApiBaseUrl: vi.fn(() => 'http://example.test'),
    ApiError: class ApiError extends Error {
      constructor(message: string, readonly status: number) {
        super(message);
      }
    },
  };
});

describe('content service', () => {
  it('calls list content', async () => {
    const { apiRequest } = await import('./api');
    await listContent();
    expect(apiRequest).toHaveBeenCalledWith('/content');
  });

  it('calls get content by id', async () => {
    const { apiRequest } = await import('./api');
    await getContent('abc');
    expect(apiRequest).toHaveBeenCalledWith('/content/abc');
  });
});
