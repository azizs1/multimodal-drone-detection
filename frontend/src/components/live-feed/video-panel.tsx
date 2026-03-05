import type { ReactNode } from "react";

type VideoPanelProps = {
  title: string;
  fps: string;
  resolution: string;
  children?: ReactNode;
};

export function VideoPanel({ title, fps, resolution, children }: VideoPanelProps) {
  return (
    <section className="overflow-hidden rounded-sm border border-slate-200 bg-slate-50 dark:border-slate-800 dark:bg-slate-900">
      <div className="flex items-center justify-between border-b border-slate-200 px-3 py-2 dark:border-slate-800">
        <div className="flex items-center gap-2 text-slate-700 dark:text-slate-200">
          <span className="size-3 rounded-full bg-emerald-500" />
          <span className="text-base font-semibold">{title}</span>
        </div>
        <span className="text-sm font-medium text-slate-500 dark:text-slate-400">Live {fps} fps</span>
      </div>

      <div className="h-[280px] bg-slate-100 sm:h-[320px] lg:h-[360px] dark:bg-slate-800">
        {children}
      </div>

      <div className="px-3 py-2 text-sm text-slate-500 dark:text-slate-400">{resolution}</div>
    </section>
  );
}
