import { apiRequest } from './api';
import { FundTestnetResponse } from '../types';

export type ArcBlockHeightResponse = {
  block_height: number;
};

export type UsdcBalanceResponse = {
  wallet_address: string;
  usdc_address: string;
  balance_minor: number;
  balance: string;
};

export async function fundTestnet(token: string): Promise<FundTestnetResponse> {
  return apiRequest<FundTestnetResponse>('/wallets/fund-testnet', {
    method: 'POST',
    headers: { authorization: `Bearer ${token}` },
  });
}

export async function getArcBlockHeight(): Promise<ArcBlockHeightResponse> {
  return apiRequest<ArcBlockHeightResponse>('/wallets/arc-block-height', {
    method: 'GET',
  });
}

export async function getUsdcBalance(token: string): Promise<UsdcBalanceResponse> {
  return apiRequest<UsdcBalanceResponse>('/wallets/usdc-balance', {
    method: 'GET',
    headers: { authorization: `Bearer ${token}` },
  });
}
