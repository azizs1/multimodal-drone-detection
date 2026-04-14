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

function SeverityIcon({ severity }: Pick<AlertBannerData, "severity">) {
  if (severity === "critical") {
    return <AlertTriangle className="size-[1.7rem]" aria-hidden="true" />;
  }

  if (severity === "warning") {
    return <Bell className="size-[1.7rem]" aria-hidden="true" />;
  }

  return <Info className="size-[1.7rem]" aria-hidden="true" />;
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
        "relative overflow-hidden rounded-sm border shadow-sm transition-colors",
        SEVERITY_STYLES[alert.severity],
        className,
      )}
    >
      <div
        className={cn(
          "absolute inset-y-0 left-0 w-1.5",
          alert.severity === "critical"
            ? "bg-rose-500"
            : alert.severity === "warning"
              ? "bg-amber-500"
              : "bg-sky-500",
        )}
      />

      <div className="flex flex-col gap-4 px-4 py-3 pl-5 md:flex-row md:items-start md:justify-between">
        <div className="flex min-w-0 gap-4">
          <div className="mt-2 shrink-0 text-current/85">
            <SeverityIcon severity={alert.severity} />
          </div>

          <div className="min-w-0">
            <p className="text-base font-semibold leading-tight md:text-[1.05rem]">
              {alert.title}
            </p>

            <p className="mt-1 line-clamp-2 text-sm leading-6 opacity-90">{alert.message}</p>

            <div className="mt-3 flex flex-wrap items-center gap-x-4 gap-y-2 text-xs font-medium opacity-80">
              <span className="inline-flex items-center rounded-full border border-black/8 bg-white/35 px-2.5 py-1 dark:border-white/10 dark:bg-white/8">
                {formatAlertTimestamp(alert.occurredAt)}
              </span>
              {typeof alert.confidence === "number" ? (
                <span className="inline-flex items-center rounded-full border border-black/8 bg-white/35 px-2.5 py-1 dark:border-white/10 dark:bg-white/8">
                  Confidence {Math.round(alert.confidence * 100)}%
                </span>
              ) : null}
              {alert.streamName ? (
                <span className="inline-flex items-center rounded-full border border-black/8 bg-white/35 px-2.5 py-1 dark:border-white/10 dark:bg-white/8">
                  Stream {alert.streamName}
                </span>
              ) : null}
            </div>
          </div>
        </div>

        <div className="flex shrink-0 items-start gap-2 md:pl-4">
          {action}
          {alert.dismissible && onDismiss ? (
            <button
              type="button"
              aria-label="Dismiss alert"
              onClick={onDismiss}
              className="inline-flex size-9 items-center justify-center rounded-md border border-black/10 bg-white/40 transition-colors hover:bg-white/70 dark:border-white/10 dark:bg-white/5 dark:hover:bg-white/10"
            >
              <X className="size-4" aria-hidden="true" />
            </button>
          ) : null}
        </div>
      </div>
    </section>
  );
}
