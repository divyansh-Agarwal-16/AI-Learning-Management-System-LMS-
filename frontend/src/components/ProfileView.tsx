// This client component displays the user's profile information, tracks study statistics, and processes profile updates.
"use client";

import React, { useState } from "react";

interface ProfileUser {
  name?: string | null;
  email?: string | null;
  image?: string | null;
}

interface ProfileViewProps {
  user: ProfileUser;
}

export function ProfileView({ user }: ProfileViewProps) {
  const [formData, setFormData] = useState({
    name: user.name || "Demo User",
    email: user.email || "user@example.com",
    newPassword: "",
    confirmPassword: "",
  });
  
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const stats = [
    { label: "Total Study Hours", value: "19.5 hrs", icon: "⏱️" },
    { label: "Courses Completed", value: "1", icon: "🏆" },
    { label: "Average Quiz Score", value: "85%", icon: "🎯" },
  ];

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value,
    });
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setMessage("");
    setError("");

    if (!formData.name || !formData.email) {
      setError("Name and Email are required.");
      return;
    }

    if (formData.newPassword && formData.newPassword !== formData.confirmPassword) {
      setError("Passwords do not match.");
      return;
    }

    setLoading(true);

    try {
      // Mock profile update request. In a real app, this posts to FastAPI backend.
      await new Promise((resolve) => setTimeout(resolve, 800));
      setMessage("Profile details updated successfully.");
      setFormData({
        ...formData,
        newPassword: "",
        confirmPassword: "",
      });
    } catch {
      setError("An error occurred. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-7xl mx-auto px-6 py-8 w-full grid grid-cols-1 lg:grid-cols-3 gap-8 font-sans text-slate-100">
      
      {/* 1. Left: Profile summary card */}
      <div className="lg:col-span-1 space-y-6">
        <div className="p-6 bg-slate-900/40 border border-slate-900 rounded-2xl flex flex-col items-center text-center space-y-4">
          <div className="w-24 h-24 rounded-full bg-gradient-to-tr from-indigo-500 via-purple-500 to-indigo-500 flex items-center justify-center text-3xl font-extrabold shadow shadow-indigo-500/20">
            {formData.name.charAt(0).toUpperCase()}
          </div>
          <div>
            <h2 className="text-xl font-bold text-white">{formData.name}</h2>
            <p className="text-xs text-slate-500 mt-1">{formData.email}</p>
          </div>
          <div className="pt-2 border-t border-slate-900 w-full text-xs text-slate-400">
            <span>Student Member since June 2026</span>
          </div>
        </div>

        {/* Study Statistics Cards */}
        <div className="space-y-4">
          <h3 className="font-bold text-slate-200 text-sm">Learning Metrics</h3>
          <div className="grid grid-cols-1 gap-4">
            {stats.map((stat, idx) => (
              <div 
                key={idx} 
                className="p-4 bg-slate-900/40 border border-slate-900 rounded-xl flex items-center gap-4"
              >
                <div className="text-2xl bg-slate-950 p-2.5 rounded-lg border border-slate-900">{stat.icon}</div>
                <div>
                  <span className="text-[10px] text-slate-500 font-semibold uppercase tracking-wider">{stat.label}</span>
                  <div className="text-sm font-bold text-white mt-0.5">{stat.value}</div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* 2. Right 2 Columns: Edit form */}
      <div className="lg:col-span-2 space-y-6">
        <div className="p-8 bg-slate-900/40 border border-slate-900 rounded-2xl space-y-6 shadow-xl">
          <div>
            <h3 className="text-xl font-bold text-slate-200">Account Preferences</h3>
            <p className="text-xs text-slate-500 mt-1">Modify your profile details and update security settings.</p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-6">
            {error && (
              <div className="bg-red-900/20 border border-red-900/50 text-red-200 text-sm p-3 rounded-lg">
                {error}
              </div>
            )}
            
            {message && (
              <div className="bg-emerald-900/20 border border-emerald-900/50 text-emerald-200 text-sm p-3 rounded-lg">
                {message}
              </div>
            )}

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
              <div>
                <label htmlFor="name" className="block text-xs font-semibold text-slate-300">
                  Full Name
                </label>
                <input
                  id="name"
                  name="name"
                  type="text"
                  required
                  value={formData.name}
                  onChange={handleChange}
                  className="mt-1.5 appearance-none block w-full px-3.5 py-2 border border-slate-800 rounded-lg bg-slate-950 placeholder-slate-650 text-white focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent text-xs"
                />
              </div>

              <div>
                <label htmlFor="email" className="block text-xs font-semibold text-slate-300">
                  Email Address
                </label>
                <input
                  id="email"
                  name="email"
                  type="email"
                  required
                  value={formData.email}
                  onChange={handleChange}
                  className="mt-1.5 appearance-none block w-full px-3.5 py-2 border border-slate-800 rounded-lg bg-slate-950 placeholder-slate-650 text-white focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent text-xs"
                />
              </div>
            </div>

            <div className="border-t border-slate-900 pt-6 space-y-6">
              <div>
                <h4 className="font-bold text-slate-200 text-sm">Update Password</h4>
                <p className="text-[11px] text-slate-500 mt-0.5">Leave blank if you do not want to alter your password.</p>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
                <div>
                  <label htmlFor="newPassword" className="block text-xs font-semibold text-slate-300">
                    New Password
                  </label>
                  <input
                    id="newPassword"
                    name="newPassword"
                    type="password"
                    value={formData.newPassword}
                    onChange={handleChange}
                    placeholder="••••••••"
                    className="mt-1.5 appearance-none block w-full px-3.5 py-2 border border-slate-800 rounded-lg bg-slate-950 placeholder-slate-650 text-white focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent text-xs"
                  />
                </div>

                <div>
                  <label htmlFor="confirmPassword" className="block text-xs font-semibold text-slate-300">
                    Confirm Password
                  </label>
                  <input
                    id="confirmPassword"
                    name="confirmPassword"
                    type="password"
                    value={formData.confirmPassword}
                    onChange={handleChange}
                    placeholder="••••••••"
                    className="mt-1.5 appearance-none block w-full px-3.5 py-2 border border-slate-800 rounded-lg bg-slate-950 placeholder-slate-650 text-white focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent text-xs"
                  />
                </div>
              </div>
            </div>

            <div className="flex justify-end pt-2">
              <button
                type="submit"
                disabled={loading}
                className="px-6 py-2.5 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white rounded-lg text-xs font-semibold transition-colors shadow shadow-indigo-500/10"
              >
                {loading ? "Saving..." : "Save Preferences"}
              </button>
            </div>
          </form>

        </div>
      </div>

    </div>
  );
}
