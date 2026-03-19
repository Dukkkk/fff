export type IncomeFrequency = "weekly" | "biweekly" | "monthly" | "irregular";
export type TxnType = "income" | "expense";

export type UserCreate = {
  name: string;
  email?: string | null;
  income_frequency: IncomeFrequency;
  monthly_income_estimate: number;
  starting_balance: number;
};

export type UserOut = UserCreate & {
  id: string;
  created_at: string;
};

export type TransactionCreate = {
  user_id: string;
  date: string; // YYYY-MM-DD
  amount: number;
  type: TxnType;
  category: string;
  merchant?: string | null;
  note?: string | null;
  tags?: string[] | null;
};

export type TransactionUpdate = Partial<Omit<TransactionCreate, "user_id">>;

export type TransactionOut = TransactionCreate & {
  id: string;
  created_at: string;
};

export type ForecastOut = {
  user_id: string;
  as_of: string;
  current_balance: number;
  horizons_days: number[];
  curve: { date: string; projected_balance: number }[];
  days_until_broke: number | null;
  safety_status: "safe" | "tight" | "at_risk";
  summary: string;
};

export type InsightOut = {
  id: string;
  user_id: string;
  type: string;
  title: string;
  description: string;
  severity: "low" | "medium" | "high";
  created_at: string;
};

export type NudgeOut = {
  id: string;
  user_id: string;
  title: string;
  message: string;
  action_label?: string | null;
  created_at: string;
};

export type StressScoreOut = {
  user_id: string;
  score: number;
  label: "low" | "moderate" | "high";
  explanation: string;
  drivers: Record<string, number>;
};

export type GoalCreate = {
  user_id: string;
  title: string;
  target_amount: number;
  target_date: string;
  current_amount: number;
  category: string;
};

export type GoalOut = GoalCreate & {
  id: string;
  created_at: string;
};

