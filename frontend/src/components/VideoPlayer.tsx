import { useEffect, useMemo, useRef, useState } from 'react';
import { Activity, ShieldCheck } from 'lucide-react';

import { ContentItem } from '../types';
import { PaymentStreamSession } from '../services/streamSession';

export default function VideoPlayer({
  token,
  item,
  onClose,
}: {
  token: string;
  item: ContentItem;
  onClose: () => void;
}) {
  const [isRunning, setIsRunning] = useState(false);
  const [sessionMinor, setSessionMinor] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const sessionRef = useRef<PaymentStreamSession | null>(null);

  const rateLabel = useMemo(() => String(item.price_per_second), [item.price_per_second]);

  useEffect(() => {
    const session = new PaymentStreamSession({
      token,
      contentId: item.id,
      pricePerSecondMinor: item.price_per_second,
      onTick: (deltaMinor) => setSessionMinor((v) => v + deltaMinor),
      onError: (msg) => setError(msg),
    });

    sessionRef.current = session;
    return () => {
      session.stop().catch(() => undefined);
      sessionRef.current = null;
    };
  }, [token, item.id, item.price_per_second]);

  async function start() {
    setError(null);
    try {
      await sessionRef.current?.start();
      setIsRunning(true);
    } catch (e) {
      setError(String(e));
      setIsRunning(false);
    }
  }

  async function stop() {
    try {
      await sessionRef.current?.stop();
    } finally {
      setIsRunning(false);
    }
  }

  async function toggle() {
    if (isRunning) {
      await stop();
    } else {
      await start();
    }
  }

  return (
    <div className="fixed inset-0 z-50 bg-black/95 backdrop-blur-xl flex flex-col items-center justify-center p-4">
      <div className="max-w-5xl w-full glass rounded-[2.5rem] overflow-hidden shadow-2xl border-emerald-500/10">
        <div className="relative aspect-video bg-zinc-950 group">
          <video className="w-full h-full object-contain" src={item.playback_url} controls onPlay={start} onPause={stop} />
        </div>

        <div className="p-8 flex flex-col md:flex-row justify-between items-center gap-6">
          <div className="space-y-1">
            <h2 className="text-2xl font-black italic">{item.title}</h2>
            <div className="flex items-center gap-2 text-zinc-500 text-sm font-bold uppercase tracking-widest">
              <Activity size={14} className="text-emerald-500" />
              IPFS <span className="text-zinc-300 mono">{item.id.slice(0, 10)}...</span>
            </div>
            {error ? <div className="text-red-400 text-sm font-bold">{error}</div> : null}
          </div>

          <div className="flex gap-6">
            <div className="text-center">
              <div className="text-[10px] text-zinc-500 font-black uppercase">Rate</div>
              <div className="mono text-emerald-400 font-bold">{rateLabel} minor/s</div>
            </div>
            <div className="w-px h-10 bg-zinc-800"></div>
            <div className="text-center">
              <div className="text-[10px] text-zinc-500 font-black uppercase">Session</div>
              <div className="mono text-white font-bold">{sessionMinor}</div>
            </div>
          </div>
        </div>

        <div className="bg-emerald-500/5 p-4 flex justify-between items-center px-10 border-t border-zinc-800">
          <div className="flex items-center gap-3 text-emerald-400 text-xs font-bold uppercase tracking-tighter">
            <ShieldCheck size={18} />
            Streaming payments active
          </div>
          <div className="flex gap-3">
            <button
              onClick={toggle}
              className="px-6 py-2 bg-emerald-500 rounded-xl text-black hover:bg-emerald-400 transition-colors font-black text-xs"
            >
              {isRunning ? 'PAUSE' : 'PLAY'}
            </button>
            <button
              onClick={async () => {
                await stop();
                onClose();
              }}
              className="px-6 py-2 bg-zinc-900 rounded-xl text-zinc-400 hover:text-red-400 transition-colors font-black text-xs"
            >
              END
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
