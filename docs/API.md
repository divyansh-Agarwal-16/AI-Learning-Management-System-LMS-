# API Reference Documentation

This document describes the complete REST API interface for the AI-LMS system. The base URL for all endpoints is `/api/v1`.

All JSON response payloads follow a unified wrapper schema:
```json
{
  "success": true,
  "data": { ... },
  "message": "Optional message string"
}
```

---

## 🔑 Authentication Router (`/auth`)

Endpoints for handling user registration, authentication, token refresh, and recovery.

### 1. User Signup
* **Endpoint:** `POST /auth/signup`
* **Authentication:** None
* **Request Body:**
  ```json
  {
    "email": "student@example.com",
    "password": "password123",
    "full_name": "Jane Doe"
  }
  ```
* **Success Response (201 Created):**
  ```json
  {
    "success": true,
    "data": {
      "id": "e83b879f-689b-4395-88f5-4672e61df3f7",
      "email": "student@example.com",
      "full_name": "Jane Doe",
      "role": "student",
      "created_at": "2026-06-23T12:00:00Z"
    },
    "message": "User registered successfully"
  }
  ```
* **Error Response (400 Bad Request):** If the email is already registered.

### 2. User Login
* **Endpoint:** `POST /auth/login`
* **Authentication:** None
* **Request Body:**
  ```json
  {
    "email": "student@example.com",
    "password": "password123"
  }
  ```
* **Success Response (200 OK):**
  ```json
  {
    "success": true,
    "data": {
      "access_token": "eyJhbGciOi...",
      "refresh_token": "eyJhbGciOi...",
      "token_type": "bearer"
    },
    "message": "Login successful"
  }
  ```
* **Error Response (401 Unauthorized):** Invalid email or password.

### 3. Refresh Access Token
* **Endpoint:** `POST /auth/refresh`
* **Authentication:** None
* **Query Parameters:** `refresh_token` (string)
* **Success Response (200 OK):**
  ```json
  {
    "success": true,
    "data": {
      "access_token": "eyJhbGciOi...",
      "refresh_token": "eyJhbGciOi...",
      "token_type": "bearer"
    },
    "message": "Tokens refreshed successfully"
  }
  ```

### 4. Forgot Password (Mock)
* **Endpoint:** `POST /auth/forgot-password`
* **Authentication:** None
* **Query Parameters:** `email` (string)
* **Success Response (200 OK):**
  ```json
  {
    "success": true,
    "data": null,
    "message": "If the email exists, a password reset link has been sent."
  }
  ```

---

## 👤 Users Router (`/users`)

Endpoints for retrieving and managing student profile metrics and interests.

### 1. Get User Profile
* **Endpoint:** `GET /users/profile`
* **Authentication:** Bearer JWT Token
* **Success Response (200 OK):**
  ```json
  {
    "success": true,
    "data": {
      "id": "e83b879f-689b-4395-88f5-4672e61df3f7",
      "email": "student@example.com",
      "full_name": "Jane Doe",
      "role": "student",
      "bio": "Studying software engineering",
      "avatar_url": "https://example.com/avatar.png",
      "interests": ["Python", "Machine Learning"]
    },
    "message": "User profile fetched successfully"
  }
  ```

### 2. Update User Profile
* **Endpoint:** `PUT /users/profile`
* **Authentication:** Bearer JWT Token
* **Request Body:**
  ```json
  {
    "full_name": "Jane Smith",
    "bio": "Aspiring AI Researcher",
    "avatar_url": "https://example.com/new-avatar.png"
  }
  ```
* **Success Response (200 OK):** Profile wrapper containing the updated fields.

### 3. Complete Onboarding
* **Endpoint:** `POST /users/onboarding`
* **Authentication:** Bearer JWT Token
* **Request Body:**
  ```json
  {
    "interests": ["Data Science", "LangGraph"]
  }
  ```
* **Success Response (200 OK):** Updated user profile object showing the onboarded flag.

---

## 📚 Courses Router (`/courses`)

Catalog searches, course outlines, lessons, and enrollment endpoints.

