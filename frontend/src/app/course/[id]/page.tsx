// This server-side route fetches individual course resources and details, and maps them to the interactive client layout.
import React from "react";
import { Navbar } from "@/components/Navbar";
import { CourseDetailView, CourseDetail } from "@/components/CourseDetailView";

interface CoursePageProps {
  params: {
    id: string;
  };
}

export default async function CoursePage({ params }: CoursePageProps) {
  // Mock data fetching logic. In production, this pulls from the database or backend based on params.id
  const course: CourseDetail = {
    id: params.id,
    title: params.id === "python-101" ? "Python Programming Basics" : "Building RAG Pipelines with LlamaIndex",
    description: "Learn foundational concepts and advanced cognitive integrations mapped to this subject area.",
    lessons: [
      {
        id: "l1",
        title: "Introduction and Environment Setup",
        duration: "10m",
        completed: true,
        videoUrl: "https://www.youtube.com/watch?v=kqtD5dpn9C8", // Standard Python tutorial URL
      },
      {
        id: "l2",
        title: "Variables, Arrays, and Expressions",
        duration: "15m",
        completed: true,
        videoUrl: "https://www.youtube.com/watch?v=Z1Yd7upQsXY",
      },
      {
        id: "l3",
        title: "Conditions, Branches, and Loop Logic",
        duration: "12m",
        completed: false,
        videoUrl: "https://www.youtube.com/watch?v=6iF8Xb7Z3kQ",
      },
      {
        id: "l4",
        title: "Hands-on Exercise: Parsing Data Logs",
        duration: "22m",
        completed: false,
        videoUrl: "",
        pdfUrl: "https://www.w3.org/WAI/ER/tests/xhtml/testfiles/resources/pdf/dummy.pdf", // Mock PDF source
      },
    ],
    overview: "This curriculum covers fundamental loops, scope definitions, structures, and tools designed to build competency.",
    notes: `# Key Code Takeaways:
1. Loops use standard syntax: 'for item in list'
2. Always wrap exceptions: 'try ... except Exception as e'
3. Context variables leverage 'with open(...) as f' statements.`,
    quiz: [
      {
        question: "Which keyword is used to declare a function in Python?",
        options: ["function", "def", "func", "define"],
        answer: 1, // 'def' is the second option
      },
      {
        question: "What is the return value of print() in Python?",
        options: ["None", "0", "True", "An empty string"],
        answer: 0, // 'None' is the first option
      },
    ],
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col font-sans">
      <Navbar />
      <CourseDetailView course={course} />
    </div>
  );
}
