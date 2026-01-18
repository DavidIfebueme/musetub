import { apiRequest, ApiError, getApiBaseUrl } from './api';
import { ContentItem, ContentResponse } from '../types';

export async function listContent(): Promise<ContentItem[]> {
  return apiRequest<ContentItem[]>('/content');
}

export async function getContent(contentId: string): Promise<ContentResponse> {
  return apiRequest<ContentResponse>(`/content/${encodeURIComponent(contentId)}`);
}

export async function uploadContent(
  token: string,
  args: {
    file: File;
    title: string;
    description: string;
    content_type: string;
    duration_seconds: number;
    resolution: string;
    bitrate_tier: string;
    engagement_intent: string;
  },
): Promise<ContentResponse> {
  const form = new FormData();
  form.append('file', args.file);
  form.append('title', args.title);
  form.append('description', args.description);
  form.append('content_type', args.content_type);
  form.append('duration_seconds', String(args.duration_seconds));
  form.append('resolution', args.resolution);
  form.append('bitrate_tier', args.bitrate_tier);
  form.append('engagement_intent', args.engagement_intent);

  const url = `${getApiBaseUrl()}/content/upload`;
  const resp = await fetch(url, {
    method: 'POST',
    headers: { authorization: `Bearer ${token}` },
    body: form,
  });

  const contentType = resp.headers.get('content-type') ?? '';
  const isJson = contentType.includes('application/json');
  const data = isJson ? await resp.json().catch(() => null) : await resp.text().catch(() => null);

  if (!resp.ok) {
    const msg = typeof data === 'string' ? data : (data?.detail ?? data?.error ?? resp.statusText);
    throw new ApiError(String(msg), resp.status);
  }

  return data as ContentResponse;
}
