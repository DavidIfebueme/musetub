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
    engagement_intent: string;
  },
  onProgress?: (pct: number) => void,
): Promise<ContentResponse> {
  const form = new FormData();
  form.append('file', args.file);
  form.append('title', args.title);
  form.append('description', args.description);
  form.append('content_type', args.content_type);
  form.append('engagement_intent', args.engagement_intent);

  const url = `${getApiBaseUrl()}/content/upload`;

  return new Promise<ContentResponse>((resolve, reject) => {
    const xhr = new XMLHttpRequest();
    xhr.open('POST', url);
    xhr.setRequestHeader('authorization', `Bearer ${token}`);

    xhr.upload.addEventListener('progress', (e) => {
      if (e.lengthComputable && onProgress) {
        onProgress(Math.round((e.loaded / e.total) * 100));
      }
    });

    xhr.addEventListener('load', () => {
      let data: any;
      try {
        data = JSON.parse(xhr.responseText);
      } catch {
        data = xhr.responseText;
      }

      if (xhr.status >= 200 && xhr.status < 300) {
        resolve(data as ContentResponse);
      } else {
        const msg = typeof data === 'string' ? data : (data?.detail ?? data?.error ?? xhr.statusText);
        reject(new ApiError(String(msg), xhr.status));
      }
    });

    xhr.addEventListener('error', () => {
      reject(new ApiError('Network error during upload', 0));
    });

    xhr.addEventListener('abort', () => {
      reject(new ApiError('Upload cancelled', 0));
    });

    xhr.send(form);
  });
}
