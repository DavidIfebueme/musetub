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

export type CircleTransactionResponse = {
  id: string;
  state: string;
  tx_hash?: string | null;
  block_height?: number | null;
  error_reason?: string | null;
  error_details?: string | null;
  contract_address?: string | null;
  abi_function_signature?: string | null;
  ref_id?: string | null;
  wallet_id?: string | null;
  create_date?: string | null;
  update_date?: string | null;
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

export async function getCircleTransaction(token: string, txId: string): Promise<CircleTransactionResponse> {
  return apiRequest<CircleTransactionResponse>(`/wallets/transactions/${encodeURIComponent(txId)}`, {
    method: 'GET',
    headers: { authorization: `Bearer ${token}` },
  });
}
