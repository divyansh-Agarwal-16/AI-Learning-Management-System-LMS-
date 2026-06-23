"use client";

import React, { useState } from "react";
import { useQuery, useMutation } from "@tanstack/react-query";
import { useRouter } from "next/navigation";
import { Navbar } from "@/components/Navbar";
import { quizzesApi, aiApi, SubmissionResponse, SubmissionDetail } from "@/lib/api";
import Link from "next/link";

interface QuizPageProps {
  params: {
    id: string;
  };
}

// Child component to lazily load and render AI Feedback for a specific question answer
function AIFeedbackCard({ detail }: { detail: SubmissionDetail }) {
  const { data, isLoading, error } = useQuery({
    queryKey: ["answerFeedback", detail.question_id, detail.selected_option_idx],
    queryFn: () => aiApi.getAnswerFeedback(
      detail.question_text,
      detail.selected_answer_text,
      detail.correct_answer_text
    ),
    staleTime: Infinity, // Feedback doesn't change
  });

  if (isLoading) {
    return (
      <div className="mt-3 p-4 bg-slate-950 border border-slate-900 rounded-xl animate-pulse space-y-2">
        <div className="h-4 bg-slate-800 rounded w-1/3" />
        <div className="h-3 bg-slate-850 rounded w-2/3" />
        <div className="h-3 bg-slate-850 rounded w-1/2" />
      </div>
    );
  }

  if (error || !data?.success) {
    return (
      <div className="mt-3 p-3 bg-red-900/10 border border-red-900/40 text-red-200 text-xs rounded-lg">
        Could not retrieve AI Tutor feedback for this answer.
      </div>
    );
  }

  const feedback = data.data;

  return (
    <div className="mt-3 p-4 bg-indigo-950/20 border border-indigo-950/40 rounded-xl space-y-3">
      <div className="flex justify-between items-center border-b border-indigo-950/60 pb-2">
        <span className="text-xs font-semibold text-indigo-300">AI Tutor Feedback</span>
        <span className="text-xs bg-indigo-500/10 text-indigo-400 px-2 py-0.5 rounded-full font-bold">
          Score: {feedback.score}/10
        </span>
      </div>
      <p className="text-xs text-slate-300 leading-relaxed">{feedback.feedback}</p>
      <div className="space-y-1.5 pt-1">
        <h5 className="text-[11px] font-bold text-slate-400 uppercase tracking-wider">Suggested Improvements:</h5>
        <ul className="list-disc pl-4 text-xs text-slate-400 space-y-1">
          {feedback.improvements.map((imp, idx) => (
            <li key={idx}>{imp}</li>
          ))}
        </ul>
      </div>
    </div>
  );
}

