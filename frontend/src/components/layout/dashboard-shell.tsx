"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Moon, Settings, Sun } from "lucide-react";
import type { ReactNode } from "react";
import { useTheme } from "@/components/theme-provider";

type NavItem = {
  label: string;
  href: string;
};

const NAV_ITEMS: NavItem[] = [
  { label: "Live Feed", href: "/live-feed" },
  { label: "Incidents", href: "/incidents" },
];

type DashboardShellProps = {
  children: ReactNode;
};

export function DashboardShell({ children }: DashboardShellProps) {
  const pathname = usePathname();
  const { setTheme } = useTheme();

  return (
    <div className="min-h-screen bg-slate-100 text-slate-800 dark:bg-slate-950 dark:text-slate-100">
      <header className="border-b border-slate-200 bg-slate-50 dark:border-slate-800 dark:bg-slate-900">
        <nav className="mx-auto flex max-w-7xl items-stretch px-4 sm:px-6 lg:px-8">
          <div className="flex flex-1 items-stretch justify-start gap-6 sm:gap-12">
            {NAV_ITEMS.map((item) => {
              const isActive = pathname === item.href;

              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={`relative inline-flex px-2 pt-5 pb-4 text-lg leading-tight transition-colors sm:pt-6 sm:pb-5 sm:text-xl ${
                    isActive
                      ? "font-bold text-slate-800 after:absolute after:inset-x-0 after:bottom-[-1px] after:h-1 after:bg-cyan-400 after:content-[''] dark:text-slate-100"
                      : "font-medium text-slate-800 hover:text-slate-900 dark:text-slate-300 dark:hover:text-slate-100"
                  }`}
                >
                  {item.label}
                </Link>
              );
            })}
          </div>
          <div className="flex items-stretch gap-2">
            <button
              type="button"
              aria-label="Toggle theme"
              onClick={() => {
                const isDark = document.documentElement.classList.contains("dark");
                setTheme(isDark ? "light" : "dark");
              }}
              className="inline-flex w-10 items-center justify-center pt-5 pb-4 text-slate-700 transition-colors hover:text-slate-900 sm:pt-6 sm:pb-5 dark:text-slate-300 dark:hover:text-slate-100"
            >
              <Sun className="hidden size-5 dark:block" />
              <Moon className="size-5 dark:hidden" />
            </button>

            <Link
              href="/settings"
              aria-label="Settings"
              className={`inline-flex w-10 items-center justify-end pt-5 pb-4 transition-colors sm:pt-6 sm:pb-5 ${
                pathname === "/settings"
                  ? "text-cyan-400"
                  : "text-slate-700 hover:text-slate-900 dark:text-slate-300 dark:hover:text-slate-100"
              }`}
            >
              <Settings className="size-5" />
            </Link>
          </div>
        </nav>
      </header>

      <main className="mx-auto w-full max-w-7xl px-4 py-6 sm:px-6 lg:px-8">{children}</main>
    </div>
  );
}
