# AI Learning Management System (ai-lms)

## Project Information
- **Project**: AI Learning Management System
- **Stack**: Next.js 14, FastAPI, PostgreSQL, Pinecone, LangGraph, OpenAI GPT-4, Docker
- **Goal**: Personalized AI tutor with RAG, multi-agent orchestration, quiz generation, adaptive learning paths
- **Current status**: Project initialized

## Build & Run Commands
- **Frontend (Next.js)**:
  - Run development server: `cd frontend && npm run dev`
  - Build project: `cd frontend && npm run build`
  - Lint: `cd frontend && npm run lint`
- **Backend (FastAPI)**:
  - Run server: `cd backend && uvicorn main:app --reload`
- **Docker Compose**:
  - Run services: `docker compose -f docker/docker-compose.yml up`