### 1. List Courses (Catalog)
* **Endpoint:** `GET /courses`
* **Authentication:** None
* **Query Parameters:**
  * `search` (Optional text search)
  * `difficulty` (Optional level: e.g. "Beginner", "Intermediate", "Advanced")
* **Success Response (200 OK):** List of courses matching criteria.

### 2. Get Enrolled Courses
* **Endpoint:** `GET /courses/enrolled`
* **Authentication:** Bearer JWT Token
* **Success Response (200 OK):**
  ```json
  {
    "success": true,
    "data": [
      {
        "id": "c1a2e3f4-d5e6-4a7b-8c9d-0e1f2a3b4c5d",
        "title": "Introduction to Python",
        "description": "Learn the basics of Python programming.",
        "difficulty": "Beginner",
        "duration": "8 hours",
        "progress": 45.5,
        "lastActive": "Recently"
      }
    ],
    "message": "Enrolled courses fetched successfully"
  }
  ```

### 3. Get Specific Course Details
* **Endpoint:** `GET /courses/{course_id}`
* **Authentication:** Bearer JWT Token
* **Success Response (200 OK):**
  ```json
  {
    "success": true,
    "data": {
      "id": "c1a2e3f4-d5e6-4a7b-8c9d-0e1f2a3b4c5d",
      "title": "Introduction to Python",
      "description": "Learn Python basics",
      "difficulty": "Beginner",
      "duration": "8 hours",
      "lessons": [
        {
          "id": "d1a2e3f4-d5e6-4a7b-8c9d-0e1f2a3b4c5d",
          "title": "Variables and Basic Types",
          "content": "Variables represent memory space...",
          "order": 1,
          "duration": 45,
          "completed": true
        }
      ]
    },
    "message": "Course details fetched successfully"
  }
  ```

### 4. Enroll in a Course
* **Endpoint:** `POST /courses/{course_id}/enroll`
* **Authentication:** Bearer JWT Token
* **Success Response (200 OK):**
  ```json
  {
    "success": true,
    "data": true,
    "message": "Enrolled in course successfully"
  }
  ```

### 5. Create Course (Admin Only)
* **Endpoint:** `POST /courses`
* **Authentication:** Bearer JWT Token
* **Request Body:** Standard `CourseCreate` schema.

### 6. Create Lesson (Admin Only)
* **Endpoint:** `POST /courses/{course_id}/lessons`
* **Authentication:** Bearer JWT Token
* **Request Body:** Standard `LessonCreate` schema.

---

## 📈 Progress Tracker Router (`/progress`)

Record lesson progress milestones and retrieve cumulative study durations.

### 1. Track Lesson Progress
* **Endpoint:** `POST /progress/lessons/{lesson_id}`
* **Authentication:** Bearer JWT Token
* **Request Body:**
  ```json
  {
    "completed": true,
    "time_spent": 1200
  }
  ```
* **Success Response (200 OK):**
  ```json
  {
    "success": true,
    "data": {
      "id": "f83b879f-689b-4395-88f5-4672e61df3f7",
      "user_id": "e83b879f-689b-4395-88f5-4672e61df3f7",
      "lesson_id": "d1a2e3f4-d5e6-4a7b-8c9d-0e1f2a3b4c5d",
      "completed": true,
      "time_spent": 1200,
      "updated_at": "2026-06-23T12:20:00Z"
    },
    "message": "Lesson progress saved successfully"
  }
  ```

### 2. Get Weekly Progress
* **Endpoint:** `GET /progress/weekly`
* **Authentication:** Bearer JWT Token
* **Success Response (200 OK):** Cumulative study hours per day for the last 7 days.
  ```json
  {
    "success": true,
    "data": [
      { "day": "Mon", "hours": 1.2 },
      { "day": "Tue", "hours": 0.8 },
      { "day": "Wed", "hours": 2.0 },
      { "day": "Thu", "hours": 0.0 },
      { "day": "Fri", "hours": 1.5 },
      { "day": "Sat", "hours": 0.5 },
      { "day": "Sun", "hours": 1.0 }
    ],
    "message": "Weekly progress fetched successfully"
  }
  ```

