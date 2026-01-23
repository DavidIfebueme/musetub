import { useEffect, useMemo, useState } from 'react';
import { LogOut, Wallet, Zap } from 'lucide-react';

import SettlementVisualizer from './components/SettlementVisualizer';
import VideoPlayer from './components/VideoPlayer';
import CreatorStudio from './components/CreatorStudio';
import UserDashboard from './components/UserDashboard';
import { ContentItem } from './types';
import { clearAuthToken, getMe, getStoredAuthToken, Me, login, register } from './services/auth';
import { listContent } from './services/content';
import { getUsdcBalance, UsdcBalanceResponse } from './services/wallets';

type View = 'home' | 'user' | 'creator';

export default function App() {
  const [token, setToken] = useState<string | null>(getStoredAuthToken());
  const [me, setMe] = useState<Me | null>(null);
  const [view, setView] = useState<View>('home');
  const [content, setContent] = useState<ContentItem[]>([]);
  const [activeContent, setActiveContent] = useState<ContentItem | null>(null);
  const [busy, setBusy] = useState(false);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [isCreator, setIsCreator] = useState(false);
  const [authMode, setAuthMode] = useState<'login' | 'register'>('login');
  const [error, setError] = useState<string | null>(null);
  const [walletPanelOpen, setWalletPanelOpen] = useState(false);
  const [walletBalance, setWalletBalance] = useState<UsdcBalanceResponse | null>(null);
  const [walletBalanceError, setWalletBalanceError] = useState<string | null>(null);
  const [walletBalanceBusy, setWalletBalanceBusy] = useState(false);

  useEffect(() => {
    let cancelled = false;

    async function load() {
      if (!token) {
        setMe(null);
        return;
      }

      const meResp = await getMe(token);
      if (!cancelled) {
        setMe(meResp);
      }
    }

    load().catch((e) => {
      setError(String(e));
      setMe(null);
    });

    return () => {
      cancelled = true;
    };
  }, [token]);

  useEffect(() => {
    let cancelled = false;

    async function loadContent() {
      if (!token) return;
      const items = await listContent();
      if (!cancelled) {
        setContent(items);
      }
    }

    loadContent().catch((e) => setError(String(e)));
    return () => {
      cancelled = true;
    };
  }, [token]);

  async function refreshContent() {
    const items = await listContent();
    setContent(items);
  }

  const walletLabel = useMemo(() => {
    if (!me?.wallet_address) return null;
    return `${me.wallet_address.slice(0, 8)}...`;
  }, [me?.wallet_address]);

  async function submitAuth() {
    if (busy) return;
    setBusy(true);
    setError(null);

    try {
      const resp = authMode === 'login' ? await login(email, password) : await register(email, password, isCreator);
      setToken(resp.access_token);
    } catch (e) {
      setError(String(e));
    } finally {
      setBusy(false);
    }
  }

  function logout() {
    clearAuthToken();
    setToken(null);
    setMe(null);
    setContent([]);
    setActiveContent(null);
  }

  async function openWalletPanel(): Promise<void> {
    if (!token) return;
    setWalletPanelOpen(true);

    if (walletBalanceBusy || walletBalance) return;
    setWalletBalanceBusy(true);
    setWalletBalanceError(null);
    try {
      const bal = await getUsdcBalance(token);
      setWalletBalance(bal);
    } catch (e) {
      setWalletBalanceError(String(e));
    } finally {
      setWalletBalanceBusy(false);
    }
  }

  if (!token) {
    return (
      <div className="min-h-screen bg-black flex items-center justify-center p-6">
        <div className="max-w-md w-full glass rounded-[3rem] p-12 text-center space-y-8 border-emerald-500/20 shadow-2xl shadow-emerald-500/10">
          <div className="w-20 h-20 bg-emerald-500 rounded-3xl mx-auto flex items-center justify-center shadow-2xl shadow-emerald-500/20 rotate-12 transition-transform hover:rotate-0 duration-500">
            <Zap className="text-white" fill="currentColor" size={40} />
          </div>
          <div className="space-y-2">
            <h1 className="text-4xl font-black tracking-tighter italic">MuseTub</h1>
            <p className="text-zinc-500 font-medium">Pay-Per-Second Media</p>
          </div>

          <div className="space-y-3">
            <div className="flex gap-2">
              <button
                className={
                  authMode === 'login'
                    ? 'flex-1 py-3 bg-white text-black font-black rounded-2xl'
                    : 'flex-1 py-3 glass border-zinc-800 text-white font-black rounded-2xl'
                }
                onClick={() => setAuthMode('login')}
                disabled={busy}
              >
                Login
              </button>
              <button
                className={
                  authMode === 'register'
                    ? 'flex-1 py-3 bg-white text-black font-black rounded-2xl'
                    : 'flex-1 py-3 glass border-zinc-800 text-white font-black rounded-2xl'
                }
                onClick={() => setAuthMode('register')}
                disabled={busy}
              >
                Register
              </button>
            </div>

            <input
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="email"
              className="w-full px-4 py-3 rounded-2xl bg-zinc-950 border border-zinc-800"
            />
            <input
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="password"
              type="password"
              className="w-full px-4 py-3 rounded-2xl bg-zinc-950 border border-zinc-800"
            />

            {authMode === 'register' ? (
              <label className="flex items-center gap-2 text-zinc-400 text-sm font-bold justify-center">
                <input type="checkbox" checked={isCreator} onChange={(e) => setIsCreator(e.target.checked)} />
                Creator account
              </label>
            ) : null}

            <button
              onClick={submitAuth}
              disabled={busy || !email || !password}
              className="w-full py-4 bg-emerald-500 text-black font-black rounded-2xl hover:bg-emerald-400 transition-all disabled:opacity-50"
            >
              {busy ? '...' : authMode === 'login' ? 'Login' : 'Register'}
            </button>

            {error ? <div className="text-red-400 text-sm font-bold">{error}</div> : null}
          </div>

          <div className="pt-4 space-y-2">
            <p className="text-[9px] text-zinc-600 uppercase tracking-[0.2em] font-black">Arc • USDC • IPFS</p>
          </div>
        </div>
      </div>
    );
  }

  if (!me) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="glass rounded-3xl p-10">Loading...</div>
      </div>
    );
  }

    return (
      <div className="min-h-screen pb-24 md:pb-0 selection:bg-zinc-200/10">
      <nav className="glass sticky top-0 z-40 px-6 py-4 flex justify-between items-center border-b border-zinc-800">
        <div className="flex items-center gap-8">
          <div className="flex items-center gap-2 group cursor-pointer" onClick={() => setView('home')}>
            <Zap className="text-zinc-200 group-hover:scale-110 transition-transform" fill="currentColor" size={24} />
            <span className="text-2xl font-black tracking-tighter italic">MuseTub</span>
          </div>
          <SettlementVisualizer />
        </div>

        <div className="hidden md:flex items-center gap-10 font-black text-[10px] tracking-[0.2em]">
          <button
            onClick={() => setView('home')}
            className={
              view === 'home'
                ? 'text-white underline decoration-2 underline-offset-8 decoration-zinc-600'
                : 'text-zinc-500 hover:text-white transition-colors'
            }
          >
            MARKET
          </button>
          <button
            onClick={() => setView('user')}
            className={
              view === 'user'
                ? 'text-white underline decoration-2 underline-offset-8 decoration-zinc-600'
                : 'text-zinc-500 hover:text-white transition-colors'
            }
          >
            DASHBOARD
          </button>
          {me.is_creator ? (
            <button
              onClick={() => setView('creator')}
              className={
                view === 'creator'
                  ? 'text-white underline decoration-2 underline-offset-8 decoration-zinc-600'
                  : 'text-zinc-500 hover:text-white transition-colors'
              }
            >
              STUDIO
            </button>
          ) : null}
          <button
            type="button"
            onClick={() => void openWalletPanel()}
            className="flex items-center gap-3 glass px-4 py-2 rounded-xl border-zinc-700 bg-zinc-900/50 hover:border-zinc-500 transition-colors"
          >
            <Wallet size={14} className="text-zinc-200" />
            <span className="mono text-xs tracking-normal">{walletLabel ?? '...'}</span>
          </button>
        </div>

        <div className="flex items-center gap-4">
          <div className="hidden lg:block text-right">
            <div className="text-[10px] text-zinc-600 font-bold uppercase">{me.email}</div>
            <div className="text-xs font-bold mono">{walletLabel ?? ''}</div>
          </div>
          <button onClick={logout} className="p-2 text-zinc-600 hover:text-red-400 transition-colors">
            <LogOut size={20} />
          </button>
        </div>
      </nav>

      <main className="max-w-7xl mx-auto p-6">
        {view === 'home' ? (
          <div className="space-y-12">
            <header className="py-16 text-center space-y-6">
              <h2 className="text-6xl md:text-8xl font-black tracking-tighter leading-none">
                Stream. <br /> <span className="text-zinc-200">Micro-Settle.</span>
              </h2>
              <p className="text-zinc-500 max-w-2xl mx-auto font-medium text-lg leading-relaxed">
                Pay only while you watch.
              </p>
            </header>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-10">
              {content.map((item) => (
                <div
                  key={item.id}
                  className="group glass rounded-[3rem] overflow-hidden border-zinc-800 hover:border-zinc-500 transition-all shadow-2xl shadow-transparent"
                >
                  <div className="relative aspect-video overflow-hidden">
                    <img
                      src={`https://picsum.photos/seed/${item.id}/800/450`}
                      alt={item.title}
                      className="w-full h-full object-cover grayscale-[20%] group-hover:grayscale-0 group-hover:scale-105 transition-all duration-700"
                    />
                    <div className="absolute inset-0 bg-gradient-to-t from-black via-transparent to-transparent opacity-60"></div>
                    <div className="absolute top-6 left-6 bg-zinc-950/80 backdrop-blur-md text-[10px] font-black px-3 py-1.5 rounded-full border border-white/10 uppercase tracking-widest">
                      IPFS
                    </div>
                  </div>
                  <div className="p-10 space-y-8">
                    <div className="flex justify-between items-start">
                      <div className="space-y-2">
                        <h4 className="text-2xl font-black italic group-hover:text-emerald-400 transition-colors leading-tight">
                          {item.title}
                        </h4>
                        <p className="text-zinc-500 font-bold tracking-widest uppercase text-xs">
                          {item.creator_id.slice(0, 8)}
                        </p>
                      </div>
                      <div className="text-right">
                        <div className="text-white mono font-black text-lg">{item.price_per_second}</div>
                        <div className="text-[9px] text-zinc-600 uppercase font-black tracking-widest">Minor/Sec</div>
                      </div>
                    </div>
                    <button
                      onClick={() => setActiveContent(item)}
                      className="w-full py-5 bg-zinc-900 border border-zinc-800 rounded-3xl flex items-center justify-center gap-3 hover:bg-white hover:text-black transition-all font-black text-sm tracking-widest"
                    >
                      WATCH
                      <Zap size={16} fill="currentColor" />
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        ) : view === 'user' ? (
          <UserDashboard token={token} />
        ) : me.is_creator ? (
          <CreatorStudio token={token} onUploaded={() => refreshContent().catch(() => undefined)} />
        ) : (
          <div className="glass p-10 rounded-3xl border-zinc-800">This account is not a creator.</div>
        )}
      </main>

      {activeContent ? (
        <VideoPlayer
          token={token}
          item={activeContent}
          onClose={() => setActiveContent(null)}
        />
      ) : null}

      {walletPanelOpen ? (
        <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-start justify-center p-6" onClick={() => setWalletPanelOpen(false)}>
          <div className="w-full max-w-lg glass rounded-[2.5rem] p-8 border-zinc-800" onClick={(e) => e.stopPropagation()}>
            <div className="flex items-center justify-between gap-4">
              <div>
                <div className="text-[10px] text-zinc-600 font-black uppercase tracking-widest">Wallet</div>
                <div className="mt-1 text-2xl font-black italic">Arc testnet USDC balance</div>
              </div>
              <button
                className="px-4 py-2 bg-zinc-900 rounded-xl text-zinc-400 hover:text-white transition-colors font-black text-xs"
                onClick={() => setWalletPanelOpen(false)}
              >
                CLOSE
              </button>
            </div>

            <div className="mt-6 space-y-3">
              <div className="glass rounded-2xl p-4 border-zinc-800">
                <div className="text-[10px] text-zinc-600 font-black uppercase tracking-widest">Address</div>
                <div className="mono text-xs font-bold text-zinc-200 break-all">{me.wallet_address}</div>
              </div>
              <div className="glass rounded-2xl p-4 border-zinc-800">
                <div className="text-[10px] text-zinc-600 font-black uppercase tracking-widest">USDC</div>
                <div className="mono text-xl font-black text-white">
                  {walletBalanceBusy ? '...' : walletBalance?.balance ?? '—'}
                </div>
                <div className="mt-1 mono text-[10px] font-bold text-zinc-500 break-all">minor: {walletBalance?.balance_minor ?? '—'}</div>
              </div>
              {walletBalanceError ? <div className="text-red-400 text-sm font-bold break-all">{walletBalanceError}</div> : null}
            </div>
          </div>
        </div>
      ) : null}
    </div>
  );
}
