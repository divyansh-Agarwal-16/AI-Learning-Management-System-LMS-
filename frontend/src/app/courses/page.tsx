// This server component fetches the directory of courses and mounts the interactive filter list interface.
import React from "react";
import { Navbar } from "@/components/Navbar";
import { CoursesFilterList, Course } from "@/components/CoursesFilterList";

export default async function CoursesPage() {
  // Mock data fetching. In production, this would make a server-side query to the database/FastAPI
  const courses: Course[] = [
    {
      id: "python-101",
      title: "Python Programming Basics",
      description: "Master variables, loops, objects, exceptions, and foundational logic inside Python.",
      difficulty: "Beginner",
      topic: "Programming",
      duration: 3,
      enrolled: true,
      progress: 68,
      thumbnail: "🐍",
    },
    {
      id: "data-science-intro",
      title: "Introduction to Data Science",
      description: "Explore data processing, Pandas structures, statistical modeling, and data visualizing packages.",
      difficulty: "Intermediate",
      topic: "Data Science",
      duration: 5,
      enrolled: true,
      progress: 35,
      thumbnail: "📊",
    },
    {
      id: "rag-pipelines",
      title: "Building RAG Pipelines with LlamaIndex",
      description: "Learn index construction, vector retrieval models, and contextual LLM generation.",
      difficulty: "Intermediate",
      topic: "Data Science",
      duration: 4.5,
      enrolled: false,
      thumbnail: "🤖",
    },
    {
      id: "langgraph-agents",
      title: "Multi-Agent Coordination with LangGraph",
      description: "Master state graphs, cognitive agent routing loops, and human-in-the-loop triggers.",
      difficulty: "Advanced",
      topic: "Programming",
      duration: 6,
      enrolled: false,
      thumbnail: "🧠",
    },
    {
      id: "postgres-deepdive",
      title: "PostgreSQL Database Administration",
      description: "Optimize queries, scale database nodes, and configure custom volumes in Docker.",
      difficulty: "Beginner",
      topic: "Infrastructure",
      duration: 8,
      enrolled: false,
      thumbnail: "🗄️",
    },
    {
      id: "ui-ux-design-foundations",
      title: "UI/UX Design Foundations",
      description: "Understand user flows, grid structures, layouts, wireframing, and interactive design theories.",
      difficulty: "Beginner",
      topic: "Design",
      duration: 4,
      enrolled: false,
      thumbnail: "🎨",
    },
  ];

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col font-sans">
      <Navbar />
      
      <main className="flex-grow max-w-7xl mx-auto px-6 py-10 w-full space-y-6">
        <div>
          <h1 className="text-3xl font-extrabold text-white">Course Catalog</h1>
          <p className="text-slate-400 text-sm mt-1">
            Browse through our syllabus paths customized by artificial intelligence.
          </p>
        </div>

        <CoursesFilterList initialCourses={courses} />
      </main>
    </div>
  );
}
