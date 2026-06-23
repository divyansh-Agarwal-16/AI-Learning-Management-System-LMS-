import axios from "axios";
import { getSession, signOut } from "next-auth/react";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

export const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    "Content-Type": "application/json",
  },
});

// Request Interceptor: Attach JWT bearer token from next-auth session
api.interceptors.request.use(
  async (config) => {
    // 1. Check localStorage first for instant availability during client transitions
    let token = typeof window !== "undefined" ? localStorage.getItem("accessToken") : null;
    
    // 2. Fall back to NextAuth session
    if (!token) {
      const session = await getSession();
      if (session?.user && (session.user as any).accessToken) {
        token = (session.user as any).accessToken;
        if (typeof window !== "undefined") {
          localStorage.setItem("accessToken", token!);
        }
      }
    }

    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response Interceptor: Handle 401 failures by renewing tokens silently
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;
    
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;
      try {
        const session = await getSession();
        const refreshTokenVal = session 
          ? (session.user as any).refreshToken 
          : (typeof window !== "undefined" ? localStorage.getItem("refreshToken") : null);

        if (refreshTokenVal) {
          const res = await axios.post(`${API_BASE_URL}/auth/refresh?refresh_token=${refreshTokenVal}`);
          if (res.status === 200 && res.data.success) {
            const { access_token, refresh_token } = res.data.data;
            
            if (typeof window !== "undefined") {
              localStorage.setItem("accessToken", access_token);
              localStorage.setItem("refreshToken", refresh_token);
            }
            
            // Re-execute initial request with new token
            originalRequest.headers.Authorization = `Bearer ${access_token}`;
            return api(originalRequest);
          }
        }
      } catch (refreshErr) {
        console.error("Token refresh failed:", refreshErr);
      }
      
      // Clean tokens and force redirect to login
      if (typeof window !== "undefined") {
        localStorage.removeItem("accessToken");
        localStorage.removeItem("refreshToken");
        signOut({ callbackUrl: "/login" });
      }
    }
    return Promise.reject(error);
  }
);

// --- TYPED API ENDPOINTS ---

export interface ApiResponse<T = any> {
  success: boolean;
  data: T;
  message: string;
}

// 1. Auth Services
export const authApi = {
  login: async (email: string, password: string) => {
    const res = await api.post<ApiResponse>("/auth/login", { email, password });
    return res.data;
  },
  signup: async (email: string, password: string, fullName: string) => {
    const res = await api.post<ApiResponse>("/auth/signup", { email, password, full_name: fullName });
    return res.data;
  },
  logout: async () => {
    if (typeof window !== "undefined") {
      localStorage.removeItem("accessToken");
      localStorage.removeItem("refreshToken");
    }
    await signOut({ callbackUrl: "/" });
  },
  refreshToken: async (refreshTokenVal: string) => {
    const res = await axios.post<ApiResponse>(`${API_BASE_URL}/auth/refresh?refresh_token=${refreshTokenVal}`);
    return res.data;
  }
};

// 2. Courses Services
export interface Course {
  id: string;
  title: string;
  description: string;
  difficulty: "Beginner" | "Intermediate" | "Advanced";
  topic: string;
  duration: string;
  enrolled?: boolean;
  progress?: number;
  thumbnail?: string;
  lessons?: Lesson[];
}

export interface Lesson {
  id: string;
  title: string;
  duration: string;
  completed: boolean;
  videoUrl: string;
  pdfUrl?: string;
}

export const coursesApi = {
  getCourses: async (search?: string, difficulty?: string) => {
    const params: Record<string, string> = {};
    if (search) params.search = search;
    if (difficulty && difficulty !== "All") params.difficulty = difficulty;
    const res = await api.get<ApiResponse<Course[]>>("/courses", { params });
    return res.data;
  },
  getCourse: async (id: string) => {
    const res = await api.get<ApiResponse<Course>>(`/courses/${id}`);
    return res.data;
  },
  enrollCourse: async (id: string) => {
    const res = await api.post<ApiResponse<boolean>>(`/courses/${id}/enroll`);
    return res.data;
  },
  getEnrolledCourses: async () => {
    const res = await api.get<ApiResponse<Course[]>>("/courses/enrolled");
    return res.data;
  }
};

// 3. AI Services
export interface QuizQuestionItem {
  id: string;
  type: string;
  question: string;
  options: string[];
  correct_answer: string;
  explanation: string;
}

