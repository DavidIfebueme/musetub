import { useEffect, useMemo, useState } from 'react';
import { ArrowUpRight, Upload, Wallet } from 'lucide-react';

import { CreatorDashboardResponse } from '../types';
import { getCreatorDashboard, withdrawCreator } from '../services/creators';
import { uploadContent } from '../services/content';
import { getCircleTransaction, CircleTransactionResponse } from '../services/wallets';

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
  const [durationSeconds, setDurationSeconds] = useState(60);
  const [resolution, setResolution] = useState('1080p');
  const [bitrateTier, setBitrateTier] = useState('high');
  const [engagementIntent, setEngagementIntent] = useState('entertainment');

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
        duration_seconds: durationSeconds,
        resolution,
        bitrate_tier: bitrateTier,
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
        <div className="inline-block glass px-4 py-2 rounded-2xl border-emerald-500/20 text-emerald-400 text-[10px] font-black tracking-[0.3em] uppercase">
          Creator Studio
        </div>
        <h2 className="text-5xl md:text-6xl font-black tracking-tighter leading-none italic">Ship content. Earn in ticks.</h2>
        <p className="text-zinc-500 max-w-2xl mx-auto font-medium text-lg italic leading-relaxed">Upload to IPFS and track settlements.</p>
      </header>

      {error ? <div className="glass rounded-3xl p-6 border-zinc-800 text-red-400 font-bold break-all">{error}</div> : null}

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="glass rounded-3xl p-8 border-zinc-800">
          <div className="text-[10px] text-zinc-600 font-black uppercase tracking-widest">Total gross</div>
          <div className="mono text-3xl font-black text-white">{totals.gross}</div>
        </div>
        <div className="glass rounded-3xl p-8 border-zinc-800">
          <div className="text-[10px] text-zinc-600 font-black uppercase tracking-widest">Creator share</div>
          <div className="mono text-3xl font-black text-emerald-400">{totals.creator}</div>
        </div>
        <button
          onClick={doWithdraw}
          disabled={busy}
          className="glass rounded-3xl p-8 border-emerald-500/20 hover:border-emerald-500/50 transition-all text-left"
        >
          <div className="flex items-center justify-between">
            <div>
              <div className="text-[10px] text-zinc-600 font-black uppercase tracking-widest">Withdraw</div>
              <div className="text-2xl font-black italic text-white">{withdrawing ? 'Submitting…' : 'To wallet'}</div>
            </div>
            <div className="w-12 h-12 bg-emerald-500 rounded-2xl flex items-center justify-center">
              <Wallet className="text-black" size={22} />
            </div>
          </div>
          <div className="mt-4 text-zinc-500 text-sm font-bold">Executes escrow withdraw when live.</div>

          {withdrawTxId ? (
            <div className="mt-4 glass rounded-2xl p-4 border-zinc-800">
              <div className="text-[10px] text-zinc-600 font-black uppercase tracking-widest">Withdraw tx</div>
              <div className="mt-2 mono text-xs text-zinc-200 break-all">{withdrawTxId}</div>
              {withdrawInfo ? (
                <div className="mt-3 space-y-1">
                  <div className="text-[10px] text-zinc-600 font-black uppercase tracking-widest">Status</div>
                  <div className="mono text-xs font-bold text-zinc-200">{withdrawInfo.state}</div>
                  {withdrawInfo.tx_hash ? (
                    <div className="mono text-[10px] text-zinc-500 break-all">on-chain: {withdrawInfo.tx_hash}</div>
                  ) : null}
                  {withdrawInfo.error_reason ? (
                    <div className="text-[10px] text-red-400 font-bold break-all">{withdrawInfo.error_reason}</div>
                  ) : null}
                  {withdrawInfo.error_details ? (
                    <div className="text-[10px] text-red-400 font-bold break-all">{withdrawInfo.error_details}</div>
                  ) : null}
                </div>
              ) : (
                <div className="mt-3 text-[10px] text-zinc-600 font-black uppercase tracking-widest">Checking status…</div>
              )}
            </div>
          ) : null}
        </button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-10">
        <div className="glass rounded-[2.5rem] p-10 border-zinc-800">
          <div className="flex items-center justify-between mb-8">
            <div>
              <div className="text-[10px] text-zinc-600 font-black uppercase tracking-widest">Upload</div>
              <div className="text-2xl font-black italic">New content</div>
            </div>
            <Upload className="text-emerald-400" size={22} />
          </div>

          <div className="space-y-4">
            <input
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="title"
              className="w-full px-4 py-3 rounded-2xl bg-zinc-950 border border-zinc-800"
            />
            <input
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="description"
              className="w-full px-4 py-3 rounded-2xl bg-zinc-950 border border-zinc-800"
            />

            <div className="grid grid-cols-2 gap-3">
              <input
                value={contentType}
                onChange={(e) => setContentType(e.target.value)}
                placeholder="content_type"
                className="w-full px-4 py-3 rounded-2xl bg-zinc-950 border border-zinc-800"
              />
              <input
                value={durationSeconds}
                onChange={(e) => setDurationSeconds(Number(e.target.value))}
                placeholder="duration_seconds"
                type="number"
                className="w-full px-4 py-3 rounded-2xl bg-zinc-950 border border-zinc-800"
              />
            </div>

            <div className="grid grid-cols-3 gap-3">
              <input
                value={resolution}
                onChange={(e) => setResolution(e.target.value)}
                placeholder="resolution"
                className="w-full px-4 py-3 rounded-2xl bg-zinc-950 border border-zinc-800"
              />
              <input
                value={bitrateTier}
                onChange={(e) => setBitrateTier(e.target.value)}
                placeholder="bitrate_tier"
                className="w-full px-4 py-3 rounded-2xl bg-zinc-950 border border-zinc-800"
              />
              <input
                value={engagementIntent}
                onChange={(e) => setEngagementIntent(e.target.value)}
                placeholder="engagement_intent"
                className="w-full px-4 py-3 rounded-2xl bg-zinc-950 border border-zinc-800"
              />
            </div>

            <input
              type="file"
              onChange={(e) => setFile(e.target.files?.[0] ?? null)}
              className="w-full px-4 py-3 rounded-2xl bg-zinc-950 border border-zinc-800 text-zinc-400"
            />

            <button
              onClick={submitUpload}
              disabled={busy || !file || !title || !description}
              className="w-full py-4 bg-emerald-500 text-black font-black rounded-2xl hover:bg-emerald-400 transition-all disabled:opacity-50"
            >
              {busy ? '...' : 'Upload'}
            </button>

            {error ? <div className="text-zinc-300 text-sm font-bold break-all">{error}</div> : null}
          </div>
        </div>

        <div className="space-y-6">
          <div className="glass rounded-[2.5rem] p-10 border-zinc-800">
            <div className="flex items-center justify-between mb-6">
              <div>
                <div className="text-[10px] text-zinc-600 font-black uppercase tracking-widest">Earnings</div>
                <div className="text-2xl font-black italic">By content</div>
              </div>
              <ArrowUpRight className="text-emerald-400" size={22} />
            </div>

            <div className="space-y-3">
              {(dashboard?.earnings_by_content ?? []).slice(0, 10).map((e) => (
                <div key={e.content_id} className="flex items-center justify-between glass px-4 py-3 rounded-2xl border-zinc-800">
                  <div className="min-w-0">
                    <div className="font-black italic truncate">{e.title}</div>
                    <div className="text-[10px] text-zinc-600 font-black uppercase tracking-widest mono">{e.content_id.slice(0, 8)}...</div>
                  </div>
                  <div className="text-right">
                    <div className="mono text-emerald-400 font-black">{e.amount_creator}</div>
                    <div className="text-[9px] text-zinc-600 uppercase font-black tracking-widest">creator</div>
                  </div>
                </div>
              ))}
              {(dashboard?.earnings_by_content ?? []).length === 0 ? (
                <div className="text-zinc-500 font-bold">No earnings yet.</div>
              ) : null}
            </div>
          </div>

          <div className="glass rounded-[2.5rem] p-10 border-zinc-800">
            <div className="text-[10px] text-zinc-600 font-black uppercase tracking-widest">Recent settlements</div>
            <div className="mt-4 space-y-3">
              {(dashboard?.recent_settlements ?? []).slice(0, 6).map((s) => (
                <div key={s.id} className="flex items-center justify-between glass px-4 py-3 rounded-2xl border-zinc-800">
                  <div>
                    <div className="mono text-xs text-zinc-300">{s.tx_hash ? `${s.tx_hash.slice(0, 10)}...` : 'simulated'}</div>
                    <div className="text-[9px] text-zinc-600 uppercase font-black tracking-widest">{new Date(s.created_at).toLocaleString()}</div>
                  </div>
                  <div className="text-right">
                    <div className="mono text-white font-black">{s.amount_gross}</div>
                    <div className="text-[9px] text-zinc-600 uppercase font-black tracking-widest">gross</div>
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
    </div>
  );
}
