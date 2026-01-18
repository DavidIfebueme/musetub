import { apiRequest } from './api';

export type TokenResponse = { access_token: string };

export type Me = {
  id: string;
  email: string;
  is_creator: boolean;
  wallet_address: string | null;
  circle_wallet_id: string | null;
};

const storageKey = 'musetub_token';

export function getStoredAuthToken(): string | null {
  return localStorage.getItem(storageKey);
}

export function clearAuthToken(): void {
  localStorage.removeItem(storageKey);
}

function storeAuthToken(token: string): void {
  localStorage.setItem(storageKey, token);
}

export async function login(email: string, password: string): Promise<TokenResponse> {
  const resp = await apiRequest<TokenResponse>('/auth/login', {
    method: 'POST',
    headers: { 'content-type': 'application/json' },
    body: JSON.stringify({ email, password }),
  });
  storeAuthToken(resp.access_token);
  return resp;
}

export async function register(email: string, password: string, isCreator: boolean): Promise<TokenResponse> {
  const resp = await apiRequest<TokenResponse>('/auth/register', {
    method: 'POST',
    headers: { 'content-type': 'application/json' },
    body: JSON.stringify({ email, password, is_creator: isCreator }),
  });
  storeAuthToken(resp.access_token);
  return resp;
}

export async function getMe(token: string): Promise<Me> {
  return apiRequest<Me>('/auth/me', {
    headers: { authorization: `Bearer ${token}` },
  });
}
