import { NextRequest } from "next/server";
import { getServerSession } from "next-auth";
import { authOptions } from "@/lib/auth";

export async function POST(req: NextRequest) {
  // Check user session
  const session = await getServerSession(authOptions);
  if (!session) {
    return new Response("Unauthorized", { status: 401 });
  }

  try {
    // 1. Parse request body containing messages list and course ID metadata
    const body = await req.json();
    const { messages, courseId } = body;
    
    // Vercel AI SDK sends message list, retrieve latest user message content
    const lastMsg = messages[messages.length - 1];
    const userMessage = lastMsg?.content || lastMsg?.text || "";

    if (!userMessage) {
      return new Response("Empty message prompt", { status: 400 });
    }

    // 2. Fetch authenticated bearer JWT from backend using seeded credentials
    const loginRes = await fetch("http://localhost:8000/api/v1/auth/login", {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      body: new URLSearchParams({
        username: "test@test.com",
        password: "password123"
      })
    });

    if (!loginRes.ok) {
      return new Response("FastAPI backend auth credentials exchange failed", { status: 500 });
    }

    const loginData = await loginRes.json();
    // Resolve token location mapping base response envelopes
    const token = loginData.data?.access_token || loginData.access_token;

    if (!token) {
      return new Response("Access token missing in backend response", { status: 500 });
    }

    // 3. Query the FastAPI RAG Multi-Agent SSE endpoint
    const backendUrl = `http://localhost:8000/api/v1/ai/chat?course_id=${courseId}`;
    const aiRes = await fetch(backendUrl, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "Authorization": `Bearer ${token}`
      },
      body: JSON.stringify({ message: userMessage })
    });

    if (!aiRes.ok) {
      const errorText = await aiRes.text();
      return new Response(`AI Agent response failure: ${errorText}`, { status: aiRes.status });
    }

    // 4. Pipe event stream chunks directly back to Vercel AI SDK client
    return new Response(aiRes.body, {
      headers: {
        "Content-Type": "text/event-stream",
        "Cache-Control": "no-cache",
        "Connection": "keep-alive"
      }
    });

  } catch (error: any) {
    return new Response(`Internal Server Error: ${error?.message || error}`, { status: 500 });
  }
}
