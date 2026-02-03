import BrandLogo from './BrandLogo';

export default function AuthPage({
  authMode,
  setAuthMode,
  busy,
  email,
  setEmail,
  password,
  setPassword,
  isCreator,
  setIsCreator,
  submitAuth,
  error,
  onBack,
}: {
  authMode: 'login' | 'register';
  setAuthMode: (mode: 'login' | 'register') => void;
  busy: boolean;
  email: string;
  setEmail: (value: string) => void;
  password: string;
  setPassword: (value: string) => void;
  isCreator: boolean;
  setIsCreator: (value: boolean) => void;
  submitAuth: () => void;
  error: string | null;
  onBack: () => void;
}) {
  return (
    <div className="min-h-screen bg-black text-white">
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_top,#1f2937_0%,transparent_55%)]" />
      <div className="relative z-10 max-w-6xl mx-auto px-6 py-12">
        <nav className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <BrandLogo size={44} />
            <div>
              <div className="text-xl font-black tracking-tight">MuseTub</div>
              <div className="text-[10px] uppercase tracking-[0.4em] text-zinc-500">settled media</div>
            </div>
          </div>
          <button
            onClick={onBack}
            className="px-5 py-2.5 rounded-full border border-white/15 bg-white/5 hover:bg-white/10 transition text-xs uppercase tracking-[0.3em]"
          >
            Back
          </button>
        </nav>

        <div className="mt-12 grid grid-cols-1 lg:grid-cols-[1.1fr_0.9fr] gap-10 items-center">
          <div className="space-y-8">
            <div className="inline-flex items-center gap-3 px-4 py-2 rounded-full border border-white/10 bg-white/5 text-[10px] uppercase tracking-[0.4em] text-zinc-400">
              Access portal
            </div>
            <h1 className="text-4xl md:text-6xl font-black leading-[0.95]">
              {authMode === 'login' ? 'Welcome back.' : 'Create your studio.'}
            </h1>
            <p className="text-zinc-400 text-lg max-w-xl">
              {authMode === 'login'
                ? 'Resume your streams and track micro‑settled sessions.'
                : 'Spin up your creator wallet and publish to IPFS.'}
            </p>
            <div className="flex gap-3">
              <button
                className={
                  authMode === 'login'
                    ? 'px-5 py-3 rounded-2xl bg-white text-black font-black uppercase tracking-widest text-xs'
                    : 'px-5 py-3 rounded-2xl border border-white/15 bg-white/5 hover:bg-white/10 transition font-black uppercase tracking-widest text-xs'
                }
                onClick={() => setAuthMode('login')}
                disabled={busy}
              >
                Login
              </button>
              <button
                className={
                  authMode === 'register'
                    ? 'px-5 py-3 rounded-2xl bg-white text-black font-black uppercase tracking-widest text-xs'
                    : 'px-5 py-3 rounded-2xl border border-white/15 bg-white/5 hover:bg-white/10 transition font-black uppercase tracking-widest text-xs'
                }
                onClick={() => setAuthMode('register')}
                disabled={busy}
              >
                Register
              </button>
            </div>
          </div>

          <div className="rounded-[2.5rem] border border-white/10 bg-white/5 p-8 backdrop-blur">
            <div className="text-[10px] uppercase tracking-[0.4em] text-zinc-500">Secure access</div>
            <div className="mt-6 space-y-4">
              <input
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="email"
                className="w-full px-4 py-3 rounded-2xl bg-zinc-950 border border-white/10 focus:outline-none focus:ring-2 focus:ring-white/30"
              />
              <input
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="password"
                type="password"
                className="w-full px-4 py-3 rounded-2xl bg-zinc-950 border border-white/10 focus:outline-none focus:ring-2 focus:ring-white/30"
              />
              {authMode === 'register' ? (
                <label className="flex items-center gap-3 text-zinc-400 text-xs font-semibold">
                  <input type="checkbox" checked={isCreator} onChange={(e) => setIsCreator(e.target.checked)} />
                  Creator account
                </label>
              ) : null}
              <button
                onClick={submitAuth}
                disabled={busy || !email || !password}
                className="w-full py-4 rounded-2xl bg-white text-black font-black uppercase tracking-widest text-xs disabled:opacity-50"
              >
                {busy ? '...' : authMode === 'login' ? 'Login' : 'Register'}
              </button>
              {error ? <div className="text-red-400 text-sm font-bold break-all">{error}</div> : null}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
