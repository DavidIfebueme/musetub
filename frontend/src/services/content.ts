import { apiRequest } from './api';
import { ContentItem } from '../types';

export async function listContent(): Promise<ContentItem[]> {
  return apiRequest<ContentItem[]>('/content');
}
