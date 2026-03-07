import { useQuery } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import {
  MessageCircle,
  ClipboardList,
  TrendingUp,
  Brain,
  ArrowRight,
} from "lucide-react";
import { insightsApi } from "@/lib/api";
import { useAuthStore } from "@/stores/authStore";

export default function Dashboard() {
  const userId = useAuthStore((s) => s.userId!);
  const navigate = useNavigate();

  const { data, isLoading } = useQuery({
    queryKey: ["dashboard", userId],
    queryFn: () => insightsApi.dashboard(userId),
  });

  if (isLoading) {
    return (
      <div className="flex justify-center py-20">
        <div className="w-6 h-6 border-2 border-meridian-400 border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  const user = data?.user;
  const sessions = data?.sessions;
  const tasks = data?.tasks;
  const metric = data?.latest_metric;

  const phaseLabels: Record<string, string> = {
    assessment: "Оценка",
    early_intervention: "Начало работы",
    active_work: "Активная работа",
    maintenance: "Поддержка",
  };

  return (
    <div className="px-4 pt-6 pb-4">
      {/* Greeting */}
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        className="mb-6"
      >
        <h1 className="text-2xl font-semibold">
          {getGreeting()}, {user?.display_name || "User"}
        </h1>
        <p className="text-ink-muted text-sm mt-1">
          {sessions?.total_completed
            ? `${sessions.total_completed} сессий пройдено`
            : "Начните первую сессию"}
          {user?.therapy_phase && (
            <span> — фаза: {phaseLabels[user.therapy_phase] || user.therapy_phase}</span>
          )}
        </p>
      </motion.div>

      {/* Quick actions */}
      <div className="grid grid-cols-2 gap-3 mb-4">
        <motion.button
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          onClick={() => navigate("/assessment/kmsi")}
          className="card p-4 text-left hover:border-meridian-300 transition-colors"
        >
          <Brain size={20} className="text-meridian-500 mb-2" />
          <h3 className="font-medium text-sm">Тест KMSI</h3>
          <p className="text-xs text-ink-muted mt-0.5">Денежные скрипты</p>
        </motion.button>

        <motion.button
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.12 }}
          onClick={() => navigate("/assessment/self_sabotage")}
          className="card p-4 text-left hover:border-meridian-300 transition-colors"
        >
          <MessageCircle size={20} className="text-warmth-500 mb-2" />
          <h3 className="font-medium text-sm">Самосаботаж</h3>
          <p className="text-xs text-ink-muted mt-0.5">7 индикаторов</p>
        </motion.button>
      </div>

      {/* Stats grid */}
      <div className="grid grid-cols-2 gap-3 mb-4">
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.15 }}
          onClick={() => navigate("/tasks")}
          className="card p-4 cursor-pointer hover:border-meridian-300 transition-colors"
        >
          <ClipboardList size={20} className="text-warmth-500 mb-2" />
          <p className="text-2xl font-semibold">{tasks?.pending || 0}</p>
          <p className="text-xs text-ink-muted">заданий ожидают</p>
          {tasks?.completed ? (
            <p className="text-xs text-green-600 mt-1">
              {tasks.completed} выполнено
            </p>
          ) : null}
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          onClick={() => navigate("/progress")}
          className="card p-4 cursor-pointer hover:border-meridian-300 transition-colors"
        >
          <TrendingUp size={20} className="text-meridian-500 mb-2" />
          <p className="text-2xl font-semibold">
            {metric?.motivation || "—"}
          </p>
          <p className="text-xs text-ink-muted">мотивация сегодня</p>
          {metric?.monetization_actions ? (
            <p className="text-xs text-meridian-600 mt-1">
              {metric.monetization_actions} действий
            </p>
          ) : null}
        </motion.div>
      </div>

      {/* Money scripts summary */}
      {user?.money_scripts && hasAnyScore(user.money_scripts) && (
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.25 }}
          className="card p-4 mb-4"
        >
          <div className="flex items-center gap-2 mb-3">
            <Brain size={18} className="text-warmth-500" />
            <h3 className="font-medium text-sm">Денежные скрипты</h3>
          </div>
          <div className="space-y-2">
            {Object.entries(SCRIPT_LABELS).map(([key, label]) => {
              const score = user.money_scripts[key as keyof typeof user.money_scripts];
              if (!score) return null;
              return (
                <div key={key} className="flex items-center gap-3">
                  <span className="text-xs text-ink-muted w-24">{label}</span>
                  <div className="flex-1 h-2 bg-surface-tertiary rounded-full overflow-hidden">
                    <div
                      className="h-full bg-meridian-400 rounded-full transition-all"
                      style={{ width: `${(score / 5) * 100}%` }}
                    />
                  </div>
                  <span className="text-xs font-medium w-8 text-right">
                    {score.toFixed(1)}
                  </span>
                </div>
              );
            })}
          </div>
        </motion.div>
      )}

      {/* Last session summary */}
      {sessions?.last_session?.summary && (
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
          className="card p-4"
        >
          <h3 className="font-medium text-sm mb-2">Последняя сессия</h3>
          <p className="text-sm text-ink-secondary line-clamp-4">
            {sessions.last_session.summary}
          </p>
        </motion.div>
      )}
    </div>
  );
}

const SCRIPT_LABELS: Record<string, string> = {
  avoidance: "Избегание",
  worship: "Поклонение",
  status: "Статус",
  vigilance: "Бдительность",
};

function hasAnyScore(scripts: Record<string, number | undefined | null>): boolean {
  return Object.values(scripts).some((v) => v != null && v > 0);
}

function getGreeting(): string {
  const h = new Date().getHours();
  if (h < 6) return "Доброй ночи";
  if (h < 12) return "Доброе утро";
  if (h < 18) return "Добрый день";
  return "Добрый вечер";
}
