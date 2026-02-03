import BrandLogo from './BrandLogo';
import Hero3D from './Hero3D';

export default function LandingPage({ onEnter }: { onEnter: () => void }) {
  return (
    <div className="min-h-screen bg-black text-white overflow-hidden relative">
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_top,#1f2937_0%,transparent_55%)]" />
      <Hero3D />
      <div className="relative z-10">
        <div className="max-w-6xl mx-auto px-6 pt-10 pb-20">
          <nav className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <BrandLogo size={44} />
              <div>
                <div className="text-xl font-black tracking-tight">MuseTub</div>
                <div className="text-[10px] uppercase tracking-[0.4em] text-zinc-500">streaming protocol</div>
              </div>
            </div>
            <button
              onClick={onEnter}
              className="px-5 py-2.5 rounded-full border border-white/15 bg-white/10 hover:bg-white/20 transition text-xs uppercase tracking-[0.3em]"
            >
              Enter
            </button>
          </nav>

          <div className="mt-20 grid grid-cols-1 lg:grid-cols-[1.2fr_0.8fr] gap-12 items-center">
            <div className="space-y-8">
              <div className="inline-flex items-center gap-3 px-4 py-2 rounded-full border border-white/10 bg-white/5 text-[10px] uppercase tracking-[0.4em] text-zinc-400">
                Arc · USDC · IPFS
              </div>
              <h1 className="text-5xl md:text-7xl font-black leading-[0.95] tracking-tight">
                The dark stage for micro‑settled media.
              </h1>
              <p className="text-lg md:text-xl text-zinc-400 max-w-xl">
                Pay only while you watch. Every 10 seconds settles on Arc. Creators see real‑time owed vs settled.
              </p>
              <div className="flex flex-wrap gap-4">
                <button
                  onClick={onEnter}
                  className="px-7 py-4 rounded-2xl bg-white text-black font-black uppercase tracking-widest text-xs"
                >
                  Start watching
                </button>
                <button
                  onClick={onEnter}
                  className="px-7 py-4 rounded-2xl border border-white/15 bg-white/5 hover:bg-white/10 transition font-black uppercase tracking-widest text-xs"
                >
                  Creator access
                </button>
              </div>
            </div>
            <div className="space-y-6">
              <div className="rounded-[2.5rem] border border-white/10 bg-white/5 p-8 backdrop-blur">
                <div className="text-[10px] uppercase tracking-[0.4em] text-zinc-500">Live settlement</div>
                <div className="mt-4 text-3xl font-black">10s credit blocks</div>
                <div className="mt-2 text-zinc-400 text-sm leading-relaxed">
                  Stream in prepaid windows. Keep control of spend and stop anytime.
                </div>
              </div>
              <div className="rounded-[2.5rem] border border-white/10 bg-gradient-to-br from-white/10 via-white/5 to-transparent p-8 backdrop-blur">
                <div className="text-[10px] uppercase tracking-[0.4em] text-zinc-500">Creator studio</div>
                <div className="mt-4 text-3xl font-black">Upload to IPFS</div>
                <div className="mt-2 text-zinc-400 text-sm leading-relaxed">
                  Revenue splits, wallet ops, and settlement telemetry in one space.
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
