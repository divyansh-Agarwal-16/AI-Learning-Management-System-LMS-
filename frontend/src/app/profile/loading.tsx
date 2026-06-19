// This loading component renders skeletal placeholders while the user profile details and stats compile.
import React from "react";

export default function ProfileLoading() {
  return (
    <div className="min-h-screen bg-slate-950 p-6 space-y-8 animate-pulse font-sans">
      <div className="max-w-7xl mx-auto grid grid-cols-1 lg:grid-cols-3 gap-8">
        
        {/* Left Card skeleton */}
        <div className="lg:col-span-1 space-y-6">
          <div className="p-6 bg-slate-900/45 border border-slate-900 rounded-2xl flex flex-col items-center space-y-4">
            <div className="w-24 h-24 rounded-full bg-slate-900" />
            <div className="h-6 bg-slate-900 rounded w-1/2" />
            <div className="h-4 bg-slate-900 rounded w-1/3" />
          </div>
          <div className="h-48 bg-slate-900/45 border border-slate-900 rounded-xl" />
        </div>

        {/* Right Card skeleton */}
        <div className="lg:col-span-2 p-8 bg-slate-900/45 border border-slate-900 rounded-2xl h-96" />

      </div>
    </div>
  );
}
