"use client";

import { ResponsiveContainer, AreaChart, Area, XAxis, YAxis, Tooltip } from "recharts";

export function BalanceCurve({ points }: { points: { date: string; projected_balance: number }[] }) {
  return (
    <div className="h-44 w-full">
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart data={points} margin={{ top: 8, right: 12, left: -8, bottom: 0 }}>
          <defs>
            <linearGradient id="balFill" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#38477d" stopOpacity={0.28} />
              <stop offset="100%" stopColor="#38477d" stopOpacity={0} />
            </linearGradient>
          </defs>
          <XAxis
            dataKey="date"
            tick={{ fontSize: 10, fill: "rgba(40,52,87,0.55)" }}
            tickLine={false}
            axisLine={false}
            interval={6}
          />
          <YAxis
            tick={{ fontSize: 10, fill: "rgba(40,52,87,0.55)" }}
            tickLine={false}
            axisLine={false}
            width={40}
          />
          <Tooltip
            contentStyle={{
              borderRadius: 12,
              border: "1px solid rgba(215,222,239,0.9)",
              background: "rgba(255,255,255,0.9)",
              boxShadow: "0 10px 24px rgba(12,18,38,0.10)"
            }}
            formatter={(v: any) => [`$${Number(v).toFixed(0)}`, "Projected"]}
            labelFormatter={(l) => `Date: ${l}`}
          />
          <Area type="monotone" dataKey="projected_balance" stroke="#38477d" strokeWidth={2} fill="url(#balFill)" />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}

