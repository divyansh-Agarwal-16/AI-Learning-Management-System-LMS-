// This client-side multi-step onboarding wizard collects user goals, proficiency levels, and time commitments, redirecting to the dashboard on completion.
"use client";

import React, { useState } from "react";
import { useRouter } from "next/navigation";

export default function OnboardingPage() {
  const router = useRouter();
  const [step, setStep] = useState(1);
  const [formData, setFormData] = useState({
    subject: "",
    level: "",
    hours: 10,
  });

  const nextStep = () => {
    if (step === 1 && !formData.subject) return;
    if (step === 2 && !formData.level) return;
    
    if (step < 3) {
      setStep(step + 1);
    } else {
      // Mock onboarding finalization
      router.push("/dashboard");
    }
  };

  const prevStep = () => {
    if (step > 1) {
      setStep(step - 1);
    }
  };

  const handleSelectSubject = (e: React.ChangeEvent<HTMLSelectElement>) => {
    setFormData({ ...formData, subject: e.target.value });
  };

  const handleSelectLevel = (level: string) => {
    setFormData({ ...formData, level });
  };

  const handleSliderChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setFormData({ ...formData, hours: parseInt(e.target.value, 10) });
  };

  const progressPercentage = (step / 3) * 100;

  return (
    <div className="min-h-screen bg-slate-950 flex flex-col justify-center py-12 px-6 lg:px-8 text-slate-100 font-sans">
      <div className="sm:mx-auto sm:w-full sm:max-w-md text-center mb-8">
        <span className="text-sm font-semibold tracking-wider text-indigo-400 uppercase">
          Onboarding Process
        </span>
        <h2 className="mt-2 text-3xl font-extrabold tracking-tight text-white">
          Personalize Your Experience
        </h2>
      </div>

      <div className="sm:mx-auto sm:w-full sm:max-w-xl">
        <div className="bg-slate-900/60 border border-slate-900 py-8 px-6 shadow-xl rounded-xl sm:px-10">
          
          {/* Progress Bar Header */}
          <div className="mb-8">
            <div className="flex justify-between items-center text-sm text-slate-400 mb-2">
              <span>Step {step} of 3</span>
              <span className="font-semibold text-indigo-400">{Math.round(progressPercentage)}% Complete</span>
            </div>
            <div className="w-full bg-slate-800 h-2 rounded-full overflow-hidden">
              <div 
                className="bg-gradient-to-r from-indigo-500 to-purple-500 h-full transition-all duration-300"
                style={{ width: `${progressPercentage}%` }}
              />
            </div>
          </div>

          {/* Form Content */}
          <div className="min-h-[220px]">
            {step === 1 && (
              <div className="space-y-4">
                <h3 className="text-xl font-bold text-slate-200">What do you want to learn?</h3>
                <p className="text-slate-400 text-sm">Select the subject area you would like your AI Tutor to personalize material for.</p>
                <div className="mt-4">
                  <select
                    value={formData.subject}
                    onChange={handleSelectSubject}
                    className="block w-full px-3 py-3 border border-slate-800 rounded-lg bg-slate-950 text-slate-300 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent text-sm"
                  >
                    <option value="" disabled>-- Choose a Subject --</option>
                    <option value="Programming">Programming</option>
                    <option value="Data Science">Data Science</option>
                    <option value="Design">Design</option>
                    <option value="Mathematics">Mathematics</option>
                    <option value="Language">Language</option>
                    <option value="Other">Other</option>
                  </select>
                </div>
              </div>
            )}

            {step === 2 && (
              <div className="space-y-4">
                <h3 className="text-xl font-bold text-slate-200">What is your current level?</h3>
                <p className="text-slate-400 text-sm">Choose the description that best fits your current knowledge in this subject.</p>
                <div className="grid grid-cols-1 gap-4 sm:grid-cols-3 mt-4">
                  {["Beginner", "Intermediate", "Advanced"].map((level) => (
                    <button
                      key={level}
                      type="button"
                      onClick={() => handleSelectLevel(level)}
                      className={`p-4 border rounded-xl flex flex-col items-center justify-center transition-all ${
                        formData.level === level
                          ? "border-indigo-500 bg-indigo-500/10 shadow-lg shadow-indigo-500/5"
                          : "border-slate-800 bg-slate-950 hover:bg-slate-900"
                      }`}
                    >
                      <span className="font-semibold text-slate-200">{level}</span>
                    </button>
                  ))}
                </div>
              </div>
            )}

            {step === 3 && (
              <div className="space-y-4">
                <h3 className="text-xl font-bold text-slate-200">How many hours per week can you study?</h3>
                <p className="text-slate-400 text-sm">Set your weekly study goal to help customize lesson delivery schedules.</p>
                <div className="mt-8 space-y-4">
                  <div className="flex justify-between items-center text-slate-200 font-semibold text-lg">
                    <span>Study Hours:</span>
                    <span className="text-indigo-400 bg-indigo-500/10 px-3 py-1 rounded-full text-base">{formData.hours} hrs/week</span>
                  </div>
                  <input
                    type="range"
                    min="1"
                    max="20"
                    value={formData.hours}
                    onChange={handleSliderChange}
                    className="w-full h-2 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-indigo-500"
                  />
                  <div className="flex justify-between text-xs text-slate-500">
                    <span>1 hour</span>
                    <span>10 hours</span>
                    <span>20 hours</span>
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Navigation Buttons */}
          <div className="mt-8 flex justify-between gap-4">
            {step > 1 ? (
              <button
                type="button"
                onClick={prevStep}
                className="px-6 py-2 border border-slate-800 hover:bg-slate-900 text-slate-300 hover:text-white rounded-lg transition-colors text-sm font-semibold"
              >
                Back
              </button>
            ) : (
              <div />
            )}

            <button
              type="button"
              onClick={nextStep}
              disabled={
                (step === 1 && !formData.subject) ||
                (step === 2 && !formData.level)
              }
              className="px-6 py-2 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-55 text-white rounded-lg transition-colors text-sm font-semibold shadow-lg shadow-indigo-500/10"
            >
              {step === 3 ? "Complete" : "Next"}
            </button>
          </div>

        </div>
      </div>
    </div>
  );
}
