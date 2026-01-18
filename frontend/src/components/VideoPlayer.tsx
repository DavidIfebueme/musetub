import { useEffect, useMemo, useRef, useState } from 'react';
import { Activity, ShieldCheck } from 'lucide-react';

import { ContentItem } from '../types';
import { PaymentStreamSession } from '../services/streamSession';
import {
  autoPayStream,
  createPaymentSignature,
  getStreamPlaybackUrl,
  X402PaymentRequiredBody,
  X402PaymentRequiredError,
} from '../services/stream';

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
  const [streamUrl, setStreamUrl] = useState<string | null>(null);
  const [paywall, setPaywall] = useState<X402PaymentRequiredBody | null>(null);
  const [paymentResponse, setPaymentResponse] = useState<string | null>(null);
  const [unlockBusy, setUnlockBusy] = useState(false);
  const sessionRef = useRef<PaymentStreamSession | null>(null);
  const videoRef = useRef<HTMLVideoElement | null>(null);

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

  useEffect(() => {
    setStreamUrl(null);
    setPaywall(null);
    setPaymentResponse(null);
  }, [item.id]);

  async function ensureUnlocked(): Promise<boolean> {
    if (unlockBusy) return false;

    setUnlockBusy(true);
    setError(null);
    setPaywall(null);

    try {
      const res = await getStreamPlaybackUrl(token, item.id);
      setStreamUrl(res.playbackUrl);
      setPaymentResponse(res.paymentResponseHeader ?? null);
      return true;
    } catch (e) {
      if (e instanceof X402PaymentRequiredError) {
        setPaywall(e.body);
        return false;
      }
      setError(String(e));
      return false;
    } finally {
      setUnlockBusy(false);
    }
  }

  async function payAndUnlock(): Promise<void> {
    if (unlockBusy) return;
    setError(null);

    const accept = paywall?.accepts?.[0];
    if (accept) {
      try {
        const signature = createPaymentSignature(accept);
        const res = await getStreamPlaybackUrl(token, item.id, signature);
        setStreamUrl(res.playbackUrl);
        setPaymentResponse(res.paymentResponseHeader ?? null);
        return;
      } catch {
      }
    }

    const res = await autoPayStream(token, item.id);
    setStreamUrl(res.playbackUrl);
    setPaymentResponse(res.paymentResponseHeader ?? null);
  }

  async function start() {
    setError(null);
    try {
      const ok = streamUrl ? true : await ensureUnlocked();
      if (!ok) {
        setIsRunning(false);
        return;
      }
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

  const accept = paywall?.accepts?.[0];

  return (
    <div className="fixed inset-0 z-50 bg-black/95 backdrop-blur-xl flex flex-col items-center justify-center p-4">
      <div className="max-w-5xl w-full glass rounded-[2.5rem] overflow-hidden shadow-2xl border-emerald-500/10">
        <div className="relative aspect-video bg-zinc-950 group">
          {streamUrl ? (
            <video
              ref={videoRef}
              className="w-full h-full object-contain"
              src={streamUrl}
              controls
              onPlay={start}
              onPause={stop}
            />
          ) : (
            <div className="absolute inset-0 flex items-center justify-center p-8">
              <div className="w-full max-w-2xl glass rounded-3xl p-8 border border-zinc-800">
                <div className="text-[10px] text-zinc-600 font-black uppercase tracking-widest">x402</div>
                <div className="mt-1 text-2xl font-black italic">Payment required to stream</div>

                {accept ? (
                  <div className="mt-6 grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div className="glass rounded-2xl p-4 border-zinc-800">
                      <div className="text-[10px] text-zinc-600 font-black uppercase tracking-widest">Amount</div>
                      <div className="mono text-white font-bold break-all">{accept.amount}</div>
                    </div>
                    <div className="glass rounded-2xl p-4 border-zinc-800">
                      <div className="text-[10px] text-zinc-600 font-black uppercase tracking-widest">Network</div>
                      <div className="mono text-white font-bold break-all">{accept.network}</div>
                    </div>
                    <div className="glass rounded-2xl p-4 border-zinc-800 md:col-span-2">
                      <div className="text-[10px] text-zinc-600 font-black uppercase tracking-widest">Pay to</div>
                      <div className="mono text-white font-bold break-all">{accept.payTo}</div>
                    </div>
                  </div>
                ) : null}

                <div className="mt-6 space-y-3">
                  <div className="flex gap-3">
                    <button
                      onClick={async () => {
                        try {
                          await payAndUnlock();
                          await start();
                          await videoRef.current?.play().catch(() => undefined);
                        } catch (e) {
                          setError(String(e));
                        }
                      }}
                      disabled={unlockBusy}
                      className="flex-1 py-4 bg-emerald-500 text-black font-black rounded-2xl hover:bg-emerald-400 transition-all disabled:opacity-50"
                    >
                      {unlockBusy ? '...' : 'PAY & PLAY'}
                    </button>
                    <button
                      onClick={onClose}
                      className="px-6 py-4 bg-zinc-900 rounded-2xl text-zinc-400 hover:text-red-400 transition-colors font-black"
                    >
                      CLOSE
                    </button>
                  </div>
                </div>

                {paymentResponse ? (
                  <div className="mt-4 text-[10px] text-zinc-500 font-black uppercase tracking-widest break-all">
                    Payment-Response: {paymentResponse}
                  </div>
                ) : null}

                {error ? <div className="mt-3 text-red-400 text-sm font-bold break-all">{error}</div> : null}
              </div>
            </div>
          )}
        </div>

        <div className="p-8 flex flex-col md:flex-row justify-between items-center gap-6">
          <div className="space-y-1">
            <h2 className="text-2xl font-black italic">{item.title}</h2>
            <div className="flex items-center gap-2 text-zinc-500 text-sm font-bold uppercase tracking-widest">
              <Activity size={14} className="text-emerald-500" />
              IPFS <span className="text-zinc-300 mono">{item.id.slice(0, 10)}...</span>
            </div>
            {streamUrl ? null : paywall ? (
              <div className="text-emerald-400 text-xs font-black uppercase tracking-widest">Awaiting payment signature…</div>
            ) : null}
            {error ? <div className="text-red-400 text-sm font-bold break-all">{error}</div> : null}
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
