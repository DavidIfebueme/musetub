export default function BrandLogo({ size = 36 }: { size?: number }) {
  return (
    <div
      className="rounded-2xl bg-gradient-to-br from-zinc-900 via-zinc-800 to-zinc-950 border border-white/5 shadow-[0_0_30px_rgba(255,255,255,0.08)]"
      style={{ width: size, height: size }}
    >
      <svg viewBox="0 0 64 64" className="w-full h-full">
        <defs>
          <linearGradient id="mtb" x1="0" y1="0" x2="1" y2="1">
            <stop offset="0" stopColor="#f4f4f5" />
            <stop offset="1" stopColor="#9ca3af" />
          </linearGradient>
        </defs>
        <path
          d="M12 34C12 22.954 20.954 14 32 14s20 8.954 20 20c0 8.5-5.3 15.8-12.8 18.7-2.7 1-5.6-1-5.6-3.8V36.5l-1.6 1.3-10.4 8.4c-2 1.6-4.9.2-4.9-2.3V34z"
          fill="url(#mtb)"
        />
        <circle cx="43" cy="24" r="5" fill="#111827" />
      </svg>
    </div>
  );
}
