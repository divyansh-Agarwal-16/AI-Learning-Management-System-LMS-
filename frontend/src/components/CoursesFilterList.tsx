// This client component manages search and filter states for the courses directory view.
"use client";

import React, { useState, useMemo } from "react";
import Link from "next/link";

export interface Course {
  id: string;
  title: string;
  description: string;
  difficulty: "Beginner" | "Intermediate" | "Advanced";
  topic: string;
  duration: number; // in hours
  enrolled: boolean;
  progress?: number; // percentage
  thumbnail: string;
}

interface CoursesFilterListProps {
  initialCourses: Course[];
}

export function CoursesFilterList({ initialCourses }: CoursesFilterListProps) {
  const [search, setSearch] = useState("");
  const [difficulty, setDifficulty] = useState("All");
  const [topic, setTopic] = useState("All");
  const [duration, setDuration] = useState("All");

  // Filter calculations
  const filteredCourses = useMemo(() => {
    return initialCourses.filter((course) => {
      const matchesSearch = course.title.toLowerCase().includes(search.toLowerCase()) || 
                            course.description.toLowerCase().includes(search.toLowerCase());
      
      const matchesDifficulty = difficulty === "All" || course.difficulty === difficulty;
      const matchesTopic = topic === "All" || course.topic === topic;
      
      let matchesDuration = true;
      if (duration === "Short") matchesDuration = course.duration <= 4;
      else if (duration === "Medium") matchesDuration = course.duration > 4 && course.duration <= 7;
      else if (duration === "Long") matchesDuration = course.duration > 7;

      return matchesSearch && matchesDifficulty && matchesTopic && matchesDuration;
    });
  }, [initialCourses, search, difficulty, topic, duration]);

  // Extract unique topics for dropdown
  const uniqueTopics = useMemo(() => {
    const topics = initialCourses.map((c) => c.topic);
    return ["All", ...Array.from(new Set(topics))];
  }, [initialCourses]);

  return (
    <div className="space-y-8 font-sans">
      
      {/* Search and Filters Header */}
      <div className="bg-slate-900/40 border border-slate-900 p-6 rounded-xl space-y-4">
        <div className="flex flex-col md:flex-row gap-4">
          {/* Search Input */}
          <div className="flex-1">
            <label htmlFor="search" className="sr-only">Search courses</label>
            <input
              id="search"
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search by course title or keywords..."
              className="w-full px-4 py-2.5 border border-slate-800 rounded-lg bg-slate-950 placeholder-slate-600 text-sm text-white focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
            />
          </div>

          {/* Difficulty Dropdown */}
          <div className="w-full md:w-48">
            <select
              value={difficulty}
              onChange={(e) => setDifficulty(e.target.value)}
              className="w-full px-3 py-2.5 border border-slate-800 rounded-lg bg-slate-950 text-sm text-slate-300 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
            >
              <option value="All">All Difficulties</option>
              <option value="Beginner">Beginner</option>
              <option value="Intermediate">Intermediate</option>
              <option value="Advanced">Advanced</option>
            </select>
          </div>

          {/* Topic Dropdown */}
          <div className="w-full md:w-48">
            <select
              value={topic}
              onChange={(e) => setTopic(e.target.value)}
              className="w-full px-3 py-2.5 border border-slate-800 rounded-lg bg-slate-950 text-sm text-slate-300 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
            >
              <option value="All">All Topics</option>
              {uniqueTopics.filter(t => t !== "All").map((t) => (
                <option key={t} value={t}>{t}</option>
              ))}
            </select>
          </div>

          {/* Duration Dropdown */}
          <div className="w-full md:w-48">
            <select
              value={duration}
              onChange={(e) => setDuration(e.target.value)}
              className="w-full px-3 py-2.5 border border-slate-800 rounded-lg bg-slate-950 text-sm text-slate-300 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
            >
              <option value="All">All Durations</option>
              <option value="Short">Short (≤ 4 hrs)</option>
              <option value="Medium">Medium (4 - 7 hrs)</option>
              <option value="Long">Long (&gt; 7 hrs)</option>
            </select>
          </div>

        </div>
      </div>

      {/* Grid of Course Cards */}
      {filteredCourses.length > 0 ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
          {filteredCourses.map((course) => (
            <div 
              key={course.id} 
              className="flex flex-col justify-between p-6 bg-slate-900/40 border border-slate-900 hover:border-slate-800 rounded-2xl shadow hover:shadow-indigo-500/[0.01] hover:shadow-lg transition-all duration-300"
            >
              <div>
                {/* Thumbnail placeholder */}
                <div className="aspect-video w-full bg-slate-950 border border-slate-850 rounded-xl mb-4 flex items-center justify-center text-4xl overflow-hidden relative group">
                  <div className="absolute inset-0 bg-gradient-to-tr from-indigo-950/40 to-slate-900" />
                  <span className="relative z-10 transition-transform group-hover:scale-110 duration-300">{course.thumbnail}</span>
                </div>

                <div className="flex justify-between items-center gap-2 mb-2">
                  <span className="text-[10px] text-slate-500 font-semibold uppercase tracking-wider">{course.topic}</span>
                  <span className={`text-[9px] font-bold px-2 py-0.5 rounded border uppercase ${
                    course.difficulty === "Beginner" 
                      ? "text-emerald-400 bg-emerald-500/10 border-emerald-500/20"
                      : course.difficulty === "Intermediate"
                      ? "text-indigo-400 bg-indigo-500/10 border-indigo-500/20"
                      : "text-rose-400 bg-rose-500/10 border-rose-500/20"
                  }`}>
                    {course.difficulty}
                  </span>
                </div>

                <h3 className="text-lg font-bold text-slate-200 mb-2 hover:text-white line-clamp-1">{course.title}</h3>
                <p className="text-slate-400 text-xs leading-relaxed mb-6 line-clamp-3">{course.description}</p>
              </div>

              <div className="space-y-4">
                {course.enrolled && course.progress !== undefined && (
                  <div className="space-y-2">
                    <div className="flex justify-between text-[11px] text-slate-500">
                      <span>Progress</span>
                      <span className="font-semibold text-slate-300">{course.progress}%</span>
                    </div>
                    <div className="w-full bg-slate-800 h-1.5 rounded-full overflow-hidden">
                      <div className="bg-indigo-500 h-full rounded-full" style={{ width: `${course.progress}%` }} />
                    </div>
                  </div>
                )}
                
                <div className="flex justify-between items-center pt-2 border-t border-slate-900/60">
                  <span className="text-[10px] text-slate-500 font-semibold">{course.duration} hrs total content</span>
                  <Link 
                    href={`/course/${course.id}`} 
                    className="px-4 py-2 text-xs font-semibold bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg transition-colors shadow shadow-indigo-500/10"
                  >
                    {course.enrolled ? "Resume" : "Enroll"}
                  </Link>
                </div>
              </div>

            </div>
          ))}
        </div>
      ) : (
        <div className="text-center py-20 bg-slate-900/20 border border-slate-900 rounded-2xl">
          <div className="text-3xl mb-4">🔍</div>
          <h3 className="text-lg font-bold text-slate-200">No courses match your filters</h3>
          <p className="text-slate-400 text-sm mt-1">Try resetting the drop-downs or searching for different keywords.</p>
        </div>
      )}

    </div>
  );
}
