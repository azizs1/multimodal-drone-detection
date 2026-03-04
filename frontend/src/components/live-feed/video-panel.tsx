type VideoPanelProps = {
  title: string;
  fps: string;
  resolution: string;
  boxColor: string;
  boxLabel: string;
};

export function VideoPanel({ title, fps, resolution, boxColor, boxLabel }: VideoPanelProps) {
  return (
    <section className="overflow-hidden rounded-sm border border-slate-200 bg-slate-50 dark:border-slate-800 dark:bg-slate-900">
      <div className="flex items-center justify-between border-b border-slate-200 px-3 py-2 dark:border-slate-800">
        <div className="flex items-center gap-2 text-slate-700 dark:text-slate-200">
          <span className="size-3 rounded-full bg-emerald-500" />
          <span className="text-base font-semibold">{title}</span>
        </div>
        <span className="text-sm font-medium text-slate-500 dark:text-slate-400">Live {fps} fps</span>
      </div>

      <div className="relative h-[280px] bg-slate-100 sm:h-[320px] lg:h-[360px] dark:bg-slate-800">
        <div className="absolute inset-0 flex items-center justify-center text-5xl text-slate-400 dark:text-slate-500">+</div>
        <div
          className={`absolute left-1/2 top-1/2 h-20 w-28 -translate-x-1/2 -translate-y-1/2 border-4 ${boxColor}`}
        >
          <span className={`absolute -left-1 -top-8 px-1 text-sm font-semibold ${boxColor}`}>
            {boxLabel}
          </span>
        </div>
      </div>

      <div className="px-3 py-2 text-sm text-slate-500 dark:text-slate-400">{resolution}</div>
    </section>
  );
}
