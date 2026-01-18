import express from 'express';
import 'dotenv/config';

import { BatchFacilitatorClient } from '@circlefin/x402-batching/server';

const gatewayUrl = process.env.GATEWAY_URL;
if (!gatewayUrl) {
  throw new Error('GATEWAY_URL is required');
}

const client = new BatchFacilitatorClient({ url: gatewayUrl });

const app = express();
app.use(express.json({ limit: '1mb' }));

app.get('/health', (_req, res) => {
  res.json({ ok: true });
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

const port = Number(process.env.PORT || 4010);
app.listen(port, () => {
  console.log(`x402 sidecar listening on ${port}`);
});
