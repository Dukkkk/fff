"use client";

import { useEffect, useState } from "react";

import { Card, CardTitle, Muted, Pill } from "@/components/ui";
import { api } from "@/lib/api";
import { getLocalUserId } from "@/lib/session";
import type { ForecastOut, InsightOut, StressScoreOut } from "@/types/api";

export default function InsightsPage() {
  const userId = getLocalUserId();
  const [insights, setInsights] = useState<InsightOut[]>([]);
  const [forecast, setForecast] = useState<ForecastOut | null>(null);
  const [stress, setStress] = useState<StressScoreOut | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    async function run() {
      if (!userId) return;
      setLoading(true);
      try {
        const [ins, fc, st] = await Promise.all([api.insights(userId), api.forecast(userId), api.stress(userId)]);
        if (cancelled) return;
        setInsights(ins);
        setForecast(fc);
        setStress(st);
      } finally {
        if (!cancelled) setLoading(false);
      }
    }
    run();
    return () => {
      cancelled = true;
    };
  }, [userId]);

  if (!userId) {
    return (
      <Card>
        <CardTitle>You're not onboarded</CardTitle>
        <Muted>Go to onboarding first.</Muted>
      </Card>
    );
  }

  return (
    <div className="space-y-4">
      <Card className="space-y-2">
        <CardTitle>Summary</CardTitle>
        <div className="flex flex-wrap items-center gap-2">
          {forecast && (
            <Pill tone={forecast.safety_status === "safe" ? "good" : forecast.safety_status === "tight" ? "warn" : "bad"}>
              {forecast.safety_status === "safe" ? "Safety: good" : forecast.safety_status === "tight" ? "Safety: tight" : "Safety: at risk"}
            </Pill>
          )}
          {stress && <Pill tone={stress.label === "low" ? "good" : stress.label === "moderate" ? "warn" : "bad"}>Stress: {stress.score}/100</Pill>}
        </div>
        <Muted>{forecast?.summary ?? "—"}</Muted>
      </Card>

      <Card className="space-y-3">
        <CardTitle>Behavioral patterns</CardTitle>
        {loading ? (
          <Muted>Loading…</Muted>
        ) : (
          <div className="space-y-2">
            {insights.map((i) => (
              <div key={i.id} className="rounded-2xl bg-white/60 p-3">
                <div className="flex items-start justify-between gap-3">
                  <div className="text-sm font-semibold leading-snug">{i.title}</div>
                  <Pill tone={i.severity === "high" ? "bad" : i.severity === "medium" ? "warn" : "neutral"}>{i.severity}</Pill>
                </div>
                <Muted>{i.description}</Muted>
              </div>
            ))}
            {!insights.length && <Muted>No insights yet — add a few transactions first.</Muted>}
          </div>
        )}
      </Card>
    </div>
  );
}

