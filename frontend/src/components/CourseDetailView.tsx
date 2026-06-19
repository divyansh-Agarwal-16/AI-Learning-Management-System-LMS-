// This client component coordinates course detail interactions, managing active lessons, content tabs, video playback, and chat panel displays.
"use client";

import React, { useState, useEffect } from "react";
import ReactPlayer from "react-player";
import { AIChatPanel } from "./AIChatPanel";

const Player = ReactPlayer as unknown as React.ComponentType<{ url?: string; width?: string; height?: string; controls?: boolean }>;

export interface Lesson {
  id: string;
  title: string;
  duration: string;
  completed: boolean;
  videoUrl: string;
  pdfUrl?: string;
}

export interface CourseDetail {
  id: string;
  title: string;
  description: string;
  lessons: Lesson[];
  overview: string;
  notes: string;
  quiz: {
    question: string;
    options: string[];
    answer: number;
  }[];
}

interface CourseDetailViewProps {
  course: CourseDetail;
}

export function CourseDetailView({ course }: CourseDetailViewProps) {
  const [currentLessonIdx, setCurrentLessonIdx] = useState(0);
  const [activeTab, setActiveTab] = useState("Overview");
  const [isClient, setIsClient] = useState(false);
  const [quizScore, setQuizScore] = useState<number | null>(null);
  const [selectedAnswers, setSelectedAnswers] = useState<Record<number, number>>({});

  // Ensure client-side mounting before loading ReactPlayer
  useEffect(() => {
    setIsClient(true);
  }, []);

  const currentLesson = course.lessons[currentLessonIdx] || course.lessons[0];

  const handleQuizSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    let score = 0;
    course.quiz.forEach((q, idx) => {
      if (selectedAnswers[idx] === q.answer) {
        score += 1;
      }
    });
    setQuizScore(score);
  };

  const handleOptionChange = (questionIdx: number, optionIdx: number) => {
    setSelectedAnswers({
      ...selectedAnswers,
      [questionIdx]: optionIdx,
    });
  };

  return (
    <div className="max-w-7xl mx-auto px-6 py-8 w-full grid grid-cols-1 lg:grid-cols-4 gap-8 font-sans text-slate-100">
      
      {/* 1. Left Sidebar: Lesson List */}
      <div className="lg:col-span-1 space-y-4">
        <div className="p-4 bg-slate-900/40 border border-slate-900 rounded-xl">
          <h3 className="font-bold text-slate-200 text-sm mb-4">Lessons</h3>
          <div className="space-y-2">
            {course.lessons.map((lesson, idx) => (
              <button
                key={lesson.id}
                onClick={() => {
                  setCurrentLessonIdx(idx);
                  setQuizScore(null);
                  setSelectedAnswers({});
                }}
                className={`w-full text-left p-3 rounded-lg flex items-center justify-between text-xs transition-colors border ${
                  idx === currentLessonIdx
                    ? "bg-indigo-500/10 border-indigo-500/50 text-indigo-400 font-semibold"
                    : "bg-slate-950/60 border-slate-900 hover:border-slate-800 text-slate-400 hover:text-slate-200"
                }`}
              >
                <div className="flex items-center gap-2 truncate">
                  <span className="text-slate-500 font-bold">{idx + 1}.</span>
                  <span className="truncate">{lesson.title}</span>
                </div>
                <div className="flex items-center gap-2 shrink-0">
                  <span className="text-[10px] text-slate-500">{lesson.duration}</span>
                  {lesson.completed ? (
                    <span className="text-emerald-500 font-bold">✓</span>
                  ) : (
                    <span className="w-1.5 h-1.5 rounded-full bg-slate-700" />
                  )}
                </div>
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* 2. Main content area: Video/PDF Player and Tabs */}
      <div className="lg:col-span-2 space-y-6">
        {/* Media Player Card */}
        <div className="p-4 bg-slate-900/40 border border-slate-900 rounded-2xl overflow-hidden shadow-lg">
          <div className="flex justify-between items-center mb-3">
            <span className="text-[10px] text-indigo-400 font-semibold uppercase tracking-wider">Lesson {currentLessonIdx + 1}</span>
            <h2 className="text-sm font-bold text-slate-200 truncate max-w-[280px]">{currentLesson.title}</h2>
          </div>
          
          <div className="aspect-video w-full bg-slate-950 rounded-xl overflow-hidden flex items-center justify-center border border-slate-850 relative">
            {isClient ? (
              currentLesson.videoUrl ? (
                <Player
                  url={currentLesson.videoUrl}
                  width="100%"
                  height="100%"
                  controls
                />
              ) : currentLesson.pdfUrl ? (
                // Safe PDF Embed Frame
                <iframe
                  src={currentLesson.pdfUrl}
                  title="PDF Reader"
                  className="w-full h-full border-0"
                />
              ) : (
                <div className="text-slate-500 text-xs">No media available.</div>
              )
            ) : (
              <div className="w-full h-full bg-slate-900 animate-pulse flex items-center justify-center text-xs text-slate-500">
                Initializing Player...
              </div>
            )}
          </div>
        </div>

        {/* Dynamic Tabs Block */}
        <div className="p-6 bg-slate-900/40 border border-slate-900 rounded-2xl space-y-6">
          <div className="flex border-b border-slate-900 gap-6">
            {["Overview", "Notes", "Quiz", "Discussion"].map((tab) => (
              <button
                key={tab}
                onClick={() => setActiveTab(tab)}
                className={`pb-3 text-sm font-semibold transition-all relative ${
                  activeTab === tab 
                    ? "text-indigo-400" 
                    : "text-slate-400 hover:text-slate-200"
                }`}
              >
                {tab}
                {activeTab === tab && (
                  <span className="absolute bottom-0 left-0 w-full h-0.5 bg-indigo-500 rounded-full" />
                )}
              </button>
            ))}
          </div>

          <div className="min-h-[160px] text-sm leading-relaxed text-slate-300">
            {activeTab === "Overview" && (
              <div className="space-y-2">
                <h4 className="font-bold text-slate-200 text-base">About this Lesson</h4>
                <p>{course.overview}</p>
                <div className="pt-2">
                  <h5 className="font-bold text-slate-300 text-xs uppercase tracking-wider mb-1">Course Description</h5>
                  <p className="text-xs text-slate-400">{course.description}</p>
                </div>
              </div>
            )}

            {activeTab === "Notes" && (
              <div className="space-y-4">
                <h4 className="font-bold text-slate-200 text-base">Key Notes & Cheat Sheet</h4>
                <div className="p-4 bg-slate-950 border border-slate-800 rounded-xl font-mono text-xs text-indigo-300 whitespace-pre-wrap leading-loose">
                  {course.notes}
                </div>
              </div>
            )}

            {activeTab === "Quiz" && (
              <form onSubmit={handleQuizSubmit} className="space-y-6">
                <h4 className="font-bold text-slate-200 text-base">Practice Quiz</h4>
                {course.quiz.map((item, qIdx) => (
                  <div key={qIdx} className="space-y-3 p-4 bg-slate-950/60 border border-slate-900 rounded-xl">
                    <p className="font-medium text-slate-200 text-xs">
                      {qIdx + 1}. {item.question}
                    </p>
                    <div className="grid grid-cols-1 gap-2">
                      {item.options.map((opt, oIdx) => (
                        <label
                          key={oIdx}
                          className={`flex items-center gap-3 p-3 rounded-lg border text-xs cursor-pointer transition-colors ${
                            selectedAnswers[qIdx] === oIdx
                              ? "border-indigo-500 bg-indigo-500/5 text-indigo-400"
                              : "border-slate-800 bg-slate-950 hover:bg-slate-900"
                          }`}
                        >
                          <input
                            type="radio"
                            name={`question-${qIdx}`}
                            checked={selectedAnswers[qIdx] === oIdx}
                            onChange={() => handleOptionChange(qIdx, oIdx)}
                            className="text-indigo-600 focus:ring-indigo-500 border-slate-800 bg-slate-950"
                          />
                          <span>{opt}</span>
                        </label>
                      ))}
                    </div>
                  </div>
                ))}

                {quizScore !== null ? (
                  <div className="p-4 bg-indigo-950/20 border border-indigo-950 rounded-xl flex items-center justify-between">
                    <div>
                      <div className="font-bold text-white text-sm">Quiz Results</div>
                      <div className="text-xs text-slate-400 mt-1">
                        You scored {quizScore} out of {course.quiz.length} correctly.
                      </div>
                    </div>
                    <span className="text-xl font-extrabold text-indigo-400">
                      {Math.round((quizScore / course.quiz.length) * 100)}%
                    </span>
                  </div>
                ) : (
                  <button
                    type="submit"
                    className="px-6 py-2 bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg text-xs font-semibold transition-colors shadow shadow-indigo-500/10"
                  >
                    Submit Answers
                  </button>
                )}
              </form>
            )}

            {activeTab === "Discussion" && (
              <div className="space-y-4">
                <h4 className="font-bold text-slate-200 text-base">Classroom Forum</h4>
                <div className="space-y-3">
                  <div className="p-4 bg-slate-950/60 border border-slate-900 rounded-xl">
                    <div className="flex justify-between items-center text-xs mb-1">
                      <span className="font-semibold text-slate-300">Alex Johnson</span>
                      <span className="text-slate-500">2 hours ago</span>
                    </div>
                    <p className="text-xs text-slate-400">Did anyone else get confused by the difference between RAG indexing and traditional vector DB queries? The tutor panel was super helpful for clarifying it.</p>
                  </div>
                </div>
                <div className="flex gap-2">
                  <input
                    type="text"
                    placeholder="Ask your class or post a question..."
                    className="flex-grow px-3 py-2 border border-slate-800 rounded-lg bg-slate-950 placeholder-slate-600 text-xs text-white focus:outline-none focus:ring-1 focus:ring-indigo-500"
                  />
                  <button
                    type="button"
                    className="px-4 py-2 bg-slate-900 hover:bg-slate-800 border border-slate-800 rounded-lg text-xs font-semibold transition-colors"
                  >
                    Post
                  </button>
                </div>
              </div>
            )}
          </div>

        </div>

      </div>

      {/* 3. Right Sidebar: AI Chat Panel */}
      <div className="lg:col-span-1 h-[550px]">
        <AIChatPanel courseId={course.id} />
      </div>

    </div>
  );
}
