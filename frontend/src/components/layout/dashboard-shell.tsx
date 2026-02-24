"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Settings } from "lucide-react";
import type { ReactNode } from "react";

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

  return (
    <div className="min-h-screen bg-slate-100 text-slate-800">
      <header className="border-b border-slate-200 bg-slate-50">
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
                      ? "font-bold text-slate-800 after:absolute after:inset-x-0 after:bottom-[-1px] after:h-1 after:bg-cyan-400 after:content-['']"
                      : "font-medium text-slate-800 hover:text-slate-900"
                  }`}
                >
                  {item.label}
                </Link>
              );
            })}
          </div>
          <Link
            href="/settings"
            aria-label="Settings"
            className={`inline-flex w-12 items-center justify-end pt-5 pb-4 transition-colors sm:pt-6 sm:pb-5 ${
              pathname === "/settings" ? "text-cyan-400" : "text-slate-700 hover:text-slate-900"
            }`}
          >
            <Settings className="size-5" />
          </Link>
        </nav>
      </header>

      <main className="mx-auto w-full max-w-7xl px-4 py-6 sm:px-6 lg:px-8">{children}</main>
    </div>
  );
}
