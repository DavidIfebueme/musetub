import express from 'express';
import 'dotenv/config';

import { BatchFacilitatorClient } from '@circlefin/x402-batching/server';
import { GatewayClient } from '@circlefin/x402-batching/client';

const gatewayUrl = process.env.GATEWAY_URL;

const client = gatewayUrl ? new BatchFacilitatorClient({ url: gatewayUrl }) : new BatchFacilitatorClient();

let supportedCache: { value: unknown; expiresAt: number } | null = null;
const SUPPORTED_TTL_MS = 5 * 60 * 1000;

const apiBaseUrl = process.env.API_BASE_URL || 'http://localhost:8000/api/v1';
const privateKey = process.env.PRIVATE_KEY as `0x${string}` | undefined;

const app = express();
app.use(express.json({ limit: '1mb' }));

app.get('/health', (_req, res) => {
  res.json({ ok: true });
});

app.get('/supported', async (_req, res) => {
  try {
    const now = Date.now();
    if (supportedCache && supportedCache.expiresAt > now) {
      return res.json(supportedCache.value);
    }
    const supported = await client.getSupported();
    supportedCache = { value: supported, expiresAt: now + SUPPORTED_TTL_MS };
    return res.json(supported);
  } catch (e) {
    return res.status(502).json({ error: String(e) });
  }
});

app.post('/verify-settle', async (req, res) => {
  const paymentPayload = req.body?.paymentPayload;
  const requirements = req.body?.requirements;

  if (!paymentPayload || !requirements) {
    return res.status(400).json({ error: 'paymentPayload and requirements required' });
  }

  const verifyResult = await client.verify(paymentPayload, requirements);
  if (!verifyResult.isValid) {
    return res.status(400).json({ error: verifyResult.invalidReason || 'invalid' });
  }

  const settleResult = await client.settle(paymentPayload, requirements);
  if (!settleResult.success) {
    return res.status(400).json({ error: settleResult.errorReason || 'settle_failed' });
  }

  return res.json({
    transaction: settleResult.transaction,
    payer: settleResult.payer || 'unknown'
  });
});

app.post('/pay', async (req, res) => {
  try {
    const contentId = req.body?.contentId;
    const accessToken = req.body?.accessToken;
    const baseUrlOverride = req.body?.apiBaseUrl;

    if (!privateKey) {
      return res.status(503).json({ error: 'PRIVATE_KEY not configured' });
    }

    if (!contentId || !accessToken) {
      return res.status(400).json({ error: 'contentId and accessToken required' });
    }

    const baseUrl = typeof baseUrlOverride === 'string' && baseUrlOverride ? baseUrlOverride : apiBaseUrl;
    const url = `${baseUrl}/content/${encodeURIComponent(contentId)}/stream?access_token=${encodeURIComponent(accessToken)}`;

    const gateway = new GatewayClient({ chain: 'arcTestnet', privateKey });
    const balances: any = await gateway.getBalances();

    const gatewayAvailStr = String(balances?.gateway?.formattedAvailable ?? '0');
    const walletAvailStr = String(balances?.wallet?.formatted ?? balances?.wallet?.formattedAvailable ?? '0');
    const gatewayAvail = parseFloat(gatewayAvailStr);
    const walletAvail = parseFloat(walletAvailStr);

    if (!(gatewayAvail > 0)) {
      // The Circle Gateway deposit flow enforces a minimum deposit (commonly 1 USDC).
      // If the funding wallet doesn't have enough, fail fast with a clear message.
      if (!(walletAvail >= 1)) {
        return res.status(402).json({
          error: 'Insufficient USDC to fund gateway deposit (need >= 1 USDC in wallet)',
          wallet_available: walletAvailStr,
          gateway_available: gatewayAvailStr,
        });
      }

      await gateway.deposit('1');
    }

    const result = await gateway.pay<{ playback_url: string }>(url);
    return res.json({
      playback_url: result.data.playback_url,
      transaction: result.transaction,
      formatted_amount: result.formattedAmount,
    });
  } catch (e) {
    return res.status(502).json({ error: String(e) });
  }
});

const port = Number(process.env.PORT || 4010);
app.listen(port, () => {
  console.log(`x402 sidecar listening on ${port}`);
});
