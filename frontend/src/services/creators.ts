import { apiRequest } from './api';
import { CreatorDashboardResponse, WithdrawResponse } from '../types';

export async function getCreatorDashboard(token: string): Promise<CreatorDashboardResponse> {
  return apiRequest<CreatorDashboardResponse>('/creators/dashboard', {
    headers: { authorization: `Bearer ${token}` },
  });
}

export async function withdrawCreator(token: string): Promise<WithdrawResponse> {
  return apiRequest<WithdrawResponse>('/creators/withdraw', {
    method: 'POST',
    headers: { authorization: `Bearer ${token}` },
  });
}