### 3. Get Course Progress Status
* **Endpoint:** `GET /progress/courses/{course_id}`
* **Authentication:** Bearer JWT Token
* **Success Response (200 OK):**
  ```json
  {
    "success": true,
    "data": {
      "id": "a83b879f-689b-4395-88f5-4672e61df3f7",
      "user_id": "e83b879f-689b-4395-88f5-4672e61df3f7",
      "course_id": "c1a2e3f4-d5e6-4a7b-8c9d-0e1f2a3b4c5d",
      "percentage": 100.0,
      "status": "completed"
    },
    "message": "Course progress fetched successfully"
  }
  ```

---

## 📝 Quizzes Router (`/quizzes` / `/courses`)

Retrieve course quizzes, submit scores, and retrieve submission histories.

### 1. Get Course Quiz
* **Endpoint:** `GET /courses/{course_id}/quiz`
* **Authentication:** None
* **Success Response (200 OK):** Course practice quiz questions list.

### 2. Get Specific Quiz
* **Endpoint:** `GET /quizzes/{quiz_id}`
* **Authentication:** None
* **Success Response (200 OK):**
  ```json
  {
    "success": true,
    "data": {
      "id": "b1a2e3f4-d5e6-4a7b-8c9d-0e1f2a3b4c5d",
      "course_id": "c1a2e3f4-d5e6-4a7b-8c9d-0e1f2a3b4c5d",
      "title": "Python Control Flow Quiz",
      "questions": [
        {
          "id": "q1",
          "question": "What is the output of `print(2 ** 3)`?",
          "options": ["6", "8", "9", "Error"],
          "correct_answer": "8",
          "explanation": "Double star exponentiation"
        }
      ]
    },
    "message": "Quiz questions loaded successfully"
  }
  ```

### 3. Submit Quiz for Grading
* **Endpoint:** `POST /quizzes/{quiz_id}/submit`
* **Authentication:** Bearer JWT Token
* **Request Body:**
  ```json
  {
    "answers": {
      "q1": "8"
    }
  }
  ```
* **Success Response (200 OK):**
  ```json
  {
    "success": true,
    "data": {
      "id": "s83b879f-689b-4395-88f5-4672e61df3f7",
      "user_id": "e83b879f-689b-4395-88f5-4672e61df3f7",
      "quiz_id": "b1a2e3f4-d5e6-4a7b-8c9d-0e1f2a3b4c5d",
      "score": 100.0,
      "answers": { "q1": "8" },
      "created_at": "2026-06-23T12:30:00Z"
    },
    "message": "Quiz graded and submitted successfully"
  }
  ```

### 4. Get Quiz Submissions History
* **Endpoint:** `GET /quizzes/{quiz_id}/submissions`
* **Authentication:** Bearer JWT Token
* **Success Response (200 OK):** List of past submissions and scores.

---

## 🧠 AI & GenAI Router (`/ai`)

Dynamic AI-driven concepts maps, study plans, quizzes, and SSE chat streams.

### 1. Dynamic Quiz Generation (GPT-4)
* **Endpoint:** `POST /ai/generate-quiz`
* **Authentication:** Bearer JWT Token
* **Request Body:**
  ```json
  {
    "lesson_id": "d1a2e3f4-d5e6-4a7b-8c9d-0e1f2a3b4c5d",
    "difficulty": "Intermediate",
    "num_questions": 5
  }
  ```
* **Success Response (200 OK):**
  ```json
  {
    "success": true,
    "data": {
      "quiz_title": "Intermediate Python Data Structures Quiz",
      "difficulty": "Intermediate",
      "questions": [
        {
          "id": "ai_q_1",
          "type": "multiple_choice",
          "question": "Which of the following is mutable in Python?",
          "options": ["List", "Tuple", "String", "Int"],
          "correct_answer": "List",
          "explanation": "Lists can be modified in-place."
        }
      ]
    },
    "message": "Quiz generated successfully"
  }
  ```

