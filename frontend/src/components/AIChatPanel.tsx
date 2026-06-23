// This component implements the custom SSE streaming AI chat interface for courses, displaying real-time replies, suggestions, and specialized agent badges.
"use client";

import React, { useRef, useEffect, useState } from "react";
import { getSession } from "next-auth/react";
import Link from "next/link";

interface AIChatPanelProps {
  courseId: string;
  externalPrompt?: { text: string; timestamp: number } | null;
}

interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  parts: { type: "text" | "reasoning"; text: string }[];
  agent?: string;
}

export function AIChatPanel({ courseId, externalPrompt }: AIChatPanelProps) {
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState<ChatMessage[]>([
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
  ]);
  
  const [isLoading, setIsLoading] = useState(false);
  const [currentAgent, setCurrentAgent] = useState<string | null>(null);
  const [connectionError, setConnectionError] = useState<string | null>(null);
  const [interruptData, setInterruptData] = useState<any>(null);

  const chatEndRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom of chat
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isLoading]);

  const suggestions = [
    "Explain this lesson in simple terms",
    "Generate a 3-question quiz for me",
    "What are the main key takeaways?",
  ];

  const handleSendMessage = async (text: string) => {
    if (!text.trim() || isLoading) return;

    setIsLoading(true);
    setConnectionError(null);
    setCurrentAgent("orchestrator");
    setInterruptData(null);

    // Append user message
    const userMsg: ChatMessage = {
      id: Math.random().toString(),
      role: "user",
      parts: [{ type: "text", text }],
    };
    setMessages((prev) => [...prev, userMsg]);

    try {
      const session = await getSession();
      const token = session ? (session.user as any).accessToken : (typeof window !== "undefined" ? localStorage.getItem("accessToken") : null);
      
      const apiBaseUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";
      const res = await fetch(`${apiBaseUrl}/ai/chat?course_id=${courseId}`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${token || ""}`,
        },
        body: JSON.stringify({ message: text }),
      });

      if (!res.ok) {
        throw new Error(`Chat request failed with status: ${res.status}`);
      }

      // Initialize empty assistant message
      const assistantMsg: ChatMessage = {
        id: Math.random().toString(),
        role: "assistant",
        parts: [{ type: "text", text: "" }],
      };
      setMessages((prev) => [...prev, assistantMsg]);

      // Read SSE stream
      const reader = res.body?.getReader();
      const decoder = new TextDecoder();
      let buffer = "";

      if (!reader) {
        throw new Error("Response body is not readable");
      }

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        
        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n");
        buffer = lines.pop() || "";

        for (const line of lines) {
          const cleanLine = line.trim();
          if (cleanLine.startsWith("data: ")) {
            const dataStr = cleanLine.slice(6).trim();
            if (!dataStr) continue;
            try {
              const payload = JSON.parse(dataStr);
              if (payload.type === "token") {
                setMessages((prev) => {
                  const list = [...prev];
                  const last = list[list.length - 1];
                  if (last && last.role === "assistant") {
                    const textPart = last.parts[0];
                    if (textPart) {
                      textPart.text += payload.content;
                    }
                  }
                  return list;
                });
              } else if (payload.type === "agent_start") {
                setCurrentAgent(payload.agent);
              } else if (payload.type === "agent_end") {
                // Keep the active agent tracker or reset on end
              } else if (payload.type === "interrupt") {
                setInterruptData(payload.quiz_data);
              } else if (payload.type === "error") {
                setConnectionError(payload.content);
              }
            } catch {
              // Ignore parse errors on partial streams
            }
          }
        }
      }
    } catch (err: any) {
      console.error("SSE stream error:", err);
      setConnectionError(err.message || "Unable to establish connection to AI Tutor.");
    } finally {
      setIsLoading(false);
      setCurrentAgent(null);
    }
  };

  // Watch for external prompts (like concept map node clicks)
  useEffect(() => {
    if (externalPrompt?.text) {
      handleSendMessage(externalPrompt.text);
    }
  }, [externalPrompt]);

  const handleSuggestionClick = (suggestion: string) => {
    handleSendMessage(suggestion);
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isLoading) return;
    handleSendMessage(input);
    setInput("");
  };

  // Map backend agent codes to beautiful display labels & styles
  const getAgentBadge = (agentCode: string | null) => {
    if (!agentCode) return null;
    switch (agentCode.toLowerCase()) {
      case "tutor":
        return <span className="text-[10px] px-2 py-0.5 bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 rounded-full font-semibold">Tutor Agent</span>;
      case "quiz_generator":
        return <span className="text-[10px] px-2 py-0.5 bg-indigo-500/10 text-indigo-400 border border-indigo-500/20 rounded-full font-semibold">Quiz Agent</span>;
      case "path_advisor":
        return <span className="text-[10px] px-2 py-0.5 bg-purple-500/10 text-purple-400 border border-purple-500/20 rounded-full font-semibold">Path Advisor</span>;
      case "orchestrator":
        return <span className="text-[10px] px-2 py-0.5 bg-slate-800 text-slate-300 border border-slate-700 rounded-full font-semibold">Orchestrator</span>;
      default:
        return <span className="text-[10px] px-2 py-0.5 bg-slate-800 text-slate-300 border border-slate-700 rounded-full font-semibold">{agentCode}</span>;
    }
  };

  return (
    <div className="flex flex-col h-full bg-slate-900/40 border border-slate-900 rounded-xl text-slate-100 font-sans shadow-lg">
      
      {/* Panel Header */}
      <div className="p-4 border-b border-slate-900 flex items-center justify-between bg-slate-950/40 rounded-t-xl">
        <div className="flex items-center gap-2">
          <span className={`w-2.5 h-2.5 rounded-full ${isLoading ? "bg-indigo-500 animate-ping" : "bg-emerald-500"}`} />
          <h3 className="font-semibold text-slate-200 text-sm">Personal AI Tutor</h3>
        </div>
        {isLoading ? getAgentBadge(currentAgent) : <span className="text-[10px] text-slate-500 uppercase tracking-wider">Active</span>}
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
                    return null;
                  })}
                </div>
              </div>
            </div>
          );
        })}

        {/* Connection Error Alert */}
        {connectionError && (
          <div className="p-3 bg-red-900/20 border border-red-900/50 text-red-200 text-xs rounded-lg">
            ⚠️ {connectionError}
          </div>
        )}

        {/* Interrupt/Human-in-the-loop Notification */}
        {interruptData && (
          <div className="p-4 bg-indigo-950/40 border border-indigo-500/30 rounded-xl space-y-3">
            <div className="text-xs font-semibold text-slate-200 flex items-center gap-1.5">
              <span>📋</span> Practice Quiz Ready for Review
            </div>
            <p className="text-[11px] text-slate-400">
              The AI Tutor has generated a custom quiz on this topic. Do you want to take it?
            </p>
            <div className="flex gap-2">
              <Link 
                href={`/quiz/${interruptData.id || "generated"}`}
                className="px-3 py-1 bg-indigo-600 hover:bg-indigo-500 text-white rounded text-[11px] font-semibold transition-colors"
              >
                Start Quiz
              </Link>
            </div>
          </div>
        )}

        {/* Loading skeleton */}
        {isLoading && !messages[messages.length - 1]?.parts[0]?.text && (
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
            disabled={isLoading}
            placeholder={isLoading ? "AI Tutor is processing..." : "Ask a question..."}
            className="flex-1 min-w-0 px-3.5 py-2 border border-slate-800 rounded-lg bg-slate-950 placeholder-slate-600 text-sm text-white focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent disabled:opacity-50"
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
