import { apiRequest } from './api';
import { UserHistoryItem, UserSpendingResponse } from '../types';

export async function getMySpending(token: string): Promise<UserSpendingResponse> {
  return apiRequest<UserSpendingResponse>('/users/me/spending', {
    headers: { authorization: `Bearer ${token}` },
  });
}

export async function getMyHistory(token: string): Promise<UserHistoryItem[]> {
  return apiRequest<UserHistoryItem[]>('/users/me/history', {
    headers: { authorization: `Bearer ${token}` },
  });
}
