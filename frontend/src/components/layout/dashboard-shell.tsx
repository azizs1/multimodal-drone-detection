"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import type { ReactNode } from "react";

type NavItem = {
  label: string;
  href: string;
};

const NAV_ITEMS: NavItem[] = [
  { label: "Live Feed", href: "/live-feed" },
  { label: "Incidents", href: "/incidents" },
  { label: "Settings", href: "/settings" },
];

type DashboardShellProps = {
  children: ReactNode;
};

export function DashboardShell({ children }: DashboardShellProps) {
  const pathname = usePathname();

  return (
    <div className="min-h-screen bg-slate-100 text-slate-800">
      <header className="border-b border-slate-200 bg-slate-50">
        <nav className="mx-auto flex max-w-7xl items-stretch justify-center gap-6 px-4 sm:gap-12 sm:px-6 lg:px-8">
          {NAV_ITEMS.map((item) => {
            const isActive = pathname === item.href;

            return (
              <Link
                key={item.href}
                href={item.href}
                className={`relative px-2 pt-5 pb-4 text-lg leading-tight transition-colors sm:px-2 sm:pt-6 sm:pb-5 sm:text-xl ${
                  isActive
                    ? "font-bold text-slate-800 after:absolute after:inset-x-0 after:bottom-[-1px] after:h-1 after:bg-cyan-400 after:content-['']"
                    : "font-medium text-slate-800 hover:text-slate-900"
                }`}
              >
                {item.label}
              </Link>
            );
          })}
        </nav>
      </header>

      <main className="mx-auto w-full max-w-7xl px-4 py-6 sm:px-6 lg:px-8">{children}</main>
    </div>
  );
}
