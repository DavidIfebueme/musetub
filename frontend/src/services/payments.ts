import { apiRequest } from './api';

export type ChannelResponse = {
  id: string;
  content_id: string;
  status: string;
  price_per_second_locked: number;
  total_seconds_streamed: number;
  total_amount_owed: number;
  total_amount_settled: number;
  escrow_address: string | null;
  usdc_address: string | null;
};

export type TickResponse = ChannelResponse & {
  tick_seconds: number;
  did_settle: boolean;
  settlement_tx_id: string | null;
  settlement_amount: number | null;
};

export async function openChannel(token: string, contentId: string): Promise<ChannelResponse> {
  return apiRequest<ChannelResponse>('/payments/channel/open', {
    method: 'POST',
    headers: { 'content-type': 'application/json', authorization: `Bearer ${token}` },
    body: JSON.stringify({ content_id: contentId }),
  });
}

export async function tickChannel(token: string, channelId: string): Promise<TickResponse> {
  return apiRequest<TickResponse>('/payments/channel/tick', {
    method: 'POST',
    headers: { 'content-type': 'application/json', authorization: `Bearer ${token}` },
    body: JSON.stringify({ channel_id: channelId }),
  });
}

export async function closeChannel(token: string, channelId: string): Promise<TickResponse> {
  return apiRequest<TickResponse>('/payments/channel/close', {
    method: 'POST',
    headers: { 'content-type': 'application/json', authorization: `Bearer ${token}` },
    body: JSON.stringify({ channel_id: channelId }),
  });
}
