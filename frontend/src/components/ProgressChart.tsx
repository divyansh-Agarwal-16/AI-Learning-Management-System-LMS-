// This client component renders the weekly study hours bar chart using Recharts.
"use client";

import React, { useEffect, useState } from "react";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";

interface ProgressChartProps {
  data?: { day: string; hours: number }[];
}

export default function ProgressChart({ data = [] }: ProgressChartProps) {
  const [mounted, setMounted] = useState(false);

  // Avoid hydration mismatch by waiting until client-side mount
  useEffect(() => {
    setMounted(true);
  }, []);

  if (!mounted) {
    return (
      <div className="w-full h-64 bg-slate-900/10 animate-pulse rounded-lg border border-slate-900/50 flex items-center justify-center text-xs text-slate-500">
        Loading analytics chart...
      </div>
    );
  }

  return (
    <div className="w-full h-64">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={data} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" vertical={false} />
          <XAxis dataKey="day" stroke="#64748b" fontSize={12} tickLine={false} axisLine={false} />
          <YAxis stroke="#64748b" fontSize={12} tickLine={false} axisLine={false} />
          <Tooltip
            contentStyle={{
              backgroundColor: "#0f172a",
              borderColor: "#334155",
              borderRadius: "8px",
              color: "#f8fafc",
            }}
            labelClassName="font-bold text-slate-200"
          />
          <Bar dataKey="hours" fill="#6366f1" radius={[4, 4, 0, 0]} maxBarSize={40} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
