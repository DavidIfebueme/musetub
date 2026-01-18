import { useEffect, useMemo, useState } from 'react';
import { Clock, Copy, ReceiptText } from 'lucide-react';

import { FundTestnetResponse, UserHistoryItem, UserSpendingResponse } from '../types';
import { getMyHistory, getMySpending } from '../services/users';
import { fundTestnet } from '../services/wallets';

export default function UserDashboard({ token }: { token: string }) {
  const [spending, setSpending] = useState<UserSpendingResponse | null>(null);
  const [history, setHistory] = useState<UserHistoryItem[]>([]);
  const [funding, setFunding] = useState<FundTestnetResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    async function load() {
      setError(null);
      const [s, h, f] = await Promise.all([getMySpending(token), getMyHistory(token), fundTestnet(token)]);
      if (!cancelled) {
        setSpending(s);
        setHistory(h);
        setFunding(f);
      }
    }

    load().catch((e) => setError(String(e)));
    return () => {
      cancelled = true;
    };
  }, [token]);

  const totals = useMemo(() => {
    return {
      seconds: spending?.total_seconds_streamed ?? 0,
      owed: spending?.total_amount_owed ?? 0,
      settled: spending?.total_amount_settled ?? 0,
    };
  }, [spending]);

  return (
    <div className="space-y-10">
      <header className="py-10 text-center space-y-4">
        <div className="inline-block glass px-4 py-2 rounded-2xl border-emerald-500/20 text-emerald-400 text-[10px] font-black tracking-[0.3em] uppercase">
          User Dashboard
        </div>
        <h2 className="text-5xl md:text-6xl font-black tracking-tighter leading-none italic">Your streaming history</h2>
        <p className="text-zinc-500 max-w-2xl mx-auto font-medium text-lg italic leading-relaxed">Totals and recent channels.</p>
      </header>

      {error ? <div className="glass rounded-3xl p-6 border-zinc-800 text-red-400 font-bold break-all">{error}</div> : null}

      {funding ? (
        <div className="glass rounded-[2.5rem] p-10 border-zinc-800">
          <div className="text-[10px] text-zinc-600 font-black uppercase tracking-widest">Wallet</div>
          <div className="mt-4 grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div className="glass rounded-2xl p-6 border-zinc-800">
              <div className="text-[10px] text-zinc-600 font-black uppercase tracking-widest">Arc address</div>
              <div className="mt-2 flex items-center justify-between gap-3">
                <div className="mono text-xs font-bold text-zinc-200 break-all">{funding.wallet_address || '—'}</div>
                <button
                  className="px-3 py-2 bg-zinc-900 rounded-xl text-zinc-300 hover:text-emerald-400 transition-colors font-black text-xs"
                  onClick={async () => {
                    try {
                      await navigator.clipboard.writeText(funding.wallet_address || '');
                    } catch {
                      setError('Copy failed');
                    }
                  }}
                >
                  <span className="inline-flex items-center gap-2">
                    <Copy size={14} />
                    COPY
                  </span>
                </button>
              </div>
            </div>
            <div className="glass rounded-2xl p-6 border-zinc-800">
              <div className="text-[10px] text-zinc-600 font-black uppercase tracking-widest">Funding</div>
              <div className="mt-2 text-zinc-300 font-bold">{funding.instructions}</div>
              <a
                className="mt-3 inline-block text-emerald-400 font-black text-xs tracking-widest uppercase"
                href={funding.docs_url}
                target="_blank"
                rel="noreferrer"
              >
                Docs
              </a>
            </div>
          </div>
        </div>
      ) : null}

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="glass rounded-3xl p-8 border-zinc-800">
          <div className="flex items-center justify-between">
            <div>
              <div className="text-[10px] text-zinc-600 font-black uppercase tracking-widest">Total seconds</div>
              <div className="mono text-3xl font-black text-white">{totals.seconds}</div>
            </div>
            <Clock className="text-emerald-400" size={22} />
          </div>
        </div>
        <div className="glass rounded-3xl p-8 border-zinc-800">
          <div className="text-[10px] text-zinc-600 font-black uppercase tracking-widest">Total owed</div>
          <div className="mono text-3xl font-black text-white">{totals.owed}</div>
        </div>
        <div className="glass rounded-3xl p-8 border-zinc-800">
          <div className="flex items-center justify-between">
            <div>
              <div className="text-[10px] text-zinc-600 font-black uppercase tracking-widest">Total settled</div>
              <div className="mono text-3xl font-black text-emerald-400">{totals.settled}</div>
            </div>
            <ReceiptText className="text-emerald-400" size={22} />
          </div>
        </div>
      </div>

      <div className="glass rounded-[2.5rem] p-10 border-zinc-800">
        <div className="text-[10px] text-zinc-600 font-black uppercase tracking-widest">Recent channels</div>
        <div className="mt-6 space-y-3">
          {history.slice(0, 20).map((h) => (
            <div key={h.channel_id} className="flex items-center justify-between glass px-4 py-3 rounded-2xl border-zinc-800">
              <div className="min-w-0">
                <div className="font-black italic truncate">{h.content_title}</div>
                <div className="text-[10px] text-zinc-600 font-black uppercase tracking-widest mono">
                  {h.status} • {h.total_seconds_streamed}s
                </div>
              </div>
              <div className="text-right">
                <div className="mono text-white font-black">{h.total_amount_owed}</div>
                <div className="text-[9px] text-zinc-600 uppercase font-black tracking-widest">owed</div>
              </div>
            </div>
          ))}
          {history.length === 0 ? <div className="text-zinc-500 font-bold">No history yet.</div> : null}
        </div>
      </div>
    </div>
  );
}
