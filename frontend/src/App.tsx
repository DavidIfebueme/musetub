import { useEffect, useMemo, useState } from 'react';
import { LogOut, Wallet } from 'lucide-react';

import SettlementVisualizer from './components/SettlementVisualizer';
import VideoPlayer from './components/VideoPlayer';
import CreatorStudio from './components/CreatorStudio';
import UserDashboard from './components/UserDashboard';
import LandingPage from './components/LandingPage';
import AuthPage from './components/AuthPage';
import BrandLogo from './components/BrandLogo';
import { formatUsdcMinor, formatUsdcDecimal } from './utils/format';
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
  const [unauthView, setUnauthView] = useState<'landing' | 'auth'>('landing');
  const [meLoading, setMeLoading] = useState(false);
  const [meError, setMeError] = useState<string | null>(null);
  const [showOnboarding, setShowOnboarding] = useState(false);

  useEffect(() => {
    let cancelled = false;

    async function load() {
      if (!token) {
        setMe(null);
        setMeError(null);
        setMeLoading(false);
        return;
      }

      setMeLoading(true);
      setMeError(null);

      const meResp = await getMe(token);
      if (!cancelled) {
        setMe(meResp);
        setMeLoading(false);
      }
    }

    load().catch((e) => {
      setError(String(e));
      setMe(null);
      setMeError(String(e));
      setMeLoading(false);
    });

    return () => {
      cancelled = true;
    };
  }, [token]);

  useEffect(() => {
    if (!me) return;
    const seen = localStorage.getItem('musetub_onboarding_seen');
    if (!seen) {
      setShowOnboarding(true);
      localStorage.setItem('musetub_onboarding_seen', 'true');
    }
  }, [me]);

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
    if (unauthView === 'landing') {
      return <LandingPage onEnter={() => setUnauthView('auth')} />;
    }
    return (
      <AuthPage
        authMode={authMode}
        setAuthMode={setAuthMode}
        busy={busy}
        email={email}
        setEmail={setEmail}
        password={password}
        setPassword={setPassword}
        isCreator={isCreator}
        setIsCreator={setIsCreator}
        submitAuth={submitAuth}
        error={error}
        onBack={() => setUnauthView('landing')}
      />
    );
  }

  if (!me) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="glass rounded-3xl p-10 border-white/10 space-y-4 text-center">
          <div className="text-white font-black text-lg">{meLoading ? 'Loading...' : 'Unable to load account'}</div>
          {meError ? <div className="text-red-400 text-sm font-bold break-all">{meError}</div> : null}
          <div className="flex items-center justify-center gap-3">
            <button
              onClick={() => setToken(getStoredAuthToken())}
              className="px-4 py-2 bg-white text-black rounded-xl font-black text-xs uppercase tracking-[0.3em]"
            >
              Retry
            </button>
            <button
              onClick={logout}
              className="px-4 py-2 bg-white/10 text-zinc-300 rounded-xl font-black text-xs uppercase tracking-[0.3em]"
            >
              Logout
            </button>
          </div>
        </div>
      </div>
    );
  }

    return (
        <div className="min-h-screen pb-24 md:pb-0 selection:bg-white/10">
          <nav className="glass sticky top-0 z-40 px-6 py-4 flex justify-between items-center border-b border-white/10">
        <div className="flex items-center gap-8">
          <div className="flex items-center gap-2 group cursor-pointer" onClick={() => setView('home')}>
                <BrandLogo size={32} />
                <span className="text-2xl font-black tracking-tight">MuseTub</span>
          </div>
          <SettlementVisualizer />
        </div>

        <div className="hidden md:flex items-center gap-8 font-black text-[10px] tracking-[0.35em] uppercase">
          <button
            onClick={() => setView('home')}
            className={
              view === 'home'
                ? 'text-white underline decoration-2 underline-offset-8 decoration-white/40'
                : 'text-zinc-500 hover:text-white transition-colors'
            }
          >
            MARKET
          </button>
          <button
            onClick={() => setView('user')}
            className={
              view === 'user'
                ? 'text-white underline decoration-2 underline-offset-8 decoration-white/40'
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
                  ? 'text-white underline decoration-2 underline-offset-8 decoration-white/40'
                  : 'text-zinc-500 hover:text-white transition-colors'
              }
            >
              STUDIO
            </button>
          ) : null}
          <button
            type="button"
            onClick={() => void openWalletPanel()}
            className="flex items-center gap-3 glass px-4 py-2 rounded-full border-white/10 bg-white/5 hover:border-white/30 transition-colors"
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
            <header className="py-8 flex flex-col md:flex-row md:items-end md:justify-between gap-4">
              <div>
                <div className="text-[10px] uppercase tracking-[0.35em] text-zinc-500">Explore</div>
                <h2 className="text-3xl md:text-5xl font-black tracking-tight">Pick a stream</h2>
              </div>
              <div className="text-zinc-400 text-sm">Per‑second pricing. Pause anytime.</div>
            </header>

            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
              {content.map((item) => (
                <div
                  key={item.id}
                  className="group glass rounded-[2rem] overflow-hidden border-white/10 hover:border-white/30 transition-all"
                >
                  <div className="relative aspect-video overflow-hidden">
                    <img
                      src={`https://picsum.photos/seed/${item.id}/800/450`}
                      alt={item.title}
                      className="w-full h-full object-cover grayscale-[35%] group-hover:grayscale-0 group-hover:scale-105 transition-all duration-700"
                    />
                    <div className="absolute inset-0 bg-gradient-to-t from-black via-transparent to-transparent opacity-70" />
                    <div className="absolute bottom-4 left-4 text-xs uppercase tracking-[0.25em] text-zinc-300">
                      {formatUsdcMinor(item.price_per_second)} USDC / sec
                    </div>
                  </div>
                  <div className="p-5 space-y-4">
                    <div className="flex justify-between items-start">
                      <div className="space-y-2">
                        <h4 className="text-lg font-black group-hover:text-white transition-colors leading-tight">
                          {item.title}
                        </h4>
                        <p className="text-zinc-500 font-bold tracking-[0.3em] uppercase text-[10px]">
                          {item.creator_id.slice(0, 8)}
                        </p>
                      </div>
                    </div>
                    <button
                      onClick={() => setActiveContent(item)}
                      className="w-full py-3 bg-white text-black rounded-2xl flex items-center justify-center gap-3 hover:bg-zinc-100 transition-all font-black text-xs tracking-[0.35em] uppercase"
                    >
                      WATCH
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
          <div className="w-full max-w-lg glass rounded-[2.5rem] p-8 border-white/10" onClick={(e) => e.stopPropagation()}>
            <div className="flex items-center justify-between gap-4">
              <div>
                <div className="text-[10px] text-zinc-500 font-black uppercase tracking-[0.35em]">Wallet</div>
                <div className="mt-1 text-2xl font-black">USDC balance</div>
              </div>
              <button
                className="px-4 py-2 bg-white/10 rounded-xl text-zinc-300 hover:text-white transition-colors font-black text-xs"
                onClick={() => setWalletPanelOpen(false)}
              >
                CLOSE
              </button>
            </div>

            <div className="mt-6 space-y-3">
              <div className="glass rounded-2xl p-4 border-white/10">
                <div className="text-[10px] text-zinc-500 font-black uppercase tracking-[0.35em]">Address</div>
                <div className="mono text-xs font-bold text-zinc-200 break-all">{me.wallet_address}</div>
              </div>
              <div className="glass rounded-2xl p-4 border-white/10">
                <div className="text-[10px] text-zinc-500 font-black uppercase tracking-[0.35em]">Balance</div>
                <div className="mono text-xl font-black text-white">
                  {walletBalanceBusy ? '...' : formatUsdcDecimal(walletBalance?.balance)}
                </div>
              </div>
              {walletBalanceError ? <div className="text-red-400 text-sm font-bold break-all">{walletBalanceError}</div> : null}
            </div>
          </div>
        </div>
      ) : null}

      {showOnboarding ? (
        <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-6">
          <div className="w-full max-w-xl glass rounded-[2.5rem] p-8 border-white/10 text-center space-y-6">
            <div className="text-[10px] uppercase tracking-[0.35em] text-zinc-500">Welcome</div>
            <div className="text-3xl font-black">Pay only while you watch</div>
            <div className="text-zinc-400 text-sm">
              Start a video and your balance only moves while it plays. Pause anytime to stop charges.
            </div>
            <button
              onClick={() => setShowOnboarding(false)}
              className="px-6 py-3 rounded-2xl bg-white text-black font-black uppercase tracking-[0.35em] text-xs"
            >
              Got it
            </button>
          </div>
        </div>
      ) : null}
    </div>
  );
}
