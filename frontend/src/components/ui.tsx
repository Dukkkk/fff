"use client";

import clsx from "clsx";
import type { ButtonHTMLAttributes, InputHTMLAttributes } from "react";

export function Card({
  children,
  className
}: {
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <div className={clsx("glass rounded-2xl border border-ink-200/60 p-4 shadow-card", className)}>
      {children}
    </div>
  );
}

export function CardTitle({ children }: { children: React.ReactNode }) {
  return <div className="text-sm font-semibold text-ink-900">{children}</div>;
}

export function Muted({ children }: { children: React.ReactNode }) {
  return <div className="text-xs text-ink-700/70">{children}</div>;
}

export function Button({
  className,
  ...props
}: ButtonHTMLAttributes<HTMLButtonElement> & { variant?: "primary" | "ghost" }) {
  const variant = (props as any).variant ?? "primary";
  return (
    <button
      {...props}
      className={clsx(
        "inline-flex items-center justify-center rounded-xl px-4 py-2 text-sm font-semibold transition",
        "disabled:cursor-not-allowed disabled:opacity-50",
        variant === "primary"
          ? "bg-ink-800 text-white shadow-soft hover:bg-ink-900"
          : "bg-transparent text-ink-900 hover:bg-white/60",
        className
      )}
    />
  );
}

export function Input({ className, ...props }: InputHTMLAttributes<HTMLInputElement>) {
  return (
    <input
      {...props}
      className={clsx(
        "w-full rounded-xl border border-ink-200/70 bg-white/70 px-3 py-2 text-sm outline-none",
        "focus:border-ink-400 focus:ring-2 focus:ring-ink-200/60",
        className
      )}
    />
  );
}

export function Select({
  className,
  ...props
}: React.SelectHTMLAttributes<HTMLSelectElement>) {
  return (
    <select
      {...props}
      className={clsx(
        "w-full rounded-xl border border-ink-200/70 bg-white/70 px-3 py-2 text-sm outline-none",
        "focus:border-ink-400 focus:ring-2 focus:ring-ink-200/60",
        className
      )}
    />
  );
}

export function Pill({ children, tone = "neutral" }: { children: React.ReactNode; tone?: "neutral" | "good" | "warn" | "bad" }) {
  const toneCls =
    tone === "good"
      ? "bg-emerald-100 text-emerald-900 border-emerald-200/60"
      : tone === "warn"
        ? "bg-amber-100 text-amber-900 border-amber-200/60"
        : tone === "bad"
          ? "bg-rose-100 text-rose-900 border-rose-200/60"
          : "bg-ink-100/70 text-ink-900 border-ink-200/60";
  return <span className={clsx("inline-flex items-center rounded-full border px-2 py-0.5 text-[11px] font-medium", toneCls)}>{children}</span>;
}

