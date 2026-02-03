import { useEffect, useMemo, useRef, useState } from 'react';
import { Activity, ShieldCheck } from 'lucide-react';

import { ContentItem, ContentResponse } from '../types';
import { getContent } from '../services/content';
import {
  autoPayStream,
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
  const [contentDetails, setContentDetails] = useState<ContentResponse | null>(null);
  const [detailsError, setDetailsError] = useState<string | null>(null);
  const consumeIntervalRef = useRef<number | null>(null);
  const playGuardRef = useRef(false);
  const videoRef = useRef<HTMLVideoElement | null>(null);

  const rateLabel = useMemo(() => String(item.price_per_second), [item.price_per_second]);

  useEffect(() => {
    return () => {
      if (consumeIntervalRef.current !== null) {
        window.clearInterval(consumeIntervalRef.current);
        consumeIntervalRef.current = null;
      }
    };
  }, []);

  useEffect(() => {
    setStreamUrl(null);
    setPaywall(null);
    setPaymentResponse(null);
    setContentDetails(null);
    setDetailsError(null);
    setSessionMinor(0);
    setIsRunning(false);
    if (consumeIntervalRef.current !== null) {
      window.clearInterval(consumeIntervalRef.current);
      consumeIntervalRef.current = null;
    }
  }, [item.id]);

  useEffect(() => {
    let cancelled = false;

    async function loadDetails() {
      const details = await getContent(item.id);
      if (!cancelled) {
        setContentDetails(details);
      }
    }

    loadDetails().catch((e) => {
      if (!cancelled) {
        setDetailsError(String(e));
      }
    });

    return () => {
      cancelled = true;
    };
  }, [item.id]);

  useEffect(() => {
    // Do not auto-consume credit on modal open.
  }, [item.id]);

  async function consumeChunk(): Promise<boolean> {
    if (unlockBusy) return false;

    setUnlockBusy(true);
    setError(null);
    setPaywall(null);

    try {
      const res = await getStreamPlaybackUrl(token, item.id);
      setStreamUrl(res.playbackUrl);
      setPaymentResponse(res.paymentResponseHeader ?? null);
      setSessionMinor((v) => v + item.price_per_second * 10);
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

    const res = await autoPayStream(token, item.id);
    setPaymentResponse(res.paymentResponseHeader ?? null);
    // Do not rely on /pay response for gating; /stream consumes credit.
    // We still keep the returned header for debugging.
    void res;
  }

  async function startConsuming(): Promise<void> {
    if (consumeIntervalRef.current !== null) return;
    consumeIntervalRef.current = window.setInterval(() => {
      consumeChunk().then((ok) => {
        if (!ok) {
          if (consumeIntervalRef.current !== null) {
            window.clearInterval(consumeIntervalRef.current);
            consumeIntervalRef.current = null;
          }
          videoRef.current?.pause();
          setIsRunning(false);
        }
      });
    }, 10_000);
  }

  function stopConsuming(): void {
    if (consumeIntervalRef.current !== null) {
      window.clearInterval(consumeIntervalRef.current);
      consumeIntervalRef.current = null;
    }
  }

  async function toggle() {
    const v = videoRef.current;
    if (!v) return;

    if (isRunning) {
      stopConsuming();
      v.pause();
      setIsRunning(false);
      return;
    }

    const ok = await consumeChunk();
    if (!ok) return;

    await startConsuming();
    await v.play().catch(() => undefined);
    setIsRunning(true);
  }

  const accept = paywall?.accepts?.[0];
  const pricingExplanation = contentDetails?.pricing_explanation ?? null;

  return (
    <div className="fixed inset-0 z-50 bg-black/95 backdrop-blur-xl flex flex-col items-center justify-center p-4">
      <div className="max-w-5xl w-full glass rounded-[2.5rem] overflow-hidden shadow-2xl border-white/10">
        <div className="relative aspect-video bg-zinc-950 group">
          {streamUrl ? (
            <video
              ref={videoRef}
              className="w-full h-full object-contain"
              src={streamUrl}
              controls
              onPlay={() => {
                // Important: don't consume a chunk here.
                // PAY & PLAY / the explicit PLAY button already consumes.
                // Consuming again on native play burns the only 10s chunk and immediately triggers 402.
                void startConsuming();
                setIsRunning(true);
              }}
              onPause={() => {
                stopConsuming();
                setIsRunning(false);
              }}
            />
          ) : (
            <div className="absolute inset-0 flex items-center justify-center p-8">
              <div className="w-full max-w-2xl glass rounded-3xl p-8 border border-white/10">
                <div className="text-[10px] text-zinc-500 font-black uppercase tracking-[0.35em]">x402</div>
                <div className="mt-1 text-2xl font-black">Payment required to stream</div>

                {pricingExplanation ? (
                  <div className="mt-4 glass rounded-2xl p-4 border-white/10">
                    <div className="text-[10px] text-zinc-500 font-black uppercase tracking-[0.35em]">Why this price</div>
                    <div className="mt-2 text-zinc-200 text-sm font-semibold leading-relaxed">{pricingExplanation}</div>
                  </div>
                ) : detailsError ? (
                  <div className="mt-4 text-[10px] text-zinc-500 font-black uppercase tracking-[0.35em] break-all">
                    Pricing details unavailable: {detailsError}
                  </div>
                ) : null}

                {accept ? (
                  <div className="mt-6 grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div className="glass rounded-2xl p-4 border-white/10">
                      <div className="text-[10px] text-zinc-500 font-black uppercase tracking-[0.35em]">Amount</div>
                      <div className="mono text-white font-bold break-all">{accept.amount}</div>
                    </div>
                    <div className="glass rounded-2xl p-4 border-white/10">
                      <div className="text-[10px] text-zinc-500 font-black uppercase tracking-[0.35em]">Network</div>
                      <div className="mono text-white font-bold break-all">{accept.network}</div>
                    </div>
                    <div className="glass rounded-2xl p-4 border-white/10 md:col-span-2">
                      <div className="text-[10px] text-zinc-500 font-black uppercase tracking-[0.35em]">Pay to</div>
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
                          const ok = await consumeChunk();
                          if (!ok) return;
                          await startConsuming();
                          await videoRef.current?.play().catch(() => undefined);
                          setIsRunning(true);
                        } catch (e) {
                          setError(String(e));
                        }
                      }}
                      disabled={unlockBusy}
                      className="flex-1 py-4 bg-white text-black font-black rounded-2xl hover:bg-zinc-100 transition-all disabled:opacity-50"
                    >
                      {unlockBusy ? '...' : 'PAY & PLAY'}
                    </button>
                    <button
                      onClick={onClose}
                      className="px-6 py-4 bg-white/10 rounded-2xl text-zinc-300 hover:text-white transition-colors font-black"
                    >
                      CLOSE
                    </button>
                  </div>
                </div>

                {paymentResponse ? (
                  <div className="mt-4 text-[10px] text-zinc-500 font-black uppercase tracking-[0.35em] break-all">
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
              <div className="text-emerald-400 text-xs font-black uppercase tracking-widest">Awaiting payment…</div>
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
                stopConsuming();
                setIsRunning(false);
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
