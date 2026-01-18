export type ContentItem = {
  id: string;
  creator_id: string;
  title: string;
  content_type: string;
  duration_seconds: number;
  price_per_second: number;
  quality_score: number;
  playback_url: string;
  created_at: string;
};

export type ContentResponse = {
  id: string;
  creator_id: string;
  title: string;
  description: string;
  content_type: string;
  duration_seconds: number;
  resolution: string;
  bitrate_tier: string;
  engagement_intent: string;
  quality_score: number;
  suggested_price_per_second: number;
  price_per_second: number;
  ipfs_cid: string;
  playback_url: string;
  pricing_explanation: string;
  created_at: string;
};

export type CreatorContentEarningsItem = {
  content_id: string;
  title: string;
  amount_gross: number;
  amount_creator: number;
};

export type CreatorSettlementItem = {
  id: string;
  content_id: string;
  channel_id: string;
  amount_gross: number;
  amount_creator: number;
  tx_hash: string;
  created_at: string;
};

export type CreatorDashboardResponse = {
  total_amount_gross: number;
  total_amount_creator: number;
  earnings_by_content: CreatorContentEarningsItem[];
  recent_settlements: CreatorSettlementItem[];
};

export type WithdrawResponse = {
  tx_id: string;
};

export type StreamResponse = {
  playback_url: string;
};
