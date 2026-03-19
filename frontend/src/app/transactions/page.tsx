"use client";

import { useEffect, useMemo, useState } from "react";

import { Button, Card, CardTitle, Input, Muted, Pill, Select } from "@/components/ui";
import { api } from "@/lib/api";
import { getLocalUserId } from "@/lib/session";
import type { TransactionOut, TxnType } from "@/types/api";

const CATEGORIES = [
  "food",
  "transport",
  "rent",
  "shopping",
  "entertainment",
  "bills",
  "savings",
  "health",
  "salary",
  "freelance",
  "other"
];

function money(n: number) {
  return n.toLocaleString(undefined, { style: "currency", currency: "USD", maximumFractionDigits: 2 });
}

export default function TransactionsPage() {
  const userId = getLocalUserId();
  const [txns, setTxns] = useState<TransactionOut[]>([]);
  const [loading, setLoading] = useState(true);
  const [filterType, setFilterType] = useState<string>("");
  const [filterCategory, setFilterCategory] = useState<string>("");

  // add form
  const [date, setDate] = useState(() => new Date().toISOString().slice(0, 10));
  const [amount, setAmount] = useState(12.5);
  const [type, setType] = useState<TxnType>("expense");
  const [category, setCategory] = useState("food");
  const [merchant, setMerchant] = useState("");
  const [note, setNote] = useState("");

  async function refresh() {
    if (!userId) return;
    setLoading(true);
    try {
      const list = await api.listTransactions(userId, {
        type: filterType || undefined,
        category: filterCategory || undefined
      });
      setTxns(list);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    refresh();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [userId, filterType, filterCategory]);

  const totals = useMemo(() => {
    const income = txns.filter((t) => t.type === "income").reduce((a, t) => a + t.amount, 0);
    const expense = txns.filter((t) => t.type === "expense").reduce((a, t) => a + t.amount, 0);
    return { income, expense };
  }, [txns]);

  async function addTxn() {
    if (!userId) return;
    await api.createTransaction({
      user_id: userId,
      date,
      amount,
      type,
      category,
      merchant: merchant || null,
      note: note || null,
      tags: null
    });
    setMerchant("");
    setNote("");
    await refresh();
  }

  async function del(id: string) {
    await api.deleteTransaction(id);
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
        <div className="flex items-baseline justify-between">
          <CardTitle>Transactions</CardTitle>
          <div className="flex items-center gap-2">
            <Pill tone="good">+{money(totals.income)}</Pill>
            <Pill tone="bad">-{money(totals.expense)}</Pill>
          </div>
        </div>
        <div className="grid grid-cols-2 gap-3">
          <div className="space-y-1">
            <Muted>Type</Muted>
            <Select value={filterType} onChange={(e) => setFilterType(e.target.value)}>
              <option value="">All</option>
              <option value="income">Income</option>
              <option value="expense">Expense</option>
            </Select>
          </div>
          <div className="space-y-1">
            <Muted>Category</Muted>
            <Select value={filterCategory} onChange={(e) => setFilterCategory(e.target.value)}>
              <option value="">All</option>
              {CATEGORIES.map((c) => (
                <option key={c} value={c}>
                  {c}
                </option>
              ))}
            </Select>
          </div>
        </div>
      </Card>

      <Card className="space-y-3">
        <CardTitle>Add transaction</CardTitle>
        <div className="grid grid-cols-2 gap-3">
          <div className="space-y-1">
            <Muted>Date</Muted>
            <Input type="date" value={date} onChange={(e) => setDate(e.target.value)} />
          </div>
          <div className="space-y-1">
            <Muted>Amount</Muted>
            <Input type="number" value={amount} onChange={(e) => setAmount(Number(e.target.value))} />
          </div>
        </div>
        <div className="grid grid-cols-2 gap-3">
          <div className="space-y-1">
            <Muted>Type</Muted>
            <Select value={type} onChange={(e) => setType(e.target.value as TxnType)}>
              <option value="expense">Expense</option>
              <option value="income">Income</option>
            </Select>
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
        <div className="space-y-1">
          <Muted>Merchant (optional)</Muted>
          <Input value={merchant} onChange={(e) => setMerchant(e.target.value)} placeholder="e.g., UberEats" />
        </div>
        <div className="space-y-1">
          <Muted>Note (optional)</Muted>
          <Input value={note} onChange={(e) => setNote(e.target.value)} placeholder="e.g., Dinner with friends" />
        </div>
        <Button onClick={addTxn}>Add</Button>
      </Card>

      <Card className="space-y-2">
        <CardTitle>Recent</CardTitle>
        {loading ? (
          <Muted>Loading…</Muted>
        ) : (
          <div className="space-y-2">
            {txns.slice(0, 30).map((t) => (
              <div key={t.id} className="flex items-center justify-between rounded-xl bg-white/60 px-3 py-2">
                <div>
                  <div className="text-sm font-semibold">{t.merchant || t.category}</div>
                  <Muted>
                    {t.date} • {t.type} • {t.category}
                  </Muted>
                </div>
                <div className="flex items-center gap-2">
                  <div className={t.type === "income" ? "text-emerald-700 font-semibold" : "text-ink-900 font-semibold"}>
                    {t.type === "income" ? "+" : "-"}
                    {money(t.amount)}
                  </div>
                  <button className="text-xs font-semibold text-ink-700/70 hover:text-ink-900" onClick={() => del(t.id)}>
                    Delete
                  </button>
                </div>
              </div>
            ))}
            {!txns.length && <Muted>No transactions yet.</Muted>}
          </div>
        )}
      </Card>
    </div>
  );
}

