// This loading component displays skeletal placeholders while the dashboard metrics and widgets fetch and compile.
import React from "react";

export default function DashboardLoading() {
  return (
    <div className="min-h-screen bg-slate-950 p-6 space-y-8 animate-pulse font-sans">
      <div className="max-w-7xl mx-auto space-y-8">
        
        {/* Header Skeleton */}
        <div className="h-10 bg-slate-900 rounded-lg w-1/4" />

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Main Panel Skeletons */}
          <div className="lg:col-span-2 space-y-8">
            <div className="h-40 bg-slate-900 rounded-2xl w-full" />
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-6">
              <div className="h-24 bg-slate-900 rounded-xl" />
              <div className="h-24 bg-slate-900 rounded-xl" />
              <div className="h-24 bg-slate-900 rounded-xl" />
            </div>
            <div className="h-64 bg-slate-900 rounded-xl w-full" />
          </div>

          {/* Sidebar Skeletons */}
          <div className="space-y-8">
            <div className="h-72 bg-slate-900 rounded-xl w-full" />
            <div className="h-72 bg-slate-900 rounded-xl w-full" />
          </div>
        </div>

      </div>
    </div>
  );
}
