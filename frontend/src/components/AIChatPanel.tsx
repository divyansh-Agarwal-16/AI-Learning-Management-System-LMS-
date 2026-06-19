// This component implements the streaming AI chat interface for courses, using the Vercel AI SDK to display responses and suggestion chips.
"use client";

import React, { useRef, useEffect, useState } from "react";
import { useChat, UIMessage } from "@ai-sdk/react";
import { DefaultChatTransport } from "ai";

interface AIChatPanelProps {
  courseId: string;
}

export function AIChatPanel({ courseId }: AIChatPanelProps) {
  const [input, setInput] = useState("");
  
  // Use Vercel AI SDK useChat hook. Sends requests to /api/chat with courseId metadata.
  const { messages, sendMessage, status } = useChat<UIMessage>({
    transport: new DefaultChatTransport({
      api: "/api/chat",
      body: { courseId },
    }),
    messages: [
      {
        id: "welcome",
        role: "assistant",
        parts: [
          {
            type: "text",
            text: "Hi! I am your AI Tutor. I have access to the LlamaIndex RAG pipeline for this course. What would you like to learn or clarify today?",
          },
        ],
      },
    ],
  });

  const isLoading = status === "submitted" || status === "streaming";
  const chatEndRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom of chat when messages update or loading state changes
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isLoading]);

  const suggestions = [
    "Explain this lesson in simple terms",
    "Generate a 3-question quiz for me",
    "What are the main key takeaways?",
  ];

  const handleSuggestionClick = (suggestion: string) => {
    sendMessage({ text: suggestion });
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim()) return;
    sendMessage({ text: input });
    setInput("");
  };

  return (
    <div className="flex flex-col h-full bg-slate-900/40 border border-slate-900 rounded-xl text-slate-100 font-sans">
      
      {/* Panel Header */}
      <div className="p-4 border-b border-slate-900 flex items-center justify-between bg-slate-950/40 rounded-t-xl">
        <div className="flex items-center gap-2">
          <span className="w-2.5 h-2.5 rounded-full bg-emerald-500 animate-pulse" />
          <h3 className="font-semibold text-slate-200 text-sm">Personal AI Tutor</h3>
        </div>
        <span className="text-[10px] text-slate-500 uppercase tracking-widest">Course ID: {courseId}</span>
      </div>

      {/* Message List */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4 max-h-[420px] min-h-[300px]">
        {messages.map((msg) => {
          const isUser = msg.role === "user";
          return (
            <div 
              key={msg.id} 
              className={`flex ${isUser ? "justify-end" : "justify-start"}`}
            >
              <div 
                className={`max-w-[85%] rounded-xl px-4 py-2.5 text-sm shadow ${
                  isUser 
                    ? "bg-indigo-600 text-white rounded-br-none" 
                    : "bg-slate-950/80 border border-slate-800 text-slate-300 rounded-bl-none leading-relaxed"
                }`}
              >
                <div className="font-semibold text-[10px] opacity-75 mb-1">
                  {isUser ? "You" : "AI Tutor"}
                </div>
                <div className="whitespace-pre-wrap">
                  {msg.parts?.map((part, pIdx) => {
                    if (part.type === "text") {
                      return <span key={pIdx}>{part.text}</span>;
                    }
                    if (part.type === "reasoning") {
                      return <span key={pIdx} className="text-slate-500 italic">{part.text}</span>;
                    }
                    return null;
                  })}
                </div>
              </div>
            </div>
          );
        })}

        {/* Loading skeleton */}
        {isLoading && (
          <div className="flex justify-start">
            <div className="max-w-[85%] rounded-xl px-4 py-2.5 bg-slate-950/80 border border-slate-800 text-slate-300 rounded-bl-none shadow space-y-2 w-2/3">
              <div className="font-semibold text-[10px] opacity-75">AI Tutor</div>
              <div className="flex items-center gap-1.5 py-1">
                <span className="w-2 h-2 rounded-full bg-slate-600 animate-bounce" style={{ animationDelay: "0ms" }} />
                <span className="w-2 h-2 rounded-full bg-slate-600 animate-bounce" style={{ animationDelay: "150ms" }} />
                <span className="w-2 h-2 rounded-full bg-slate-600 animate-bounce" style={{ animationDelay: "300ms" }} />
              </div>
            </div>
          </div>
        )}
        <div ref={chatEndRef} />
      </div>

      {/* Suggested Questions Chips */}
      {suggestions.length > 0 && !isLoading && (
        <div className="px-4 py-2 border-t border-slate-900/60 bg-slate-950/20">
          <div className="flex flex-wrap gap-2">
            {suggestions.map((sug, idx) => (
              <button
                key={idx}
                onClick={() => handleSuggestionClick(sug)}
                className="text-xs px-2.5 py-1 bg-slate-900 border border-slate-800 hover:border-indigo-500/50 hover:text-indigo-400 rounded-full transition-colors text-slate-400 text-left"
              >
                {sug}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Input Form */}
      <form onSubmit={handleSubmit} className="p-4 border-t border-slate-900 bg-slate-950/40 rounded-b-xl">
        <div className="flex gap-2">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask a question..."
            className="flex-1 min-w-0 px-3.5 py-2 border border-slate-800 rounded-lg bg-slate-950 placeholder-slate-600 text-sm text-white focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
          />
          <button
            type="submit"
            disabled={isLoading || !input.trim()}
            className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white rounded-lg text-sm font-semibold transition-colors flex items-center justify-center"
          >
            Send
          </button>
        </div>
      </form>

    </div>
  );
}
