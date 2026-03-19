"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import clsx from "clsx";
import { useEffect, useMemo, useState } from "react";

import { getLocalUserId } from "@/lib/session";

const nav = [
  { href: "/dashboard", label: "Home" },
  { href: "/transactions", label: "Transactions" },
  { href: "/insights", label: "Insights" },
  { href: "/goals", label: "Goals" },
  { href: "/settings", label: "Settings" }
];

export function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const [ready, setReady] = useState(false);

  useEffect(() => {
    setReady(true);
  }, []);

  const showNav = useMemo(() => pathname !== "/onboarding", [pathname]);
  const userId = ready ? getLocalUserId() : null;

  return (
    <div className="min-h-screen">
      <div className="mx-auto max-w-md px-4 pb-24 pt-6">
        <header className="mb-6 flex items-center justify-between">
          <div>
            <div className="text-xs font-medium text-ink-700/70">Personal Finance, but Smarter</div>
            <div className="text-xl font-semibold tracking-tight">A calm money coach</div>
          </div>
          {showNav && (
            <div className="rounded-full border border-ink-200/70 bg-white/60 px-3 py-1 text-xs text-ink-800 shadow-soft">
              {userId ? "Demo user" : "Not onboarded"}
            </div>
          )}
        </header>
        {children}
      </div>

      {showNav && (
        <nav className="fixed inset-x-0 bottom-0 mx-auto max-w-md px-4 pb-5">
          <div className="glass rounded-2xl border border-ink-200/60 shadow-card">
            <div className="grid grid-cols-5">
              {nav.map((item) => {
                const active = pathname?.startsWith(item.href);
                return (
                  <Link
                    key={item.href}
                    href={item.href}
                    className={clsx(
                      "px-2 py-3 text-center text-[11px] font-medium",
                      active ? "text-ink-800" : "text-ink-700/70"
                    )}
                  >
                    <div
                      className={clsx(
                        "mx-auto mb-1 h-1.5 w-6 rounded-full",
                        active ? "bg-ink-600" : "bg-transparent"
                      )}
                    />
                    {item.label}
                  </Link>
                );
              })}
            </div>
          </div>
        </nav>
      )}
    </div>
  );
}

