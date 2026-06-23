"use client";

import React from "react";
import { useSession } from "next-auth/react";
import { useQuery } from "@tanstack/react-query";
import { Navbar } from "@/components/Navbar";
import ProgressChart from "@/components/ProgressChart";
import Link from "next/link";
import { coursesApi, aiApi, progressApi } from "@/lib/api";

export default function DashboardPage() {
  const { data: session, status: sessionStatus } = useSession();

  // 1. Fetch Enrolled Courses
  const { 
    data: enrolledRes, 
    isLoading: coursesLoading, 
    error: coursesError 
  } = useQuery({
    queryKey: ["enrolledCourses"],
    queryFn: coursesApi.getEnrolledCourses,
    enabled: sessionStatus === "authenticated",
  });

  // 2. Fetch AI Study Plan
  const { 
    data: planRes, 
    isLoading: planLoading, 
    error: planError 
  } = useQuery({
    queryKey: ["studyPlan", (session?.user as any)?.id],
    queryFn: () => aiApi.getStudyPlan((session?.user as any)?.id || "me"),
    enabled: sessionStatus === "authenticated" && !!session?.user,
  });

  // 3. Fetch Weekly Progress Chart
  const { 
    data: weeklyRes, 
    isLoading: weeklyLoading, 
    error: weeklyError 
  } = useQuery({
    queryKey: ["weeklyProgress"],
    queryFn: progressApi.getWeeklyProgress,
    enabled: sessionStatus === "authenticated",
  });

  // 4. Fetch Recommendations
  const { 
    data: recsRes, 
    isLoading: recsLoading, 
    error: recsError 
  } = useQuery({
    queryKey: ["recommendations"],
    queryFn: aiApi.getRecommendations,
    enabled: sessionStatus === "authenticated",
  });

  const enrolledCourses = enrolledRes?.data || [];
  const studyPlanData = planRes?.data;
  const weeklyData = weeklyRes?.data || [];
  const recommendations = recsRes?.data?.recommendations || [];

  const fullName = session?.user?.name || session?.user?.email || "Scholar";
  const firstName = fullName.split(" ")[0];

  const stats = [
    { label: "Courses Enrolled", value: String(enrolledCourses.length), icon: "📚" },
    { 
      label: "Quizzes Completed", 
      value: String(enrolledCourses.reduce((acc, c) => acc + (c.progress && c.progress >= 100 ? 1 : 0), 0)), 
      icon: "🧠" 
    },
    { label: "Study Streak", value: "Active", icon: "🔥" },
  ];

  const isLoading = sessionStatus === "loading" || coursesLoading || planLoading || weeklyLoading || recsLoading;
  const isError = coursesError || planError || weeklyError || recsError;

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col font-sans">
      <Navbar />

      <main className="flex-grow max-w-7xl mx-auto px-6 py-10 w-full grid grid-cols-1 lg:grid-cols-3 gap-8">
        
        {/* Left 2 Columns: Greeting, Stats, Learning Paths, Chart */}
        <div className="lg:col-span-2 space-y-8">
          
          {/* Welcome Message */}
          <div className="p-8 bg-gradient-to-r from-indigo-950/40 via-purple-950/20 to-slate-900 border border-slate-900 rounded-2xl shadow-xl">
            <h1 className="text-3xl font-extrabold tracking-tight text-white mb-2">
              Welcome back, {firstName}!
            </h1>
            <p className="text-slate-400 text-sm max-w-xl leading-relaxed">
              Your autonomous AI agents have adjusted your syllabus based on your progress. Ready to tackle today&apos;s targets?
            </p>
          </div>

          {isError && (
            <div className="bg-red-900/20 border border-red-900/50 text-red-200 text-sm p-4 rounded-xl">
              Failed to load some dashboard sections. Please try refreshing.
            </div>
          )}

          {/* Quick Stats Grid */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-6">
            {stats.map((stat, idx) => (
              <div 
                key={idx} 
                className="p-6 bg-slate-900/40 border border-slate-900 rounded-xl flex items-center gap-4 hover:border-slate-800 transition-colors"
              >
                <div className="text-3xl bg-slate-950 p-3 rounded-lg border border-slate-900">{stat.icon}</div>
                <div>
                  <span className="text-xs text-slate-500 font-semibold uppercase tracking-wider">{stat.label}</span>
                  <div className="text-xl font-bold text-white mt-0.5">{stat.value}</div>
                </div>
              </div>
            ))}
          </div>

          {/* Continue Learning */}
          <section className="space-y-4">
            <h2 className="text-xl font-bold text-slate-200">Continue Learning</h2>
            {isLoading ? (
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
                {[1, 2].map((i) => (
                  <div key={i} className="p-6 bg-slate-900/20 border border-slate-900/50 rounded-xl h-40 animate-pulse" />
                ))}
              </div>
            ) : enrolledCourses.length > 0 ? (
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
                {enrolledCourses.map((course) => (
                  <div 
                    key={course.id} 
                    className="p-6 bg-slate-900/40 border border-slate-900 rounded-xl flex flex-col justify-between hover:border-slate-800 transition-colors"
                  >
                    <div>
                      <span className="text-[10px] text-slate-500 font-semibold uppercase">Active • {course.difficulty}</span>
                      <h3 className="font-bold text-slate-200 mt-1 mb-4 line-clamp-1">{course.title}</h3>
                    </div>
                    <div className="space-y-2">
                      <div className="flex justify-between text-xs text-slate-400">
                        <span>Progress</span>
                        <span className="font-semibold text-indigo-400">{course.progress || 0}%</span>
                      </div>
                      <div className="w-full bg-slate-800 h-1.5 rounded-full overflow-hidden">
                        <div className="bg-indigo-500 h-full rounded-full" style={{ width: `${course.progress || 0}%` }} />
                      </div>
                      <div className="pt-2 flex justify-end">
                        <Link 
                          href={`/course/${course.id}`} 
                          className="text-xs text-indigo-400 hover:text-indigo-300 font-semibold transition-colors"
                        >
                          Resume Lesson →
                        </Link>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="p-8 text-center bg-slate-900/20 border border-slate-900 rounded-xl text-slate-400 text-sm">
                You are not enrolled in any courses yet. Go to the{" "}
                <Link href="/courses" className="text-indigo-400 hover:underline">
                  Courses Catalog
                </Link>{" "}
                to get started!
              </div>
            )}
          </section>

          {/* Weekly Progress Chart */}
          <section className="p-6 bg-slate-900/40 border border-slate-900 rounded-xl space-y-4">
            <div>
              <h2 className="text-xl font-bold text-slate-200">Study Analytics</h2>
              <p className="text-xs text-slate-500 mt-1">Activity metrics showing study hours per day for this week.</p>
            </div>
            {isLoading ? (
              <div className="w-full h-64 bg-slate-900/20 animate-pulse rounded-lg border border-slate-900/50" />
            ) : (
              <ProgressChart data={weeklyData} />
            )}
          </section>

        </div>

        {/* Right 1 Column: Study Plan, Recommendations */}
        <div className="space-y-8">
          
          {/* Study Plan Section */}
          <section className="p-6 bg-slate-900/40 border border-slate-900 rounded-xl space-y-4">
            <div>
              <h2 className="text-lg font-bold text-slate-200">Your Study Plan</h2>
              <p className="text-xs text-slate-500 mt-1">Recommended milestones by your AI tutor for today.</p>
            </div>
            {isLoading ? (
              <div className="space-y-3">
                {[1, 2, 3].map((i) => (
                  <div key={i} className="p-3 bg-slate-900/20 border border-slate-900/50 rounded-lg h-10 animate-pulse" />
                ))}
              </div>
            ) : studyPlanData && studyPlanData.daily_plans && studyPlanData.daily_plans[0] ? (
              <div className="space-y-3">
                <div className="text-xs font-semibold text-slate-300 border-b border-slate-800/60 pb-1 mb-2">
                  Goal: {studyPlanData.week_goal}
                </div>
                {studyPlanData.daily_plans[0].tasks.map((taskItem, idx) => (
                  <div 
                    key={idx} 
                    className="p-3 bg-slate-950/60 border border-slate-800 hover:border-slate-700 rounded-lg flex items-start justify-between gap-3 text-xs leading-relaxed"
                  >
                    <div className="text-slate-300">
                      <div className="font-semibold text-indigo-400">{taskItem.time}</div>
                      <div className="text-[11px] text-slate-400 mt-0.5">{taskItem.activity}</div>
                      <div className="text-[10px] text-slate-500 italic mt-0.5">Resource: {taskItem.resource}</div>
                    </div>
                    <span className="text-[10px] text-indigo-400 bg-indigo-500/10 px-2 py-0.5 rounded-full whitespace-nowrap">
                      {taskItem.duration_mins} mins
                    </span>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-slate-400 text-xs text-center py-6">
                No study tasks generated. Complete quizzes to identify weak areas.
              </div>
            )}
          </section>

          {/* AI Recommendations */}
          <section className="space-y-4">
            <h2 className="text-lg font-bold text-slate-200">Recommended for You</h2>
            <div className="space-y-4">
              {isLoading ? (
                [1, 2].map((i) => (
                  <div key={i} className="p-5 bg-slate-900/20 border border-slate-900/50 rounded-xl h-36 animate-pulse" />
                ))
              ) : recommendations.length > 0 ? (
                recommendations.slice(0, 3).map((rec) => (
                  <div 
                    key={rec.id} 
                    className="p-5 bg-slate-900/40 border border-slate-900 hover:border-slate-800 rounded-xl transition-colors space-y-3"
                  >
                    <div className="flex justify-between items-start gap-2">
                      <h3 className="font-bold text-slate-200 text-sm leading-snug line-clamp-1">{rec.title}</h3>
                      <span className="text-[9px] font-semibold text-slate-400 bg-slate-800 px-2 py-0.5 rounded border border-slate-700 uppercase whitespace-nowrap">
                        {rec.difficulty}
                      </span>
                    </div>
                    <p className="text-slate-400 text-xs leading-relaxed line-clamp-2">
                      {rec.description}
                    </p>
                    <div className="flex justify-between items-center pt-1">
                      <span className="text-[10px] text-slate-500">{rec.duration} total content</span>
                      <Link 
                        href={`/course/${rec.id}`} 
                        className="text-xs text-indigo-400 hover:text-indigo-300 font-semibold transition-colors"
                      >
                        Enroll →
                      </Link>
                    </div>
                  </div>
                ))
              ) : (
                <div className="text-slate-500 text-xs text-center py-4">No customized recommendations.</div>
              )}
            </div>
          </section>

        </div>

      </main>
    </div>
  );
}
