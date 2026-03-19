"use client";

import { useEffect, useMemo, useState } from "react";

import { Card, CardTitle, Muted, Pill } from "@/components/ui";
import { api } from "@/lib/api";
import { getLocalUserId, getLocalUserName } from "@/lib/session";
import type { ForecastOut, InsightOut, NudgeOut, StressScoreOut, TransactionOut, GoalOut } from "@/types/api";
import { BalanceCurve } from "@/components/charts/BalanceCurve";

function money(n: number) {
  return n.toLocaleString(undefined, { style: "currency", currency: "USD", maximumFractionDigits: 0 });
}

export default function DashboardPage() {
  const [loading, setLoading] = useState(true);
  const [forecast, setForecast] = useState<ForecastOut | null>(null);
  const [stress, setStress] = useState<StressScoreOut | null>(null);
  const [insights, setInsights] = useState<InsightOut[]>([]);
  const [nudges, setNudges] = useState<NudgeOut[]>([]);
  const [txns, setTxns] = useState<TransactionOut[]>([]);
  const [goals, setGoals] = useState<GoalOut[]>([]);
  const userId = getLocalUserId();
  const name = getLocalUserName() ?? "there";

  useEffect(() => {
    let cancelled = false;
    async function run() {
      if (!userId) {
        setLoading(false);
        return;
      }
      setLoading(true);
      try {
        const [fc, st, ins, nd, tx, gs] = await Promise.all([
          api.forecast(userId),
          api.stress(userId),
          api.insights(userId),
          api.nudges(userId),
          api.listTransactions(userId),
          api.listGoals(userId)
        ]);
        if (cancelled) return;
        setForecast(fc);
        setStress(st);
        setInsights(ins);
        setNudges(nd);
        setTxns(tx.slice(0, 6));
        setGoals(gs);
      } finally {
        if (!cancelled) setLoading(false);
      }
    }
    run();
    return () => {
      cancelled = true;
    };
  }, [userId]);

  const topInsight = insights[0];
  const topNudge = nudges[0];
  const goal = goals[0];

  const statusTone = useMemo(() => {
    if (!forecast) return "neutral" as const;
    if (forecast.safety_status === "safe") return "good" as const;
    if (forecast.safety_status === "tight") return "warn" as const;
    return "bad" as const;
  }, [forecast]);

  if (!userId) {
    return (
      <Card>
        <CardTitle>You're not onboarded</CardTitle>
        <Muted>Go to onboarding to create a user, then come back to see your dashboard.</Muted>
      </Card>
    );
  }

  return (
    <div className="space-y-4">
      <Card>
        <div className="flex items-start justify-between gap-3">
          <div>
            <div className="text-xs font-medium text-ink-700/70">Hi {name}</div>
            <div className="text-2xl font-semibold tracking-tight">Here’s what matters today</div>
          </div>
          {forecast && <Pill tone={statusTone}>{forecast.safety_status === "safe" ? "Safe" : forecast.safety_status === "tight" ? "Tight" : "At risk"}</Pill>}
        </div>
      </Card>

      <div className="grid grid-cols-2 gap-3">
        <Card className="space-y-1">
          <Muted>Current balance</Muted>
          <div className="text-2xl font-semibold">{forecast ? money(forecast.current_balance) : loading ? "—" : "—"}</div>
          <Muted>As of today</Muted>
        </Card>
        <Card className="space-y-1">
          <Muted>Days until broke</Muted>
          <div className="text-2xl font-semibold">
            {forecast ? (forecast.days_until_broke === null ? "—" : `${forecast.days_until_broke}d`) : "—"}
          </div>
          <Muted>{forecast ? forecast.summary : loading ? "Loading forecast…" : "—"}</Muted>
        </Card>
      </div>

      <Card className="space-y-3">
        <div className="flex items-baseline justify-between">
          <CardTitle>Projected balance</CardTitle>
          <Muted>30 days</Muted>
        </div>
        {forecast ? <BalanceCurve points={forecast.curve} /> : <Muted>Loading…</Muted>}
      </Card>

      <div className="grid grid-cols-2 gap-3">
        <Card className="space-y-1">
          <Muted>Stress score</Muted>
          <div className="text-2xl font-semibold">{stress ? `${stress.score}` : "—"}</div>
          <Muted>{stress ? stress.label.toUpperCase() : loading ? "Loading…" : "—"}</Muted>
        </Card>
        <Card className="space-y-1">
          <Muted>Top insight</Muted>
          <div className="text-sm font-semibold leading-snug">{topInsight ? topInsight.title : loading ? "Loading…" : "—"}</div>
          <Muted>{topInsight ? topInsight.description : ""}</Muted>
        </Card>
      </div>

      <Card className="space-y-2">
        <CardTitle>Coach</CardTitle>
        <div className="text-sm font-semibold">{topNudge ? topNudge.title : loading ? "Loading…" : "—"}</div>
        <Muted>{topNudge ? topNudge.message : ""}</Muted>
        {topNudge?.action_label && <div className="pt-2"><Pill>{topNudge.action_label}</Pill></div>}
      </Card>

      <Card className="space-y-3">
        <div className="flex items-baseline justify-between">
          <CardTitle>Latest transactions</CardTitle>
          <Muted>{txns.length} shown</Muted>
        </div>
        <div className="space-y-2">
          {txns.map((t) => (
            <div key={t.id} className="flex items-center justify-between rounded-xl bg-white/60 px-3 py-2">
              <div>
                <div className="text-sm font-semibold">{t.merchant || t.category}</div>
                <Muted>{t.date} • {t.category}</Muted>
              </div>
              <div className={t.type === "income" ? "text-emerald-700 font-semibold" : "text-ink-900 font-semibold"}>
                {t.type === "income" ? "+" : "-"}
                {money(t.amount)}
              </div>
            </div>
          ))}
          {!txns.length && <Muted>No transactions yet.</Muted>}
        </div>
      </Card>

      <Card className="space-y-2">
        <CardTitle>Goal progress</CardTitle>
        {goal ? (
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <div className="text-sm font-semibold">{goal.title}</div>
              <Muted>
                {money(goal.current_amount)} / {money(goal.target_amount)}
              </Muted>
            </div>
            <div className="h-2 w-full overflow-hidden rounded-full bg-ink-100/60">
              <div
                className="h-full rounded-full bg-ink-700"
                style={{ width: `${Math.min(100, (goal.current_amount / goal.target_amount) * 100)}%` }}
              />
            </div>
            <Muted>Target date: {goal.target_date}</Muted>
          </div>
        ) : (
          <Muted>Create a goal to get saving guidance.</Muted>
        )}
      </Card>
    </div>
  );
}

