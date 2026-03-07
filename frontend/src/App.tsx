import { useEffect } from "react";
import { Routes, Route, Navigate } from "react-router-dom";
import { useAuthStore } from "@/stores/authStore";
import Dashboard from "@/pages/Dashboard";
import Tasks from "@/pages/Tasks";
import Progress from "@/pages/Progress";
import AssessmentPage from "@/pages/Assessment";
import Navigation from "@/components/Navigation";

export default function App() {
  const { token, isLoading, initTelegram } = useAuthStore();

  useEffect(() => {
    initTelegram();
  }, [initTelegram]);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="w-8 h-8 border-2 border-meridian-400 border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  if (!token) {
    return (
      <div className="flex items-center justify-center min-h-screen px-6 text-center">
        <div>
          <p className="text-lg font-medium text-ink-primary mb-2">
            Откройте через Telegram
          </p>
          <p className="text-sm text-ink-muted">
            Этот дашборд работает как Mini App внутри Telegram бота.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col min-h-screen">
      <main className="flex-1 pb-20">
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/tasks" element={<Tasks />} />
          <Route path="/progress" element={<Progress />} />
          <Route path="/assessment/:type" element={<AssessmentPage />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </main>
      <Navigation />
    </div>
  );
}
