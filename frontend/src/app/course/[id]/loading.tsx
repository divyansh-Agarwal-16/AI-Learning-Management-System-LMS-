// This loading component displays card skeletons while the detailed course content is fetching.
import React from "react";

export default function CourseDetailLoading() {
  return (
    <div className="min-h-screen bg-slate-950 p-6 space-y-8 animate-pulse font-sans">
      <div className="max-w-7xl mx-auto grid grid-cols-1 lg:grid-cols-4 gap-8">
        
        {/* Left Sidebar Skeleton */}
        <div className="lg:col-span-1 h-72 bg-slate-900 rounded-xl" />

        {/* Main Column Skeletons */}
        <div className="lg:col-span-2 space-y-6">
          <div className="aspect-video w-full bg-slate-900 rounded-2xl" />
          <div className="h-64 bg-slate-900 rounded-2xl" />
        </div>

        {/* Right Sidebar Skeleton */}
        <div className="lg:col-span-1 h-96 bg-slate-900 rounded-xl" />

      </div>
    </div>
  );
}
