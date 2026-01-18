import { useEffect, useState } from 'react';
import { Layers } from 'lucide-react';

export default function SettlementVisualizer() {
  const [blockHeight, setBlockHeight] = useState(0);
  const [progress, setProgress] = useState(0);

  useEffect(() => {
    const interval = window.setInterval(() => {
      setProgress((prev) => {
        if (prev >= 100) {
          setBlockHeight((h) => h + 1);
          return 0;
        }
        return prev + 5;
      });
    }, 100);

    return () => {
      window.clearInterval(interval);
    };
  }, []);

  return (
    <div className="glass px-4 py-2 rounded-2xl flex items-center gap-4 border-emerald-500/20">
      <div className="relative w-8 h-8 flex items-center justify-center">
        <Layers size={18} className="text-emerald-400 absolute animate-pulse" />
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
            className="text-emerald-500 transition-all duration-100"
          />
        </svg>
      </div>
      <div>
        <div className="text-[10px] text-zinc-500 uppercase font-bold tracking-widest">Arc Block Height</div>
        <div className="mono text-xs font-bold text-emerald-400">{blockHeight.toLocaleString()}</div>
      </div>
    </div>
  );
}
