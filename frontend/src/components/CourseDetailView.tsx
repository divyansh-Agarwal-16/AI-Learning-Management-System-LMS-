// This client component coordinates course detail interactions, managing active lessons, content tabs, video playback, and chat panel displays.
"use client";

import React, { useState, useEffect } from "react";
import ReactPlayer from "react-player";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { AIChatPanel } from "./AIChatPanel";
import { ConceptMap } from "./ConceptMap";
import { coursesApi, progressApi, quizzesApi } from "@/lib/api";

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
  const [externalPrompt, setExternalPrompt] = useState<{ text: string; timestamp: number } | null>(null);

  const queryClient = useQueryClient();

  // Query Course details dynamically with user-specific progress preloaded
  const { data: courseData } = useQuery<any>({
    queryKey: ["course", course.id],
    queryFn: async () => {
      const res = await coursesApi.getCourse(course.id);
      return res.data;
    },
    initialData: course as any,
  });

  // Query Course Quiz details
  const { data: quizRes } = useQuery({
    queryKey: ["courseQuiz", course.id],
    queryFn: () => quizzesApi.getQuizByCourse(course.id),
    enabled: !!course.id,
  });
  const quiz = quizRes?.data;

  // Mutation for updating lesson completion optimistically
  const toggleProgressMutation = useMutation({
    mutationFn: ({ lessonId, completed }: { lessonId: string; completed: boolean }) =>
      progressApi.updateProgress(lessonId, completed, 0),
    onMutate: async ({ lessonId, completed }) => {
      await queryClient.cancelQueries({ queryKey: ["course", course.id] });
      const previousCourse = queryClient.getQueryData<any>(["course", course.id]);

      if (previousCourse) {
        queryClient.setQueryData(["course", course.id], {
          ...previousCourse,
          lessons: previousCourse.lessons.map((l: any) =>
            l.id === lessonId ? { ...l, completed } : l
          ),
        });
      }

      return { previousCourse };
    },
    onError: (err, variables, context) => {
      if (context?.previousCourse) {
        queryClient.setQueryData(["course", course.id], context.previousCourse);
      }
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ["course", course.id] });
      queryClient.invalidateQueries({ queryKey: ["weeklyProgress"] });
      queryClient.invalidateQueries({ queryKey: ["enrolledCourses"] });
    },
  });

  // Ensure client-side mounting before loading ReactPlayer
  useEffect(() => {
    setIsClient(true);
  }, []);

  const currentLesson = courseData.lessons?.[currentLessonIdx] || courseData.lessons?.[0] || course.lessons[0];

  const handleToggleComplete = (lessonId: string, completed: boolean) => {
    toggleProgressMutation.mutate({ lessonId, completed });
  };

  return (
    <div className="max-w-7xl mx-auto px-6 py-8 w-full grid grid-cols-1 lg:grid-cols-4 gap-8 font-sans text-slate-100">
      
      {/* 1. Left Sidebar: Lesson List */}
      <div className="lg:col-span-1 space-y-4">
        <div className="p-4 bg-slate-900/40 border border-slate-900 rounded-xl">
          <h3 className="font-bold text-slate-200 text-sm mb-4">Lessons</h3>
          <div className="space-y-2">
            {courseData.lessons?.map((lesson: any, idx: number) => (
              <button
                key={lesson.id}
                onClick={() => {
                  setCurrentLessonIdx(idx);
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
                <div className="flex items-center gap-3 shrink-0">
                  <span className="text-[10px] text-slate-500">{lesson.duration}</span>
                  <button
                    type="button"
                    onClick={(e) => {
                      e.stopPropagation();
                      handleToggleComplete(lesson.id, !lesson.completed);
                    }}
                    className={`w-4 h-4 rounded border flex items-center justify-center transition-all ${
                      lesson.completed
                        ? "bg-emerald-500 border-emerald-500 text-white font-bold"
                        : "border-slate-700 hover:border-slate-500 bg-slate-950 text-transparent"
                    }`}
                  >
                    <span className="text-[9px]">✓</span>
                  </button>
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
          <div className="flex border-b border-slate-900 gap-6 overflow-x-auto pb-1">
            {["Overview", "Notes", "Concept Map", "Quiz", "Discussion"].map((tab) => (
              <button
                key={tab}
                onClick={() => setActiveTab(tab)}
                className={`pb-3 text-sm font-semibold transition-all relative whitespace-nowrap ${
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
                <p>{courseData.description || course.overview}</p>
                <div className="pt-2">
                  <h5 className="font-bold text-slate-300 text-xs uppercase tracking-wider mb-1">Course Description</h5>
                  <p className="text-xs text-slate-400">{courseData.description || course.description}</p>
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

            {activeTab === "Concept Map" && (
              <ConceptMap
                topic={courseData.title}
                onExplainConcept={(conceptLabel) => {
                  setExternalPrompt({
                    text: `Explain the concept: ${conceptLabel}`,
                    timestamp: Date.now(),
                  });
                }}
              />
            )}

            {activeTab === "Quiz" && (
              <div className="space-y-6 text-center py-8 bg-slate-950/60 border border-slate-900 rounded-xl p-6">
                <span className="text-4xl block">📝</span>
                <h4 className="font-bold text-slate-200 text-base">Course Practice Quiz</h4>
                <p className="text-xs text-slate-400 max-w-sm mx-auto">
                  Evaluate your learning retention with this module&apos;s custom questions graded by your personal AI Tutor.
                </p>
                {quiz ? (
                  <div className="pt-4">
                    <a
                      href={`/quiz/${quiz.id}`}
                      className="inline-block px-6 py-2.5 bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg text-xs font-semibold transition-colors shadow shadow-indigo-500/10"
                    >
                      Start Practice Quiz
                    </a>
                  </div>
                ) : (
                  <p className="text-xs text-slate-500 pt-2">No practice quiz available for this course yet.</p>
                )}
              </div>
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
        <AIChatPanel courseId={course.id} externalPrompt={externalPrompt} />
      </div>

    </div>
  );
}
