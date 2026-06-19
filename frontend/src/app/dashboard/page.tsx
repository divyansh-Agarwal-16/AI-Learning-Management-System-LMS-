// This client component displays the dashboard layout, welcoming the authenticated user and providing log-out capabilities.
"use client";

import React from "react";
import { useSession, signOut } from "next-auth/react";
import Link from "next/link";

export default function DashboardPage() {
  const { data: session, status } = useSession();

  const handleSignOut = () => {
    signOut({ callbackUrl: "/" });
  };

  const mockOverview = [
    { label: "Active Courses", value: "2", color: "text-indigo-400" },
    { label: "Completed Lessons", value: "14", color: "text-emerald-400" },
    { label: "Study Time This Week", value: "6.5 hrs", color: "text-amber-400" },
    { label: "AI Advisor Interaction Score", value: "92%", color: "text-pink-400" },
  ];

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col justify-between font-sans">
      
      {/* Top Header */}
      <header className="border-b border-slate-900 bg-slate-950/80 backdrop-blur sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-6 py-4 flex justify-between items-center">
          <Link href="/" className="text-xl font-bold bg-gradient-to-r from-indigo-400 via-purple-400 to-indigo-400 bg-clip-text text-transparent">
            ai-lms
          </Link>
          <div className="flex items-center gap-4">
            <span className="text-sm text-slate-400 hidden sm:inline-block">
              {status === "authenticated" ? session.user?.email : "guest@example.com"}
            </span>
            <button
              onClick={handleSignOut}
              className="px-4 py-2 text-xs font-semibold bg-slate-900 hover:bg-slate-800 border border-slate-800 rounded-lg text-slate-300 hover:text-white transition-colors"
            >
              Log Out
            </button>
          </div>
        </div>
      </header>

      {/* Main Content Area */}
      <main className="flex-1 max-w-7xl mx-auto px-6 py-12 w-full">
        {/* Welcome Section */}
        <div className="mb-10 p-8 bg-gradient-to-r from-indigo-950/40 via-purple-950/30 to-slate-900 border border-indigo-950 rounded-2xl shadow-xl">
          <h1 className="text-3xl font-extrabold tracking-tight text-white mb-2">
            Welcome to your Dashboard, {session?.user?.name || "Scholar"}!
          </h1>
          <p className="text-slate-400 max-w-xl leading-relaxed text-sm">
            Your personalized curriculum has been generated. Ask the AI Tutor a question in your courses page or resume where you left off.
          </p>
        </div>

        {/* Overview Stats */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-12">
          {mockOverview.map((item, idx) => (
            <div key={idx} className="p-6 bg-slate-900/40 border border-slate-900 rounded-xl hover:border-slate-800 transition-colors">
              <span className="text-xs text-slate-500 font-semibold uppercase tracking-wider">{item.label}</span>
              <div className={`text-2xl font-bold mt-2 ${item.color}`}>{item.value}</div>
            </div>
          ))}
        </div>

        {/* Content Widgets */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          
          {/* Recommendations Card */}
          <div className="lg:col-span-2 p-6 bg-slate-900/40 border border-slate-900 rounded-xl space-y-4">
            <h3 className="text-lg font-bold text-slate-200">Recommended Next Steps</h3>
            <div className="space-y-3">
              <div className="p-4 bg-slate-950/80 border border-slate-800 rounded-lg flex items-center justify-between group cursor-pointer hover:border-indigo-500/50 transition-colors">
                <div>
                  <h4 className="font-semibold text-slate-200 group-hover:text-white">Python Fundamentals: Functions</h4>
                  <p className="text-xs text-slate-500 mt-1">Expected time: 25 mins • Next up in: Programming path</p>
                </div>
                <span className="text-indigo-400 group-hover:translate-x-1 transition-transform">→</span>
              </div>
              <div className="p-4 bg-slate-950/80 border border-slate-800 rounded-lg flex items-center justify-between group cursor-pointer hover:border-indigo-500/50 transition-colors">
                <div>
                  <h4 className="font-semibold text-slate-200 group-hover:text-white">Topic Quiz: Variables & Types</h4>
                  <p className="text-xs text-slate-500 mt-1">4 questions • Personalized mock review</p>
                </div>
                <span className="text-indigo-400 group-hover:translate-x-1 transition-transform">→</span>
              </div>
            </div>
          </div>

          {/* AI Tutor Chat Widget */}
          <div className="p-6 bg-slate-900/40 border border-slate-900 rounded-xl flex flex-col justify-between min-h-[300px]">
            <div>
              <h3 className="text-lg font-bold text-slate-200">Quick AI Assist</h3>
              <p className="text-xs text-slate-500 mt-1">Ask the autonomous tutor anything related to your current path.</p>
              <div className="mt-4 p-3 bg-slate-950/60 border border-slate-800 rounded-lg text-xs text-slate-400 italic">
                &quot;What specific question do you want to learn about today? I can pull from our vector-store documents.&quot;
              </div>
            </div>
            <div className="mt-4">
              <input
                type="text"
                placeholder="Type your question..."
                className="w-full px-3 py-2 border border-slate-800 rounded-lg bg-slate-950 placeholder-slate-600 text-xs text-white focus:outline-none focus:ring-1 focus:ring-indigo-500 focus:border-transparent"
              />
            </div>
          </div>

        </div>
      </main>

      {/* Footer */}
      <footer className="border-t border-slate-900 bg-slate-950 py-6 text-center text-xs text-slate-600 mt-12">
        <div className="max-w-7xl mx-auto px-6">
          <p>© {new Date().getFullYear()} AI Learning Management System. All rights reserved.</p>
        </div>
      </footer>
    </div>
  );
}
