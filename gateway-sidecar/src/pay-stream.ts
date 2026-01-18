import 'dotenv/config';

import { GatewayClient } from '@circlefin/x402-batching/client';

const API_BASE_URL = process.env.API_BASE_URL || 'http://localhost:8000/api/v1';
const CONTENT_ID = process.env.CONTENT_ID;
const ACCESS_TOKEN = process.env.ACCESS_TOKEN;
const PRIVATE_KEY = process.env.PRIVATE_KEY as `0x${string}` | undefined;

if (!CONTENT_ID) {
  throw new Error('CONTENT_ID is required');
}

if (!ACCESS_TOKEN) {
  throw new Error('ACCESS_TOKEN is required');
}

if (!PRIVATE_KEY) {
  throw new Error('PRIVATE_KEY is required');
}

const url = `${API_BASE_URL}/content/${CONTENT_ID}/stream?access_token=${encodeURIComponent(ACCESS_TOKEN)}`;

async function main(): Promise<void> {
  const client = new GatewayClient({ chain: 'arcTestnet', privateKey: PRIVATE_KEY });

  const balances = await client.getBalances();
  console.log(`Wallet:  ${balances.wallet.formatted} USDC`);
  console.log(`Gateway: ${balances.gateway.formattedAvailable} USDC available`);

  if (parseFloat(balances.gateway.formattedAvailable) <= 0) {
    console.log('Depositing 1 USDC to Gateway...');
    const dep = await client.deposit('1');
    console.log(`Deposit tx: ${dep.transaction}`);
  }

  console.log(`Paying: ${url}`);
  const result = await client.pay<{ playback_url: string }>(url);

  console.log(`Paid: ${result.formattedAmount} USDC`);
  console.log(`Transaction: ${result.transaction}`);
  console.log(`Playback URL: ${result.data.playback_url}`);
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
