"use client";

import { AlertTriangle, Bell, Info, X } from "lucide-react";
import { type ReactNode } from "react";
import { type AlertBannerData } from "@/lib/alerts";
import { cn } from "@/lib/utils";

type AlertBannerProps = {
  alert: AlertBannerData;
  onDismiss?: () => void;
  action?: ReactNode;
  className?: string;
};

const SEVERITY_STYLES: Record<AlertBannerData["severity"], string> = {
  info: "border-sky-300 bg-sky-50 text-sky-950 dark:border-sky-800/70 dark:bg-sky-950/40 dark:text-sky-100",
  warning:
    "border-amber-300 bg-amber-50 text-amber-950 dark:border-amber-700/70 dark:bg-amber-950/40 dark:text-amber-100",
  critical:
    "border-rose-300 bg-rose-50 text-rose-950 dark:border-rose-700/70 dark:bg-rose-950/40 dark:text-rose-100",
};

const CHIP_STYLES: Record<AlertBannerData["severity"], string> = {
  info: "bg-sky-100 text-sky-800 dark:bg-sky-900/60 dark:text-sky-100",
  warning: "bg-amber-100 text-amber-800 dark:bg-amber-900/60 dark:text-amber-100",
  critical: "bg-rose-100 text-rose-800 dark:bg-rose-900/60 dark:text-rose-100",
};

function SeverityIcon({ severity }: Pick<AlertBannerData, "severity">) {
  if (severity === "critical") {
    return <AlertTriangle className="size-5" aria-hidden="true" />;
  }

  if (severity === "warning") {
    return <Bell className="size-5" aria-hidden="true" />;
  }

  return <Info className="size-5" aria-hidden="true" />;
}

function formatAlertTimestamp(value: string) {
  const date = new Date(value);

  if (Number.isNaN(date.getTime())) {
    return value;
  }

  return new Intl.DateTimeFormat("en-US", {
    month: "short",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  }).format(date);
}

export function AlertBanner({ alert, onDismiss, action, className }: AlertBannerProps) {
  return (
    <section
      role="alert"
      aria-live="polite"
      className={cn(
        "rounded-sm border px-4 py-3 shadow-sm",
        "transition-colors",
        SEVERITY_STYLES[alert.severity],
        className,
      )}
    >
      <div className="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
        <div className="flex min-w-0 gap-3">
          <div className="mt-0.5 shrink-0">
            <SeverityIcon severity={alert.severity} />
          </div>

          <div className="min-w-0">
            <div className="flex flex-wrap items-center gap-2">
              <p className="text-sm font-semibold tracking-wide">{alert.title}</p>
              <span
                className={cn(
                  "inline-flex rounded-full px-2 py-0.5 text-[11px] font-semibold uppercase tracking-wide",
                  CHIP_STYLES[alert.severity],
                )}
              >
                {alert.source}
              </span>
              {alert.confidenceBand ? (
                <span className="inline-flex rounded-full bg-black/8 px-2 py-0.5 text-[11px] font-semibold uppercase tracking-wide dark:bg-white/10">
                  {alert.confidenceBand}
                </span>
              ) : null}
            </div>

            <p className="mt-1 text-sm opacity-90">{alert.message}</p>

            <div className="mt-2 flex flex-wrap items-center gap-x-4 gap-y-1 text-xs font-medium opacity-80">
              <span>{formatAlertTimestamp(alert.occurredAt)}</span>
              {typeof alert.confidence === "number" ? (
                <span>Confidence {Math.round(alert.confidence * 100)}%</span>
              ) : null}
              {alert.streamName ? <span>Stream {alert.streamName}</span> : null}
            </div>
          </div>
        </div>

        <div className="flex shrink-0 items-start gap-2 md:pl-4">
          {action}
          {alert.dismissible ? (
            <button
              type="button"
              aria-label="Dismiss alert"
              onClick={onDismiss}
              className="inline-flex size-8 items-center justify-center rounded-md border border-black/10 bg-white/40 transition-colors hover:bg-white/70 dark:border-white/10 dark:bg-white/5 dark:hover:bg-white/10"
            >
              <X className="size-4" aria-hidden="true" />
            </button>
          ) : null}
        </div>
      </div>
    </section>
  );
}
