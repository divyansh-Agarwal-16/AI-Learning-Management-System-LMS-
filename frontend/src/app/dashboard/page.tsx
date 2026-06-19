// This server component fetches user session information and coordinates sub-sections such as statistics, ongoing courses, and study plans.
import React from "react";
import { getServerSession } from "next-auth/next";
import { authOptions } from "@/lib/auth";
import { Navbar } from "@/components/Navbar";
import ProgressChart from "@/components/ProgressChart";
import Link from "next/link";

export default async function DashboardPage() {
  const session = await getServerSession(authOptions);
  
  // Extract user's first name for personalization
  const fullName = session?.user?.name || "Scholar";
  const firstName = fullName.split(" ")[0];

  const stats = [
    { label: "Courses Enrolled", value: "3", icon: "📚" },
    { label: "Quizzes Completed", value: "8", icon: "🧠" },
    { label: "Study Streak", value: "5 Days", icon: "🔥" },
  ];

  const continueLearning = [
    {
      id: "python-101",
      title: "Python Programming Basics",
      progress: 68,
      lastActive: "Yesterday",
    },
    {
      id: "data-science-intro",
      title: "Introduction to Data Science",
      progress: 35,
      lastActive: "3 days ago",
    },
  ];

  const recommendations = [
    {
      id: "rag-pipelines",
      title: "Building RAG Pipelines with LlamaIndex",
      description: "Learn index construction, vector retrieval models, and contextual LLM generation.",
      duration: "4.5 hrs",
      difficulty: "Intermediate",
    },
    {
      id: "langgraph-agents",
      title: "Multi-Agent Coordination with LangGraph",
      description: "Master state graphs, cognitive agent routing loops, and human-in-the-loop triggers.",
      duration: "6.0 hrs",
      difficulty: "Advanced",
    },
    {
      id: "postgres-deepdive",
      title: "PostgreSQL Database Administration",
      description: "Optimize queries, scale database nodes, and configure custom volumes in Docker.",
      duration: "8.0 hrs",
      difficulty: "Beginner",
    },
  ];

  const studyPlan = [
    { task: "Complete the quiz on 'FastAPI Dependency Injection'", duration: "15 mins" },
    { task: "Watch the 'LlamaIndex Storage Context' lesson video", duration: "20 mins" },
    { task: "Ask the AI Tutor to clarify 'LangGraph Cycles and Recursion'", duration: "10 mins" },
  ];

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
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
              {continueLearning.map((course) => (
                <div 
                  key={course.id} 
                  className="p-6 bg-slate-900/40 border border-slate-900 rounded-xl flex flex-col justify-between hover:border-slate-800 transition-colors"
                >
                  <div>
                    <span className="text-[10px] text-slate-500 font-semibold uppercase">Active • {course.lastActive}</span>
                    <h3 className="font-bold text-slate-200 mt-1 mb-4">{course.title}</h3>
                  </div>
                  <div className="space-y-2">
                    <div className="flex justify-between text-xs text-slate-400">
                      <span>Progress</span>
                      <span className="font-semibold text-indigo-400">{course.progress}%</span>
                    </div>
                    <div className="w-full bg-slate-800 h-1.5 rounded-full overflow-hidden">
                      <div className="bg-indigo-500 h-full rounded-full" style={{ width: `${course.progress}%` }} />
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
          </section>

          {/* Weekly Progress Chart */}
          <section className="p-6 bg-slate-900/40 border border-slate-900 rounded-xl space-y-4">
            <div>
              <h2 className="text-xl font-bold text-slate-200">Study Analytics</h2>
              <p className="text-xs text-slate-500 mt-1">Activity metrics showing study hours per day for this week.</p>
            </div>
            <ProgressChart />
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
            <div className="space-y-3">
              {studyPlan.map((item, idx) => (
                <div 
                  key={idx} 
                  className="p-3 bg-slate-950/60 border border-slate-800 hover:border-slate-700 rounded-lg flex items-start justify-between gap-3 text-xs leading-relaxed"
                >
                  <div className="text-slate-300">{item.task}</div>
                  <span className="text-[10px] text-indigo-400 bg-indigo-500/10 px-2 py-0.5 rounded-full whitespace-nowrap">{item.duration}</span>
                </div>
              ))}
            </div>
          </section>

          {/* AI Recommendations */}
          <section className="space-y-4">
            <h2 className="text-lg font-bold text-slate-200">Recommended for You</h2>
            <div className="space-y-4">
              {recommendations.map((rec) => (
                <div 
                  key={rec.id} 
                  className="p-5 bg-slate-900/40 border border-slate-900 hover:border-slate-800 rounded-xl transition-colors space-y-3"
                >
                  <div className="flex justify-between items-start gap-2">
                    <h3 className="font-bold text-slate-200 text-sm leading-snug">{rec.title}</h3>
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
              ))}
            </div>
          </section>

        </div>

      </main>
    </div>
  );
}
