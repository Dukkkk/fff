import type {
  ForecastOut,
  GoalCreate,
  GoalOut,
  InsightOut,
  NudgeOut,
  StressScoreOut,
  TransactionCreate,
  TransactionOut,
  TransactionUpdate,
  UserCreate,
  UserOut
} from "@/types/api";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE ?? "http://localhost:8000";

async function http<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: {
      "content-type": "application/json",
      ...(init?.headers ?? {})
    },
    cache: "no-store"
  });
  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(`API ${res.status}: ${text || res.statusText}`);
  }
  return (await res.json()) as T;
}

export const api = {
  createUser: (body: UserCreate) => http<UserOut>("/users", { method: "POST", body: JSON.stringify(body) }),
  getUser: (id: string) => http<UserOut>(`/users/${id}`),

  listTransactions: (userId: string, params?: { category?: string; type?: string }) => {
    const q = new URLSearchParams({ user_id: userId });
    if (params?.category) q.set("category", params.category);
    if (params?.type) q.set("type", params.type);
    return http<TransactionOut[]>(`/transactions?${q.toString()}`);
  },
  createTransaction: (body: TransactionCreate) => http<TransactionOut>("/transactions", { method: "POST", body: JSON.stringify(body) }),
  updateTransaction: (id: string, body: TransactionUpdate) => http<TransactionOut>(`/transactions/${id}`, { method: "PUT", body: JSON.stringify(body) }),
  deleteTransaction: (id: string) => http<{ ok: boolean }>(`/transactions/${id}`, { method: "DELETE" }),

  forecast: (userId: string) => http<ForecastOut>(`/forecast?user_id=${encodeURIComponent(userId)}&horizon_days=30`),
  insights: (userId: string) => http<InsightOut[]>(`/insights?user_id=${encodeURIComponent(userId)}&refresh=true`),
  stress: (userId: string) => http<StressScoreOut>(`/stress-score?user_id=${encodeURIComponent(userId)}`),
  nudges: (userId: string) => http<NudgeOut[]>(`/nudges?user_id=${encodeURIComponent(userId)}&refresh=true`),

  listGoals: (userId: string) => http<GoalOut[]>(`/goals?user_id=${encodeURIComponent(userId)}`),
  createGoal: (body: GoalCreate) => http<GoalOut>("/goals", { method: "POST", body: JSON.stringify(body) })
};

