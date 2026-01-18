import { apiRequest } from './api';
import { FundTestnetResponse } from '../types';

export async function fundTestnet(token: string): Promise<FundTestnetResponse> {
  return apiRequest<FundTestnetResponse>('/wallets/fund-testnet', {
    method: 'POST',
    headers: { authorization: `Bearer ${token}` },
  });
}
