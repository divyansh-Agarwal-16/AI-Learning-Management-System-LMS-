// This component implements the error fallback page for profile editing, offering recovery triggers for details reloading.
"use client";

import React, { useEffect } from "react";

export default function ProfileError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    console.error("Profile view error boundary caught:", error);
  }, [error]);

  return (
    <div className="min-h-screen bg-slate-950 flex flex-col items-center justify-center p-6 text-slate-100 font-sans">
      <div className="max-w-md w-full text-center space-y-6 bg-slate-900/60 border border-slate-900 p-8 rounded-2xl shadow-xl">
        <div className="text-4xl">⚠️</div>
        <h2 className="text-2xl font-bold text-white">Profile Loading Failed</h2>
        <p className="text-slate-400 text-sm leading-relaxed">
          The user parameters could not be fetched from session stores. Please try updating your session.
        </p>
        <div className="pt-2 flex justify-center gap-4">
          <button
            onClick={() => reset()}
            className="px-6 py-2 bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg text-sm font-semibold transition-colors"
          >
            Try Again
          </button>
          <a
            href="/dashboard"
            className="px-6 py-2 border border-slate-800 hover:bg-slate-800 text-slate-300 hover:text-white rounded-lg text-sm font-semibold transition-colors"
          >
            Dashboard
          </a>
        </div>
      </div>
    </div>
  );
}