### 2. Adaptive Study Plan Generator
* **Endpoint:** `POST /ai/study-plan`
* **Authentication:** Bearer JWT Token
* **Request Body:**
  ```json
  {
    "user_id": "e83b879f-689b-4395-88f5-4672e61df3f7"
  }
  ```
* **Success Response (200 OK):**
  ```json
  {
    "success": true,
    "data": {
      "week_goal": "Master Python fundamentals and solve control flow edge cases.",
      "daily_plans": [
        {
          "day": "Day 1",
          "tasks": [
            {
              "time": "Morning",
              "activity": "Review variables and syntax basics",
              "resource": "Python Basics Lesson",
              "duration_mins": 30
            }
          ]
        }
      ]
    },
    "message": "AI study plan generated successfully"
  }
  ```

### 3. Concept Map Network Generator
* **Endpoint:** `POST /ai/concept-map`
* **Authentication:** Bearer JWT Token
* **Request Body:**
  ```json
  {
    "topic": "Neural Networks"
  }
  ```
* **Success Response (200 OK):** Returns nodes and edges to be consumed by the frontend canvas (React Flow):
  ```json
  {
    "success": true,
    "data": {
      "nodes": [
        { "id": "1", "label": "Neural Networks", "type": "core" },
        { "id": "2", "label": "Perceptron", "type": "subconcept" }
      ],
      "edges": [
        { "source": "1", "target": "2", "label": "basic building block" }
      ]
    },
    "message": "Concept map generated successfully"
  }
  ```

### 4. Answer Evaluation & Feedback
* **Endpoint:** `POST /ai/feedback`
* **Authentication:** Bearer JWT Token
* **Request Body:**
  ```json
  {
    "question": "What is the difference between a list and a tuple?",
    "student_answer": "Lists are mutable and use square brackets. Tuples are not mutable and use parenthesis.",
    "correct_answer": "Lists are mutable; tuples are immutable."
  }
  ```
* **Success Response (200 OK):**
  ```json
  {
    "success": true,
    "data": {
      "score": 9,
      "feedback": "Excellent definition of mutability differences.",
      "improvements": [
        "Mention memory allocation differences",
        "Describe typical use cases for each",
        "List syntax differences"
      ]
    },
    "message": "Feedback generated successfully"
  }
  ```

### 5. SSE AI Chat Stream (LangGraph Cognitive Graph)
* **Endpoint:** `POST /ai/chat?course_id={course_id}`
* **Authentication:** Bearer JWT Token
* **Query Parameters:** `course_id` (UUID)
* **Request Body:**
  ```json
  {
    "message": "Explain how list comprehension works in Python."
  }
  ```
* **Response Header:** `Content-Type: text/event-stream`
* **Stream Events (Server-Sent Events):**
  * **Agent Start Event:** Emitted when a node begins processing.
    ```
    data: {"type": "agent_start", "agent": "orchestrator"}
    ```
  * **Token Generation Chunk:**
    ```
    data: {"type": "token", "content": "List"}
    ```
    ```
    data: {"type": "token", "content": " comprehension"}
    ```
  * **Agent End Event:**
    ```
    data: {"type": "agent_end", "agent": "tutor"}
    ```
  * **Interrupt Checkpoint (For Quiz Approvals):**
    ```
    data: {"type": "interrupt", "message": "Quiz review requested", "quiz_data": { ... }}
    ```

### 6. Course Recommendations
* **Endpoint:** `GET /ai/recommendations`
* **Authentication:** Bearer JWT Token
* **Success Response (200 OK):**
  ```json
  {
    "success": true,
    "data": {
      "recommendations": [
        {
          "id": "c2a2e3f4-d5e6-4a7b-8c9d-0e1f2a3b4c5d",
          "title": "Advanced Python Patterns",
          "description": "Deep-dive into decorators and metaclasses.",
          "duration": "10 hours",
          "difficulty": "Advanced"
        }
      ]
    },
    "message": "AI recommendations generated successfully"
  }
  ```