export interface GenerateQuizResponse {
  quiz_title: string;
  difficulty: string;
  questions: QuizQuestionItem[];
}

export interface StudyTask {
  time: string;
  activity: string;
  resource: string;
  duration_mins: number;
}

export interface DailyStudyPlan {
  day: string;
  tasks: StudyTask[];
}

export interface StudyPlanResponse {
  week_goal: string;
  daily_plans: DailyStudyPlan[];
}

export interface ConceptNode {
  id: string;
  label: string;
  type: string;
}

export interface ConceptEdge {
  source: string;
  target: string;
  label: string;
}

export interface ConceptMapResponse {
  nodes: ConceptNode[];
  edges: ConceptEdge[];
}

export interface AnswerFeedbackResponse {
  score: number;
  feedback: string;
  improvements: string[];
}

export const aiApi = {
  generateQuiz: async (lessonId: string, difficulty: string, numQuestions: number = 5) => {
    const res = await api.post<ApiResponse<GenerateQuizResponse>>("/ai/generate-quiz", {
      lesson_id: lessonId,
      difficulty,
      num_questions: numQuestions,
    });
    return res.data;
  },
  getStudyPlan: async (userId: string) => {
    const res = await api.post<ApiResponse<StudyPlanResponse>>("/ai/study-plan", {
      user_id: userId,
    });
    return res.data;
  },
  getConceptMap: async (topic: string) => {
    const res = await api.post<ApiResponse<ConceptMapResponse>>("/ai/concept-map", {
      topic,
    });
    return res.data;
  },
  getAnswerFeedback: async (question: string, studentAnswer: string, correctAnswer: string) => {
    const res = await api.post<ApiResponse<AnswerFeedbackResponse>>("/ai/feedback", {
      question,
      student_answer: studentAnswer,
      correct_answer: correctAnswer,
    });
    return res.data;
  },
  getRecommendations: async () => {
    const res = await api.get<ApiResponse<{ recommendations: any[] }>>("/ai/recommendations");
    return res.data;
  }
};

// 4. Progress Services
export interface LessonProgress {
  id: string;
  user_id: string;
  lesson_id: string;
  completed: boolean;
  time_spent: number;
}

export interface CourseProgress {
  id: string;
  user_id: string;
  course_id: string;
  percentage: number;
  status: string;
}

export interface WeeklyStudyHours {
  day: string;
  hours: number;
}

export const progressApi = {
  updateProgress: async (lessonId: string, completed: boolean, timeSpent: number) => {
    const res = await api.post<ApiResponse<LessonProgress>>(`/progress/lessons/${lessonId}`, {
      completed,
      time_spent: timeSpent,
    });
    return res.data;
  },
  getProgress: async (courseId: string) => {
    const res = await api.get<ApiResponse<CourseProgress>>(`/progress/courses/${courseId}`);
    return res.data;
  },
  getWeeklyProgress: async () => {
    const res = await api.get<ApiResponse<WeeklyStudyHours[]>>("/progress/weekly");
    return res.data;
  }
};

// 5. Quizzes Services
export interface Quiz {
  id: string;
  course_id: string;
  title: string;
  questions: {
    id: string;
    text: string;
    options: string[];
  }[];
}

export interface SubmissionDetail {
  question_id: string;
  selected_option_idx: number;
  correct_option_idx: number;
  is_correct: boolean;
  question_text: string;
  correct_answer_text: string;
  selected_answer_text: string;
}

export interface SubmissionResponse {
  id: string;
  quiz_id: string;
  score: number;
  total_questions: number;
  submitted_at: string;
  details: SubmissionDetail[];
}

export const quizzesApi = {
  getQuizByCourse: async (courseId: string) => {
    const res = await api.get<ApiResponse<Quiz>>(`/courses/${courseId}/quiz`);
    return res.data;
  },
  getQuiz: async (quizId: string) => {
    const res = await api.get<ApiResponse<Quiz>>(`/quizzes/${quizId}`);
    return res.data;
  },
  submitQuiz: async (quizId: string, answers: { question_id: string; selected_option_idx: number }[]) => {
    const res = await api.post<ApiResponse<SubmissionResponse>>(`/quizzes/${quizId}/submit`, {
      answers,
    });
    return res.data;
  }
};
