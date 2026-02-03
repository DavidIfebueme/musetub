import { useEffect, useState } from 'react';
import { Layers } from 'lucide-react';

import { getArcBlockHeight } from '../services/wallets';

export default function SettlementVisualizer() {
  const [blockHeight, setBlockHeight] = useState<number | null>(null);
  const [progress, setProgress] = useState(0);

  useEffect(() => {
    let cancelled = false;

    async function refreshHeight() {
      try {
        const resp = await getArcBlockHeight();
        if (!cancelled) {
          setBlockHeight(resp.block_height);
        }
      } catch {

      }
    }

    void refreshHeight();

    const interval = window.setInterval(() => {
      setProgress((prev) => (prev >= 100 ? 0 : prev + 5));
    }, 1_000);

    const refreshInterval = window.setInterval(() => {
      void refreshHeight();
    }, 10_000);

    return () => {
      cancelled = true;
      window.clearInterval(interval);
      window.clearInterval(refreshInterval);
    };
  }, []);

  return (
    <div className="glass px-4 py-2 rounded-full flex items-center gap-4 border-white/10">
      <div className="relative w-8 h-8 flex items-center justify-center">
        <Layers size={18} className="text-zinc-200 absolute animate-pulse" />
        <svg className="w-8 h-8 -rotate-90">
          <circle cx="16" cy="16" r="14" stroke="currentColor" strokeWidth="2" fill="transparent" className="text-zinc-800" />
          <circle
            cx="16"
            cy="16"
            r="14"
            stroke="currentColor"
            strokeWidth="2"
            fill="transparent"
            strokeDasharray={88}
            strokeDashoffset={88 - (88 * progress) / 100}
            className="text-white transition-all duration-100"
          />
        </svg>
      </div>
      <div>
        <div className="text-[10px] text-zinc-500 uppercase font-bold tracking-[0.3em]">Network</div>
        <div className="text-xs font-bold text-zinc-200">{blockHeight === null ? 'Connecting' : 'Live'}</div>
      </div>
    </div>
  );
}
