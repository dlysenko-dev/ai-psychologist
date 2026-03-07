/**
 * API client for AI Psychologist backend
 */
const API_BASE = "/api/v1";

async function request<T>(
  path: string,
  options?: RequestInit
): Promise<T> {
  const token = localStorage.getItem("psych_token");
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
  };
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  const res = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers: { ...headers, ...options?.headers },
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || `HTTP ${res.status}`);
  }

  return res.json();
}

// Auth
export const authApi = {
  telegramAuth: (initData: string) =>
    request<{ token: string; user_id: number; display_name: string }>(
      "/auth/telegram",
      {
        method: "POST",
        body: JSON.stringify({ init_data: initData }),
      }
    ),
};

// Sessions
export const sessionsApi = {
  list: (userId: number) =>
    request<SessionSummary[]>(`/sessions?user_id=${userId}`),
  create: (userId: number) =>
    request<SessionSummary>("/sessions", {
      method: "POST",
      body: JSON.stringify({ user_id: userId }),
    }),
  get: (sessionId: number) =>
    request<{ session: SessionSummary; messages: Message[] }>(
      `/sessions/${sessionId}`
    ),
  sendMessage: (sessionId: number, userId: number, content: string) =>
    request<MessageResponse>(`/sessions/${sessionId}/message`, {
      method: "POST",
      body: JSON.stringify({ user_id: userId, content }),
    }),
  complete: (sessionId: number) =>
    request<{ summary: string; duration_minutes: number }>(
      `/sessions/${sessionId}/complete`,
      { method: "POST" }
    ),
};

// Tasks
export const tasksApi = {
  list: (userId: number, status?: string) => {
    const params = new URLSearchParams({ user_id: String(userId) });
    if (status) params.set("status", status);
    return request<Task[]>(`/tasks?${params}`);
  },
  complete: (taskId: number, reflection?: string) =>
    request<{ status: string }>(`/tasks/${taskId}/complete`, {
      method: "POST",
      body: JSON.stringify({ reflection: reflection || "" }),
    }),
  skip: (taskId: number) =>
    request<{ status: string }>(`/tasks/${taskId}/skip`, {
      method: "POST",
    }),
};

// Progress
export const progressApi = {
  list: (userId: number, days?: number) =>
    request<ProgressMetric[]>(
      `/progress?user_id=${userId}${days ? `&days=${days}` : ""}`
    ),
  log: (data: LogMetricData) =>
    request<ProgressMetric>("/progress", {
      method: "POST",
      body: JSON.stringify(data),
    }),
  summary: (userId: number) =>
    request<ProgressSummary>(`/progress/summary?user_id=${userId}`),
};

// Assessments
export const assessmentsApi = {
  list: (userId: number) =>
    request<Assessment[]>(`/assessments?user_id=${userId}`),
  start: (userId: number, type: string) =>
    request<Assessment>("/assessments", {
      method: "POST",
      body: JSON.stringify({ user_id: userId, assessment_type: type }),
    }),
  submit: (assessmentId: number, answers: Record<string, number | string>) =>
    request<Assessment>(`/assessments/${assessmentId}/submit`, {
      method: "POST",
      body: JSON.stringify({ answers }),
    }),
  get: (assessmentId: number) =>
    request<Assessment>(`/assessments/${assessmentId}`),
};

// Insights
export const insightsApi = {
  dashboard: (userId: number) =>
    request<DashboardData>(`/insights/dashboard?user_id=${userId}`),
  patterns: (userId: number) =>
    request<PatternsData>(`/insights/patterns?user_id=${userId}`),
};

// Types
export interface SessionSummary {
  id: number;
  session_number: number;
  session_type: string;
  status: string;
  summary?: string;
  duration_minutes?: number;
}

export interface Message {
  id: number;
  role: "user" | "therapist";
  content: string;
  crisis_flag?: boolean;
}

export interface MessageResponse {
  message_id: number;
  content: string;
  crisis_detected: boolean;
  model_used: string;
}

export interface Task {
  id: number;
  title: string;
  description: string;
  task_type: string;
  difficulty: number;
  status: string;
  reflection?: string;
}

export interface ProgressMetric {
  id: number;
  metric_date: string;
  monetization_actions?: number;
  belief_shift?: number;
  emotional_regulation?: number;
  motivation_level?: number;
  revenue_today?: number;
  new_projects_started?: number;
  projects_abandoned?: number;
  avoidance_episodes?: number;
  journal_entry?: string;
}

export interface LogMetricData {
  user_id: number;
  metric_date?: string;
  monetization_actions?: number;
  belief_shift?: number;
  emotional_regulation?: number;
  motivation_level?: number;
  revenue_today?: number;
  new_projects_started?: number;
  projects_abandoned?: number;
  avoidance_episodes?: number;
  journal_entry?: string;
}

export interface ProgressSummary {
  total_days_tracked: number;
  total_monetization_actions: number;
  total_revenue: number;
  avg_motivation: number;
  avg_emotional_regulation: number;
  total_new_projects_started: number;
  total_avoidance_episodes: number;
}

export interface Assessment {
  id: number;
  assessment_type: string;
  status: string;
  scores?: Record<string, number | string>;
  interpretation?: string;
  recommendations?: Record<string, string>;
}

export interface DashboardData {
  user: {
    display_name: string;
    therapy_phase: string;
    preferred_methodology?: string;
    money_scripts: {
      avoidance?: number;
      worship?: number;
      status?: number;
      vigilance?: number;
    };
  };
  sessions: {
    total_completed: number;
    last_session?: {
      id: number;
      number: number;
      status: string;
      summary?: string;
    };
  };
  tasks: { pending: number; completed: number };
  latest_metric?: {
    date: string;
    motivation?: number;
    monetization_actions?: number;
    revenue?: number;
  };
}

export interface PatternsData {
  sessions: Array<{
    session_number: number;
    type: string;
    methodology?: string;
    summary?: string;
    key_insights?: string[];
    patterns?: string[];
    emotional_start?: number;
    emotional_end?: number;
  }>;
  metrics_trend: Array<{
    date: string;
    motivation?: number;
    monetization_actions?: number;
    avoidance_episodes?: number;
    revenue?: number;
  }>;
  trends: Record<string, string>;
  total_sessions: number;
}
