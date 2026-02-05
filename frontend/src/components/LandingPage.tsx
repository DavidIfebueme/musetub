import { useEffect, useMemo, useState } from 'react';

import { requestCreatorAccess, sendContactMessage } from '../services/contact';

import BrandLogo from './BrandLogo';
import Hero3D from './Hero3D';

export default function LandingPage({ onEnter }: { onEnter: () => void }) {
  const [menuOpen, setMenuOpen] = useState(false);
  const [scrollY, setScrollY] = useState(0);
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [message, setMessage] = useState('');
  const [contactBusy, setContactBusy] = useState(false);
  const [contactStatus, setContactStatus] = useState<string | null>(null);
  const [contactError, setContactError] = useState<string | null>(null);

  const [creatorName, setCreatorName] = useState('');
  const [creatorEmail, setCreatorEmail] = useState('');
  const [creatorLink, setCreatorLink] = useState('');
  const [creatorMessage, setCreatorMessage] = useState('');
  const [creatorBusy, setCreatorBusy] = useState(false);
  const [creatorStatus, setCreatorStatus] = useState<string | null>(null);
  const [creatorError, setCreatorError] = useState<string | null>(null);

  useEffect(() => {
    let raf = 0;
    const onScroll = () => {
      cancelAnimationFrame(raf);
      raf = requestAnimationFrame(() => setScrollY(window.scrollY));
    };
    onScroll();
    window.addEventListener('scroll', onScroll, { passive: true });
    return () => {
      cancelAnimationFrame(raf);
      window.removeEventListener('scroll', onScroll);
    };
  }, []);

  const heroShift = useMemo(() => Math.min(scrollY / 6, 80), [scrollY]);

  const sections = [
    { id: 'home', label: 'Home' },
    { id: 'how', label: 'How it works' },
    { id: 'get-started', label: 'Get started' },
    { id: 'creator-beta', label: 'Creator beta' },
    { id: 'contact', label: 'Contact' },
  ];

  return (
    <div className="min-h-screen bg-black text-white overflow-hidden relative">
      <div className="absolute inset-0 bg-black" />
      <Hero3D />
      <div className="relative z-10">
        <div className="max-w-6xl mx-auto px-6 pt-8 pb-20">
          <nav className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <BrandLogo size={44} />
              <div>
                <div className="text-xl font-black tracking-tight">MuseTub</div>
                <div className="text-[10px] uppercase tracking-[0.4em] text-zinc-500">pay per second</div>
              </div>
            </div>
            <div className="hidden md:flex items-center gap-8 text-[10px] uppercase tracking-[0.35em] text-zinc-400">
              {sections.map((section) => (
                <a key={section.id} href={`#${section.id}`} className="hover:text-white transition-colors">
                  {section.label}
                </a>
              ))}
              <button
                onClick={onEnter}
                className="px-5 py-2.5 rounded-full border border-white/15 bg-white/10 hover:bg-white/20 transition text-[10px] uppercase tracking-[0.35em] text-white"
              >
                Sign in
              </button>
            </div>
            <button
              onClick={() => setMenuOpen((v) => !v)}
              className="md:hidden px-4 py-2 rounded-full border border-white/10 bg-white/5 text-xs uppercase tracking-[0.3em]"
            >
              Menu
            </button>
          </nav>

          {menuOpen ? (
            <div className="mt-4 md:hidden glass rounded-3xl p-6 border-white/10 space-y-4 text-sm">
              {sections.map((section) => (
                <a
                  key={section.id}
                  href={`#${section.id}`}
                  className="block text-zinc-300 hover:text-white transition-colors"
                  onClick={() => setMenuOpen(false)}
                >
                  {section.label}
                </a>
              ))}
              <button
                onClick={() => {
                  setMenuOpen(false);
                  onEnter();
                }}
                className="w-full py-3 rounded-2xl bg-white text-black font-black uppercase tracking-[0.35em] text-xs"
              >
                Sign in
              </button>
            </div>
          ) : null}

          <section id="home" className="mt-20 grid grid-cols-1 lg:grid-cols-[1.2fr_0.8fr] gap-12 items-center">
            <div className="space-y-8" style={{ transform: `translate3d(0, ${heroShift}px, 0)` }}>
              <div className="inline-flex items-center gap-3 px-4 py-2 rounded-full border border-white/10 bg-white/5 text-[10px] uppercase tracking-[0.4em] text-zinc-400">
                only pay for what you watch
              </div>
              <h1 className="text-5xl md:text-7xl font-black leading-[0.95] tracking-tight">
                Streaming that charges by the second.
              </h1>
              <p className="text-lg md:text-xl text-zinc-400 max-w-xl">
                Start instantly, stop anytime, and never pay for time you did not watch.
              </p>
              <div className="flex flex-wrap gap-4">
                <button
                  onClick={onEnter}
                  className="px-7 py-4 rounded-2xl bg-white text-black font-black uppercase tracking-widest text-xs"
                >
                  Start watching
                </button>
                <a
                  href="#get-started"
                  className="px-7 py-4 rounded-2xl border border-white/15 bg-white/5 hover:bg-white/10 transition font-black uppercase tracking-widest text-xs"
                >
                  Get started
                </a>
              </div>
            </div>
            <div className="space-y-6">
              <div
                className="rounded-[2.5rem] border border-white/10 bg-white/5 p-8 backdrop-blur"
                style={{ transform: `translate3d(0, ${Math.min(scrollY / 16, 40)}px, 0)` }}
              >
                <div className="text-[10px] uppercase tracking-[0.4em] text-zinc-500">Pay less</div>
                <div className="mt-4 text-3xl font-black">You control the meter</div>
                <div className="mt-2 text-zinc-400 text-sm leading-relaxed">
                  Charges scale with real time watched, not fixed plans or long commitments.
                </div>
              </div>
              <div
                className="rounded-[2.5rem] border border-white/10 bg-gradient-to-br from-white/10 via-white/5 to-transparent p-8 backdrop-blur"
                style={{ transform: `translate3d(0, ${Math.min(scrollY / 12, 50)}px, 0)` }}
              >
                <div className="text-[10px] uppercase tracking-[0.4em] text-zinc-500">Instant access</div>
                <div className="mt-4 text-3xl font-black">Tap play and go</div>
                <div className="mt-2 text-zinc-400 text-sm leading-relaxed">
                  No lock‑in. Jump between creators and only pay for what you consume.
                </div>
              </div>
            </div>
          </section>

          <section id="how" className="mt-28 grid grid-cols-1 md:grid-cols-3 gap-6">
            {[
              {
                title: 'Press play',
                body: 'Streaming starts instantly. Your balance only moves while you watch.',
              },
              {
                title: 'Pause anytime',
                body: 'Pause or leave and charges stop automatically. You stay in control.',
              },
              {
                title: 'Support creators',
                body: 'Your spend flows directly to the creators you watched.',
              },
            ].map((item, index) => (
              <div
                key={item.title}
                className="glass rounded-[2.5rem] p-8 border-white/10"
                style={{ transform: `translate3d(0, ${Math.min(scrollY / 10 + index * 16, 90)}px, 0)` }}
              >
                <div className="text-[10px] uppercase tracking-[0.4em] text-zinc-500">Step {index + 1}</div>
                <div className="mt-4 text-2xl font-black">{item.title}</div>
                <div className="mt-2 text-zinc-400 text-sm leading-relaxed">{item.body}</div>
              </div>
            ))}
          </section>

          <section id="get-started" className="mt-28 grid grid-cols-1 lg:grid-cols-[1.1fr_0.9fr] gap-10 items-center">
            <div className="space-y-6" style={{ transform: `translate3d(0, ${Math.min(scrollY / 14, 60)}px, 0)` }}>
              <div className="text-[10px] uppercase tracking-[0.4em] text-zinc-500">Get started</div>
              <div className="text-4xl md:text-5xl font-black leading-tight">Your first stream is seconds away.</div>
              <div className="text-zinc-400 text-lg">
                Create an account, fund your balance, and explore creators immediately.
              </div>
              <div className="flex flex-wrap gap-4">
                <button
                  onClick={onEnter}
                  className="px-7 py-4 rounded-2xl bg-white text-black font-black uppercase tracking-widest text-xs"
                >
                  Create account
                </button>
                <a
                  href="#contact"
                  className="px-7 py-4 rounded-2xl border border-white/15 bg-white/5 hover:bg-white/10 transition font-black uppercase tracking-widest text-xs"
                >
                  Talk to us
                </a>
              </div>
            </div>
            <div className="glass rounded-[2.5rem] p-10 border-white/10" style={{ transform: `translate3d(0, ${Math.min(scrollY / 10, 80)}px, 0)` }}>
              <div className="text-[10px] uppercase tracking-[0.4em] text-zinc-500">What you get</div>
              <div className="mt-6 space-y-4 text-zinc-300">
                <div className="flex items-center justify-between">
                  <span>Per‑second pricing</span>
                  <span className="font-black text-white">Always on</span>
                </div>
                <div className="flex items-center justify-between">
                  <span>Instant start</span>
                  <span className="font-black text-white">Yes</span>
                </div>
                <div className="flex items-center justify-between">
                  <span>Pause without penalty</span>
                  <span className="font-black text-white">Yes</span>
                </div>
                <div className="flex items-center justify-between">
                  <span>Creator support</span>
                  <span className="font-black text-white">Direct</span>
                </div>
              </div>
            </div>
          </section>

          <section id="creator-beta" className="mt-28 grid grid-cols-1 lg:grid-cols-[1.1fr_0.9fr] gap-10 items-start">
            <div className="space-y-6" style={{ transform: `translate3d(0, ${Math.min(scrollY / 16, 50)}px, 0)` }}>
              <div className="text-[10px] uppercase tracking-[0.4em] text-zinc-500">Creator beta</div>
              <div className="text-4xl md:text-5xl font-black">Request early creator access.</div>
              <div className="text-zinc-400 text-lg">
                Tell us a bit about your content and we will follow up with onboarding details.
              </div>
            </div>
            <form
              className="glass rounded-[2.5rem] p-8 border-white/10 space-y-4"
              style={{ transform: `translate3d(0, ${Math.min(scrollY / 12, 70)}px, 0)` }}
              onSubmit={async (e) => {
                e.preventDefault();
                if (creatorBusy) return;
                setCreatorBusy(true);
                setCreatorError(null);
                setCreatorStatus(null);
                try {
                  await requestCreatorAccess({
                    name: creatorName,
                    email: creatorEmail,
                    channel_link: creatorLink || undefined,
                    message: creatorMessage || undefined,
                  });
                  setCreatorStatus('Request sent. We will follow up soon.');
                  setCreatorName('');
                  setCreatorEmail('');
                  setCreatorLink('');
                  setCreatorMessage('');
                } catch (err) {
                  setCreatorError(String(err));
                } finally {
                  setCreatorBusy(false);
                }
              }}
            >
              <input
                value={creatorName}
                onChange={(e) => setCreatorName(e.target.value)}
                placeholder="name"
                className="w-full px-4 py-3 rounded-2xl bg-zinc-950 border border-white/10 focus:outline-none focus:ring-2 focus:ring-white/30"
                required
              />
              <input
                value={creatorEmail}
                onChange={(e) => setCreatorEmail(e.target.value)}
                placeholder="email"
                type="email"
                className="w-full px-4 py-3 rounded-2xl bg-zinc-950 border border-white/10 focus:outline-none focus:ring-2 focus:ring-white/30"
                required
              />
              <input
                value={creatorLink}
                onChange={(e) => setCreatorLink(e.target.value)}
                placeholder="channel link (optional)"
                className="w-full px-4 py-3 rounded-2xl bg-zinc-950 border border-white/10 focus:outline-none focus:ring-2 focus:ring-white/30"
              />
              <textarea
                value={creatorMessage}
                onChange={(e) => setCreatorMessage(e.target.value)}
                placeholder="tell us about your content"
                className="w-full px-4 py-3 rounded-2xl bg-zinc-950 border border-white/10 min-h-[140px] focus:outline-none focus:ring-2 focus:ring-white/30"
              />
              <button
                type="submit"
                disabled={creatorBusy}
                className="w-full py-4 rounded-2xl bg-white text-black font-black uppercase tracking-widest text-xs disabled:opacity-50"
              >
                {creatorBusy ? 'Sending...' : 'Request access'}
              </button>
              {creatorStatus ? <div className="text-emerald-300 text-sm font-semibold">{creatorStatus}</div> : null}
              {creatorError ? <div className="text-red-400 text-sm font-semibold break-all">{creatorError}</div> : null}
            </form>
          </section>

          <section id="contact" className="mt-28 grid grid-cols-1 lg:grid-cols-[1.1fr_0.9fr] gap-10 items-start">
            <div className="space-y-6" style={{ transform: `translate3d(0, ${Math.min(scrollY / 16, 50)}px, 0)` }}>
              <div className="text-[10px] uppercase tracking-[0.4em] text-zinc-500">Contact</div>
              <div className="text-4xl md:text-5xl font-black">Let’s hear from you.</div>
              <div className="text-zinc-400 text-lg">
                Have feedback, press, or partnership ideas? Send a note.
              </div>
            </div>
            <form
              className="glass rounded-[2.5rem] p-8 border-white/10 space-y-4"
              style={{ transform: `translate3d(0, ${Math.min(scrollY / 12, 70)}px, 0)` }}
              onSubmit={async (e) => {
                e.preventDefault();
                if (contactBusy) return;
                setContactBusy(true);
                setContactError(null);
                setContactStatus(null);
                try {
                  await sendContactMessage({ name, email, message });
                  setContactStatus('Message sent. We will reply soon.');
                  setName('');
                  setEmail('');
                  setMessage('');
                } catch (err) {
                  setContactError(String(err));
                } finally {
                  setContactBusy(false);
                }
              }}
            >
              <input
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="name"
                className="w-full px-4 py-3 rounded-2xl bg-zinc-950 border border-white/10 focus:outline-none focus:ring-2 focus:ring-white/30"
                required
              />
              <input
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="email"
                type="email"
                className="w-full px-4 py-3 rounded-2xl bg-zinc-950 border border-white/10 focus:outline-none focus:ring-2 focus:ring-white/30"
                required
              />
              <textarea
                value={message}
                onChange={(e) => setMessage(e.target.value)}
                placeholder="message"
                className="w-full px-4 py-3 rounded-2xl bg-zinc-950 border border-white/10 min-h-[140px] focus:outline-none focus:ring-2 focus:ring-white/30"
                required
              />
              <button
                type="submit"
                disabled={contactBusy}
                className="w-full py-4 rounded-2xl bg-white text-black font-black uppercase tracking-widest text-xs disabled:opacity-50"
              >
                {contactBusy ? 'Sending...' : 'Send message'}
              </button>
              {contactStatus ? <div className="text-emerald-300 text-sm font-semibold">{contactStatus}</div> : null}
              {contactError ? <div className="text-red-400 text-sm font-semibold break-all">{contactError}</div> : null}
            </form>
          </section>

          <footer className="mt-24 pb-12 text-center text-[10px] uppercase tracking-[0.4em] text-zinc-500">
            MuseTub · Pay per second streaming
          </footer>
        </div>
      </div>
    </div>
  );
}
