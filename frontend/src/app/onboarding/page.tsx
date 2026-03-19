"use client";

import { useRouter } from "next/navigation";
import { useMemo, useState } from "react";

import { Button, Card, CardTitle, Input, Muted, Select } from "@/components/ui";
import { api } from "@/lib/api";
import { setLocalUser } from "@/lib/session";
import type { IncomeFrequency } from "@/types/api";

const GOALS = [
  { id: "emergency", label: "Emergency fund" },
  { id: "tuition", label: "Tuition" },
  { id: "travel", label: "Travel" },
  { id: "laptop", label: "New laptop" },
  { id: "debt", label: "Debt payoff" }
] as const;

export default function OnboardingPage() {
  const router = useRouter();
  const [name, setName] = useState("Ava");
  const [goal, setGoal] = useState<(typeof GOALS)[number]["id"]>("emergency");
  const [incomeFreq, setIncomeFreq] = useState<IncomeFrequency>("biweekly");
  const [income, setIncome] = useState(4200);
  const [startingBalance, setStartingBalance] = useState(900);
  const [loading, setLoading] = useState(false);
  const tagline = useMemo(() => {
    if (goal === "emergency") return "Build breathing room without overthinking it.";
    if (goal === "debt") return "Reduce stress by making progress feel inevitable.";
    return "Turn small habit shifts into real outcomes.";
  }, [goal]);

  async function start() {
    setLoading(true);
    try {
      const user = await api.createUser({
        name,
        income_frequency: incomeFreq,
        monthly_income_estimate: income,
        starting_balance: startingBalance
      });
      setLocalUser(user.id, user.name);
      router.push("/dashboard");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="space-y-4">
      <Card>
        <div className="flex items-start justify-between gap-3">
          <div>
            <div className="text-xs font-medium text-ink-700/70">Welcome</div>
            <div className="text-2xl font-semibold tracking-tight">Meet your money coach</div>
            <Muted>{tagline}</Muted>
          </div>
          <div className="rounded-2xl bg-ink-900 px-3 py-2 text-xs font-semibold text-white shadow-soft">MVP</div>
        </div>
      </Card>

      <Card className="space-y-3">
        <CardTitle>Your setup</CardTitle>
        <div className="space-y-1">
          <Muted>What should we call you?</Muted>
          <Input value={name} onChange={(e) => setName(e.target.value)} placeholder="Your name" />
        </div>
        <div className="space-y-1">
          <Muted>Primary goal</Muted>
          <Select value={goal} onChange={(e) => setGoal(e.target.value as any)}>
            {GOALS.map((g) => (
              <option key={g.id} value={g.id}>
                {g.label}
              </option>
            ))}
          </Select>
        </div>
        <div className="grid grid-cols-2 gap-3">
          <div className="space-y-1">
            <Muted>Income frequency</Muted>
            <Select value={incomeFreq} onChange={(e) => setIncomeFreq(e.target.value as IncomeFrequency)}>
              <option value="weekly">Weekly</option>
              <option value="biweekly">Biweekly</option>
              <option value="monthly">Monthly</option>
              <option value="irregular">Irregular</option>
            </Select>
          </div>
          <div className="space-y-1">
            <Muted>Monthly income estimate</Muted>
            <Input
              type="number"
              value={income}
              onChange={(e) => setIncome(Number(e.target.value))}
              placeholder="4200"
            />
          </div>
        </div>
        <div className="space-y-1">
          <Muted>Starting balance (optional)</Muted>
          <Input
            type="number"
            value={startingBalance}
            onChange={(e) => setStartingBalance(Number(e.target.value))}
          />
        </div>
        <Button onClick={start} disabled={loading || !name.trim()}>
          {loading ? "Starting…" : "Start"}
        </Button>
        <Muted>
          Tip: The backend also includes a realistic seeded demo dataset. Onboarding creates a new user; the seed creates a
          separate demo user.
        </Muted>
      </Card>
    </div>
  );
}

