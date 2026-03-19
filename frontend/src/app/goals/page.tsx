"use client";

import { useEffect, useState } from "react";

import { Button, Card, CardTitle, Input, Muted, Select } from "@/components/ui";
import { api } from "@/lib/api";
import { getLocalUserId } from "@/lib/session";
import type { GoalOut } from "@/types/api";

const CATEGORIES = [
  "savings",
  "emergency fund",
  "tuition",
  "travel",
  "laptop",
  "debt payoff",
  "other"
];

function money(n: number) {
  return n.toLocaleString(undefined, { style: "currency", currency: "USD", maximumFractionDigits: 0 });
}

export default function GoalsPage() {
  const userId = getLocalUserId();
  const [goals, setGoals] = useState<GoalOut[]>([]);
  const [loading, setLoading] = useState(true);

  const [title, setTitle] = useState("Emergency Fund");
  const [targetAmount, setTargetAmount] = useState(2500);
  const [targetDate, setTargetDate] = useState(() => {
    const d = new Date();
    d.setDate(d.getDate() + 150);
    return d.toISOString().slice(0, 10);
  });
  const [currentAmount, setCurrentAmount] = useState(0);
  const [category, setCategory] = useState("savings");

  async function refresh() {
    if (!userId) return;
    setLoading(true);
    try {
      setGoals(await api.listGoals(userId));
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    refresh();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [userId]);

  async function addGoal() {
    if (!userId) return;
    await api.createGoal({
      user_id: userId,
      title,
      target_amount: targetAmount,
      target_date: targetDate,
      current_amount: currentAmount,
      category
    });
    await refresh();
  }

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
      <Card className="space-y-3">
        <CardTitle>Create a goal</CardTitle>
        <div className="space-y-1">
          <Muted>Title</Muted>
          <Input value={title} onChange={(e) => setTitle(e.target.value)} />
        </div>
        <div className="grid grid-cols-2 gap-3">
          <div className="space-y-1">
            <Muted>Target amount</Muted>
            <Input type="number" value={targetAmount} onChange={(e) => setTargetAmount(Number(e.target.value))} />
          </div>
          <div className="space-y-1">
            <Muted>Target date</Muted>
            <Input type="date" value={targetDate} onChange={(e) => setTargetDate(e.target.value)} />
          </div>
        </div>
        <div className="grid grid-cols-2 gap-3">
          <div className="space-y-1">
            <Muted>Current progress</Muted>
            <Input type="number" value={currentAmount} onChange={(e) => setCurrentAmount(Number(e.target.value))} />
          </div>
          <div className="space-y-1">
            <Muted>Category</Muted>
            <Select value={category} onChange={(e) => setCategory(e.target.value)}>
              {CATEGORIES.map((c) => (
                <option key={c} value={c}>
                  {c}
                </option>
              ))}
            </Select>
          </div>
        </div>
        <Button onClick={addGoal}>Add goal</Button>
      </Card>

      <Card className="space-y-3">
        <CardTitle>Your goals</CardTitle>
        {loading ? (
          <Muted>Loading…</Muted>
        ) : (
          <div className="space-y-2">
            {goals.map((g) => (
              <div key={g.id} className="rounded-2xl bg-white/60 p-3">
                <div className="flex items-center justify-between">
                  <div className="text-sm font-semibold">{g.title}</div>
                  <Muted>
                    {money(g.current_amount)} / {money(g.target_amount)}
                  </Muted>
                </div>
                <div className="mt-2 h-2 w-full overflow-hidden rounded-full bg-ink-100/60">
                  <div
                    className="h-full rounded-full bg-ink-700"
                    style={{ width: `${Math.min(100, (g.current_amount / g.target_amount) * 100)}%` }}
                  />
                </div>
                <Muted className="mt-2">Target date: {g.target_date}</Muted>
              </div>
            ))}
            {!goals.length && <Muted>No goals yet.</Muted>}
          </div>
        )}
      </Card>
    </div>
  );
}

