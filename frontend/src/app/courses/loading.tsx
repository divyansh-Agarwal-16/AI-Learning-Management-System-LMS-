// This loading component displays card skeletons while the courses catalog is loading.
import React from "react";

export default function CoursesLoading() {
  return (
    <div className="min-h-screen bg-slate-950 p-6 space-y-8 animate-pulse font-sans">
      <div className="max-w-7xl mx-auto space-y-8">
        
        {/* Title skeleton */}
        <div className="space-y-2">
          <div className="h-8 bg-slate-900 rounded-lg w-1/4" />
          <div className="h-4 bg-slate-900 rounded w-1/3" />
        </div>

        {/* Filter bar skeleton */}
        <div className="h-16 bg-slate-900 rounded-xl w-full" />

        {/* Cards grid skeleton */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
          {[...Array(6)].map((_, i) => (
            <div key={i} className="p-6 bg-slate-900/40 border border-slate-900 rounded-2xl space-y-4">
              <div className="aspect-video w-full bg-slate-900 rounded-xl" />
              <div className="flex justify-between items-center">
                <div className="h-4 bg-slate-900 rounded w-1/4" />
                <div className="h-4 bg-slate-900 rounded w-1/6" />
              </div>
              <div className="h-6 bg-slate-900 rounded w-2/3" />
              <div className="space-y-2">
                <div className="h-3 bg-slate-900 rounded w-full" />
                <div className="h-3 bg-slate-900 rounded w-5/6" />
              </div>
              <div className="pt-4 border-t border-slate-900 flex justify-between items-center">
                <div className="h-4 bg-slate-900 rounded w-1/3" />
                <div className="h-8 bg-slate-900 rounded-lg w-1/4" />
              </div>
            </div>
          ))}
        </div>

      </div>
    </div>
  );
}
