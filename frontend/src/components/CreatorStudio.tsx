import { useEffect, useMemo, useState } from 'react';
import { ArrowUpRight, Upload, Wallet } from 'lucide-react';

import { CreatorDashboardResponse } from '../types';
import { getCreatorDashboard, withdrawCreator } from '../services/creators';
import { uploadContent } from '../services/content';
import { getCircleTransaction, CircleTransactionResponse } from '../services/wallets';
import { formatUsdcMinor } from '../utils/format';

export default function CreatorStudio({
  token,
  onUploaded,
}: {
  token: string;
  onUploaded: () => void;
}) {
  const [dashboard, setDashboard] = useState<CreatorDashboardResponse | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [withdrawTxId, setWithdrawTxId] = useState<string | null>(null);
  const [withdrawInfo, setWithdrawInfo] = useState<CircleTransactionResponse | null>(null);
  const [withdrawing, setWithdrawing] = useState(false);

  const [file, setFile] = useState<File | null>(null);
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [contentType, setContentType] = useState('video');
  const [engagementIntent, setEngagementIntent] = useState('entertainment');
  const [showUpload, setShowUpload] = useState(false);

  const totals = useMemo(() => {
    return {
      gross: dashboard?.total_amount_gross ?? 0,
      creator: dashboard?.total_amount_creator ?? 0,
    };
  }, [dashboard]);

  async function refresh() {
    setError(null);
    const resp = await getCreatorDashboard(token);
    setDashboard(resp);
  }

  useEffect(() => {
    refresh().catch((e) => setError(String(e)));
  }, [token]);

  async function submitUpload() {
    if (!file) return;
    if (busy) return;

    setBusy(true);
    setError(null);
    try {
      await uploadContent(token, {
        file,
        title,
        description,
        content_type: contentType,
        engagement_intent: engagementIntent,
      });
      setFile(null);
      setTitle('');
      setDescription('');
      await refresh();
      onUploaded();
    } catch (e) {
      setError(String(e));
    } finally {
      setBusy(false);
    }
  }

  async function doWithdraw() {
    if (busy || withdrawing) return;
    setBusy(true);
    setWithdrawing(true);
    setError(null);
    setWithdrawInfo(null);
    setWithdrawTxId(null);
    try {
      const resp = await withdrawCreator(token);
      await refresh();
      setWithdrawTxId(resp.tx_id);
    } catch (e) {
      setError(String(e));
    } finally {
      setBusy(false);
      setWithdrawing(false);
    }
  }

  useEffect(() => {
    if (!withdrawTxId) return;
    const txId = withdrawTxId!;
    let cancelled = false;
    let interval: number | null = null;

    async function poll() {
      try {
        const info = await getCircleTransaction(token, txId);
        if (cancelled) return;
        setWithdrawInfo(info);

        const state = (info.state ?? '').toUpperCase();
        if (state === 'COMPLETE' || state === 'CONFIRMED' || state === 'FAILED') {
          if (interval !== null) {
            window.clearInterval(interval);
            interval = null;
          }
        }
      } catch (e) {
        if (!cancelled) {
          // Keep UI resilient; polling is best-effort.
          setWithdrawInfo(null);
        }
      }
    }

    void poll();
    interval = window.setInterval(() => void poll(), 3_000);
    return () => {
      cancelled = true;
      if (interval !== null) window.clearInterval(interval);
    };
  }, [token, withdrawTxId]);

  return (
    <div className="space-y-10">
      <header className="py-10 text-center space-y-4">
        <div className="inline-block glass px-4 py-2 rounded-full border-white/10 text-zinc-300 text-[10px] font-black tracking-[0.4em] uppercase">
          Creator studio
        </div>
        <h2 className="text-4xl md:text-6xl font-black tracking-tight leading-[0.95]">Ship content. Earn in real time.</h2>
        <p className="text-zinc-400 max-w-2xl mx-auto font-medium text-lg leading-relaxed">Publish new content and track earnings in real time.</p>
      </header>

      {error ? <div className="glass rounded-3xl p-6 border-white/10 text-red-400 font-bold break-all">{error}</div> : null}

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="glass rounded-3xl p-8 border-white/10">
          <div className="text-[10px] text-zinc-500 font-black uppercase tracking-[0.35em]">Total gross</div>
          <div className="mono text-3xl font-black text-white">{formatUsdcMinor(totals.gross)} USDC</div>
        </div>
        <div className="glass rounded-3xl p-8 border-white/10">
          <div className="text-[10px] text-zinc-500 font-black uppercase tracking-[0.35em]">Creator share</div>
          <div className="mono text-3xl font-black text-white">{formatUsdcMinor(totals.creator)} USDC</div>
        </div>
        <button
          onClick={doWithdraw}
          disabled={busy}
          className="glass rounded-3xl p-8 border-white/10 hover:border-white/30 transition-all text-left"
        >
          <div className="flex items-center justify-between">
            <div>
              <div className="text-[10px] text-zinc-500 font-black uppercase tracking-[0.35em]">Withdraw</div>
              <div className="text-2xl font-black text-white">{withdrawing ? 'Submitting…' : 'To wallet'}</div>
            </div>
            <div className="w-12 h-12 bg-white rounded-2xl flex items-center justify-center">
              <Wallet className="text-black" size={22} />
            </div>
          </div>
          <div className="mt-4 text-zinc-500 text-sm font-semibold">Withdraw your available balance.</div>

          {withdrawTxId ? (
            <div className="mt-4 glass rounded-2xl p-4 border-white/10">
              <div className="text-[10px] text-zinc-500 font-black uppercase tracking-[0.35em]">Withdrawal status</div>
              {withdrawInfo ? (
                <div className="mt-3 space-y-1">
                  <div className="text-[10px] text-zinc-500 font-black uppercase tracking-[0.35em]">Status</div>
                  <div className="mono text-xs font-bold text-zinc-200">{withdrawInfo.state}</div>
                  {withdrawInfo.error_reason ? (
                    <div className="text-[10px] text-red-400 font-bold break-all">{withdrawInfo.error_reason}</div>
                  ) : null}
                </div>
              ) : (
                <div className="mt-3 text-[10px] text-zinc-500 font-black uppercase tracking-[0.35em]">Checking status…</div>
              )}
            </div>
          ) : null}
        </button>
      </div>

      <div className="flex items-center justify-between">
        <div className="text-[10px] text-zinc-500 font-black uppercase tracking-[0.35em]">Content</div>
        <button
          onClick={() => setShowUpload(true)}
          className="px-5 py-3 rounded-2xl bg-white text-black font-black uppercase tracking-[0.35em] text-xs"
        >
          Upload new
        </button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-10">
        <div className="space-y-6">
          <div className="glass rounded-[2.5rem] p-10 border-white/10">
            <div className="flex items-center justify-between mb-6">
              <div>
                <div className="text-[10px] text-zinc-500 font-black uppercase tracking-[0.35em]">Earnings</div>
                <div className="text-2xl font-black">By content</div>
              </div>
              <ArrowUpRight className="text-white" size={22} />
            </div>

            <div className="space-y-3">
              {(dashboard?.earnings_by_content ?? []).slice(0, 10).map((e) => (
                <div key={e.content_id} className="flex items-center justify-between glass px-4 py-3 rounded-2xl border-white/10">
                  <div className="min-w-0">
                    <div className="font-black truncate">{e.title}</div>
                    <div className="text-[10px] text-zinc-500 font-black uppercase tracking-[0.35em] mono">{e.content_id.slice(0, 8)}...</div>
                  </div>
                  <div className="text-right">
                    <div className="mono text-white font-black">{formatUsdcMinor(e.amount_creator)} USDC</div>
                    <div className="text-[9px] text-zinc-600 uppercase font-black tracking-[0.35em]">earned</div>
                  </div>
                </div>
              ))}
              {(dashboard?.earnings_by_content ?? []).length === 0 ? (
                <div className="text-zinc-500 font-bold">No earnings yet.</div>
              ) : null}
            </div>
          </div>

          <div className="glass rounded-[2.5rem] p-10 border-white/10">
            <div className="text-[10px] text-zinc-500 font-black uppercase tracking-[0.35em]">Recent settlements</div>
            <div className="mt-4 space-y-3">
              {(dashboard?.recent_settlements ?? []).slice(0, 6).map((s) => (
                <div key={s.id} className="flex items-center justify-between glass px-4 py-3 rounded-2xl border-white/10">
                  <div>
                    <div className="text-[9px] text-zinc-600 uppercase font-black tracking-[0.35em]">{new Date(s.created_at).toLocaleString()}</div>
                  </div>
                  <div className="text-right">
                    <div className="mono text-white font-black">{formatUsdcMinor(s.amount_gross)} USDC</div>
                    <div className="text-[9px] text-zinc-600 uppercase font-black tracking-[0.35em]">gross</div>
                  </div>
                </div>
              ))}
              {(dashboard?.recent_settlements ?? []).length === 0 ? (
                <div className="text-zinc-500 font-bold">No settlements yet.</div>
              ) : null}
            </div>
          </div>
        </div>
      </div>

      {showUpload ? (
        <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-6" onClick={() => setShowUpload(false)}>
          <div className="w-full max-w-xl glass rounded-[2.5rem] p-8 border-white/10" onClick={(e) => e.stopPropagation()}>
            <div className="flex items-center justify-between mb-6">
              <div>
                <div className="text-[10px] text-zinc-500 font-black uppercase tracking-[0.35em]">Upload</div>
                <div className="text-2xl font-black">New content</div>
              </div>
              <button
                onClick={() => setShowUpload(false)}
                className="px-3 py-2 rounded-xl bg-white/10 text-zinc-300 text-xs uppercase tracking-[0.3em]"
              >
                Close
              </button>
            </div>

            <div className="space-y-4">
              <input
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                placeholder="title"
                className="w-full px-4 py-3 rounded-2xl bg-zinc-950 border border-white/10 focus:outline-none focus:ring-2 focus:ring-white/30"
              />
              <input
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                placeholder="description"
                className="w-full px-4 py-3 rounded-2xl bg-zinc-950 border border-white/10 focus:outline-none focus:ring-2 focus:ring-white/30"
              />

              <div className="grid grid-cols-2 gap-3">
                <input
                  value={contentType}
                  onChange={(e) => setContentType(e.target.value)}
                  placeholder="type"
                  className="w-full px-4 py-3 rounded-2xl bg-zinc-950 border border-white/10 focus:outline-none focus:ring-2 focus:ring-white/30"
                />
                <input
                  value={engagementIntent}
                  onChange={(e) => setEngagementIntent(e.target.value)}
                  placeholder="intent"
                  className="w-full px-4 py-3 rounded-2xl bg-zinc-950 border border-white/10 focus:outline-none focus:ring-2 focus:ring-white/30"
                />
              </div>

              <input
                type="file"
                onChange={(e) => setFile(e.target.files?.[0] ?? null)}
                className="w-full px-4 py-3 rounded-2xl bg-zinc-950 border border-white/10 text-zinc-400"
              />

              <button
                onClick={async () => {
                  await submitUpload();
                  setShowUpload(false);
                }}
                disabled={busy || !file || !title || !description}
                className="w-full py-4 bg-white text-black font-black rounded-2xl hover:bg-zinc-100 transition-all disabled:opacity-50"
              >
                {busy ? '...' : 'Upload'}
              </button>

              {error ? <div className="text-zinc-300 text-sm font-bold break-all">{error}</div> : null}
            </div>
          </div>
        </div>
      ) : null}
    </div>
  );
}