export default function QuizPage({ params }: QuizPageProps) {
  const router = useRouter();
  const quizId = params.id;
  const [selectedAnswers, setSelectedAnswers] = useState<Record<string, number>>({});
  const [submissionResult, setSubmissionResult] = useState<SubmissionResponse | null>(null);

  // 1. Fetch Quiz Details
  const { data: quizRes, isLoading: quizLoading, error: quizError } = useQuery({
    queryKey: ["quiz", quizId],
    queryFn: () => quizzesApi.getQuiz(quizId),
  });

  // 2. Submit Quiz Mutation
  const submitMutation = useMutation({
    mutationFn: (answers: { question_id: string; selected_option_idx: number }[]) => 
      quizzesApi.submitQuiz(quizId, answers),
    onSuccess: (res) => {
      if (res.success) {
        setSubmissionResult(res.data);
      }
    },
  });

  const quiz = quizRes?.data;
  const isSubmitting = submitMutation.isPending;

  const handleOptionChange = (questionId: string, optionIdx: number) => {
    if (submissionResult) return; // Locked after submit
    setSelectedAnswers((prev) => ({
      ...prev,
      [questionId]: optionIdx,
    }));
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!quiz || isSubmitting || submissionResult) return;

    // Validate all answered
    const unanswered = quiz.questions.filter((q) => selectedAnswers[q.id] === undefined);
    if (unanswered.length > 0) {
      alert("Please answer all questions before submitting.");
      return;
    }

    const payload = quiz.questions.map((q) => ({
      question_id: q.id,
      selected_option_idx: selectedAnswers[q.id],
    }));

    submitMutation.mutate(payload);
  };

  if (quizLoading) {
    return (
      <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col font-sans">
        <Navbar />
        <main className="flex-grow max-w-3xl mx-auto px-6 py-12 w-full space-y-6">
          <div className="h-8 bg-slate-900 animate-pulse rounded w-1/3" />
          <div className="h-4 bg-slate-900 animate-pulse rounded w-1/2" />
          <div className="space-y-4 pt-6">
            {[1, 2, 3].map((i) => (
              <div key={i} className="p-6 bg-slate-900/20 border border-slate-900 rounded-xl h-44 animate-pulse" />
            ))}
          </div>
        </main>
      </div>
    );
  }

  if (quizError || !quiz) {
    return (
      <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col font-sans">
        <Navbar />
        <main className="flex-grow max-w-3xl mx-auto px-6 py-20 w-full text-center space-y-4">
          <div className="text-4xl">⚠️</div>
          <h2 className="text-xl font-bold">Quiz Not Found</h2>
          <p className="text-slate-400 text-sm">We couldn&apos;t load the practice quiz. It might have been deleted or the link is incorrect.</p>
          <div className="pt-4">
            <Link href="/dashboard" className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 rounded-lg text-xs font-semibold text-white">
              Back to Dashboard
            </Link>
          </div>
        </main>
      </div>
    );
  }

  // Determine if quiz score was low
  const scorePercent = submissionResult ? Math.round((submissionResult.score / submissionResult.total_questions) * 100) : 0;
  const isWeakResult = submissionResult && scorePercent < 60;

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col font-sans">
      <Navbar />

      <main className="flex-grow max-w-3xl mx-auto px-6 py-12 w-full space-y-8">
        
        {/* Quiz Header */}
        <div className="border-b border-slate-900 pb-6">
          <h1 className="text-3xl font-extrabold text-white">{quiz.title}</h1>
          <p className="text-slate-400 text-sm mt-1">
            Grade your skill level on this module. Responses are analyzed by the AI Tutor.
          </p>
        </div>

        {/* Final Score Report */}
        {submissionResult && (
          <div className={`p-6 border rounded-2xl flex flex-col sm:flex-row items-center justify-between gap-6 shadow-xl ${
            isWeakResult 
              ? "bg-red-950/20 border-red-500/30" 
              : "bg-indigo-950/20 border-indigo-500/30"
          }`}>
            <div>
              <h2 className="text-xl font-extrabold text-white">Quiz Completed!</h2>
              <p className="text-xs text-slate-400 mt-1">
                You correctly answered {submissionResult.score} of {submissionResult.total_questions} questions.
              </p>
              {isWeakResult && (
                <div className="mt-3 text-xs text-red-400 bg-red-500/10 border border-red-500/20 px-3 py-1.5 rounded-lg font-semibold flex items-center gap-1.5">
                  <span>⚠️</span> Weak Area Highlighted: Study this lesson and ask the AI Tutor for a review.
                </div>
              )}
            </div>
            <div className="flex flex-col items-center shrink-0">
              <span className={`text-4xl font-black ${isWeakResult ? "text-red-400" : "text-indigo-400"}`}>
                {scorePercent}%
              </span>
              <span className="text-[10px] text-slate-500 font-bold uppercase tracking-wider mt-1">Final Score</span>
            </div>
          </div>
        )}

        {/* Questions List */}
        <form onSubmit={handleSubmit} className="space-y-6">
          {quiz.questions.map((q, idx) => {
            // Find grading result for this question if submitted
            const detail = submissionResult?.details.find((d) => d.question_id === q.id);
            const isCorrect = detail?.is_correct;
            const hasDetail = detail !== undefined;

            return (
              <div 
                key={q.id} 
                className={`p-6 bg-slate-900/40 border border-slate-900 rounded-2xl transition-colors space-y-4 ${
                  hasDetail 
                    ? isCorrect 
                      ? "border-emerald-500/20 hover:border-emerald-500/30" 
                      : "border-red-500/20 hover:border-red-500/30"
                    : "hover:border-slate-800"
                }`}
              >
                <div className="flex justify-between items-start gap-4">
                  <h3 className="font-bold text-slate-200 text-sm">
                    {idx + 1}. {q.text}
                  </h3>
                  {hasDetail && (
                    <span className={`text-[10px] px-2 py-0.5 rounded border uppercase font-bold whitespace-nowrap ${
                      isCorrect 
                        ? "text-emerald-400 bg-emerald-500/10 border-emerald-500/20" 
                        : "text-red-400 bg-red-500/10 border-red-500/20"
                    }`}>
                      {isCorrect ? "Correct ✓" : "Incorrect ✗"}
                    </span>
                  )}
                </div>

                {/* Option Choices */}
                <div className="grid grid-cols-1 gap-3">
                  {q.options.map((opt, oIdx) => {
                    const isSelected = selectedAnswers[q.id] === oIdx;
                    const isCorrectAnswer = detail?.correct_option_idx === oIdx;
                    const isSelectedIncorrect = hasDetail && isSelected && !isCorrect;

                    let optionStyle = "border-slate-800 bg-slate-950 hover:bg-slate-900";
                    if (isSelected && !hasDetail) {
                      optionStyle = "border-indigo-500 bg-indigo-500/5 text-indigo-400";
                    } else if (hasDetail) {
                      if (isCorrectAnswer) {
                        optionStyle = "border-emerald-500 bg-emerald-500/5 text-emerald-400 font-semibold";
                      } else if (isSelectedIncorrect) {
                        optionStyle = "border-red-500 bg-red-500/5 text-red-400 font-semibold";
                      } else {
                        optionStyle = "border-slate-900 bg-slate-950/40 text-slate-500 opacity-60";
                      }
                    }

                    return (
                      <label
                        key={oIdx}
                        className={`flex items-center gap-3 p-3.5 rounded-xl border text-xs cursor-pointer transition-all ${optionStyle}`}
                      >
                        <input
                          type="radio"
                          name={`question-${q.id}`}
                          checked={isSelected}
                          disabled={hasDetail}
                          onChange={() => handleOptionChange(q.id, oIdx)}
                          className="text-indigo-600 focus:ring-indigo-500 border-slate-800 bg-slate-950 disabled:opacity-50"
                        />
                        <span>{opt}</span>
                      </label>
                    );
                  })}
                </div>

                {/* AI Tutor feedback lazily rendered per answer after submission */}
                {detail && <AIFeedbackCard detail={detail} />}
              </div>
            );
          })}

          {/* Action Buttons */}
          <div className="flex justify-end gap-4 pt-4 border-t border-slate-900">
            {submissionResult ? (
              <Link 
                href="/dashboard"
                className="px-6 py-2.5 bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg text-xs font-semibold transition-colors shadow shadow-indigo-500/10"
              >
                Back to Dashboard
              </Link>
            ) : (
              <button
                type="submit"
                disabled={isSubmitting}
                className="px-6 py-2.5 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white rounded-lg text-xs font-semibold transition-colors shadow shadow-indigo-500/10"
              >
                {isSubmitting ? "Grading answers..." : "Submit Quiz"}
              </button>
            )}
          </div>
        </form>

      </main>
    </div>
  );
}
