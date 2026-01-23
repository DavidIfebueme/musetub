# musetub

musetub is a pay-as-you-watch streaming demo: creators upload to ipfs, viewers stream, and payments are handled as small prepaid chunks.

the codebase is split into:
- backend: fastapi + async sqlalchemy (payments, credits, wallets, dashboards)
- frontend: react + vite (player + creator studio)
- contracts: foundry project (arc testnet escrow + mock usdc for local/dev)
- gateway-sidecar: x402 helper service (dev)

## how streaming + payments work

streaming is prepaid in fixed 10-second chunks.

- `POST /content/{id}/pay`
  - adds 10 seconds of local streaming credit for the user/content pair
  - when circle + arc are configured, it also submits an on-chain escrow payment using an erc-3009 authorization (usdc `receiveWithAuthorization`) via a circle contract execution transaction
- `POST /content/{id}/stream`
  - consumes 10 seconds of credit
  - if the user is out of credit, returns `402` with x402-style “accepts” info so the client can prompt for payment

the frontend video player calls `/stream` every 10 seconds while playing. on `402`, it pauses playback and shows the paywall.

## x402 in this repo

the backend uses `402 payment required` responses to indicate “you need to pay to keep going”. when enabled, the gateway sidecar can help with request signing / forwarding.

relevant env vars live in [backend/.env.example](backend/.env.example).

## on-chain escrow + withdraw

the escrow contract tracks balances in usdc:
- 90% to `creatorBalances[creator]`
- 10% to `platformBalance`

creator withdraw is an on-chain contract call (`withdrawCreator()`) submitted via circle.

notes:
- the creator wallet must have a little arc testnet native token to pay gas.
- if the creator has nothing accrued on-chain yet, `withdrawCreator()` reverts (custom error `NothingToWithdraw()`). the backend now pre-checks `creatorBalances(creator)` and returns a clean 400 instead of submitting a transaction that will fail gas estimation.
- you can poll circle transaction status via `GET /wallets/transactions/{tx_id}`.

## agentic pricing (lightweight)

uploads include structured metadata (duration, resolution, bitrate tier, engagement intent, etc). the backend uses deterministic heuristics to compute a suggested price/score.

gemini is used for narrative/explanation (text-only) and is intended to be cached / minimal, not the source of truth for pricing.

## local development

### 1) start infra (postgres/redis/ipfs + gateway sidecar)

- ensure `.env.docker` exists for postgres (see [.env.docker](.env.docker))
- ensure `backend/.env` exists (copy from `backend/.env.example` and fill values)

run:

- `docker compose up -d`

this exposes:
- postgres on `localhost:5433`
- redis on `localhost:6380`
- ipfs api on `localhost:5001`, gateway on `localhost:8080`
- gateway-sidecar on `localhost:4010`

### 2) backend

from `backend/`:
- `uv sync`
- `uv run alembic upgrade head`
- `uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000`

tests:
- `uv run pytest -q`

### 3) frontend

from `frontend/`:
- `npm install`
- `npm run dev`

tests:
- `npm test`

## quick debugging pointers

- if you see withdraw “failed / estimation error”, it usually means the contract call would revert during gas estimation (most commonly: nothing to withdraw yet, or the wallet has no gas).
- if dashboard totals move but on-chain balances lag, check the circle tx state via `/wallets/transactions/{tx_id}`.
