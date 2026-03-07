import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { motion } from "framer-motion";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";
import { Plus, TrendingUp, DollarSign, Brain, AlertTriangle } from "lucide-react";
import { progressApi, type LogMetricData } from "@/lib/api";
import { useAuthStore } from "@/stores/authStore";

export default function Progress() {
  const userId = useAuthStore((s) => s.userId!);
  const queryClient = useQueryClient();
  const [showLog, setShowLog] = useState(false);

  const { data: metrics } = useQuery({
    queryKey: ["progress", userId],
    queryFn: () => progressApi.list(userId, 30),
  });

  const { data: summary } = useQuery({
    queryKey: ["progress-summary", userId],
    queryFn: () => progressApi.summary(userId),
  });

  const logMutation = useMutation({
    mutationFn: (data: LogMetricData) => progressApi.log(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["progress"] });
      queryClient.invalidateQueries({ queryKey: ["progress-summary"] });
      setShowLog(false);
    },
  });

  // Reverse for chronological order in chart
  const chartData = [...(metrics || [])].reverse().map((m) => ({
    date: m.metric_date.slice(5), // "02-24"
    motivation: m.motivation_level,
    actions: m.monetization_actions,
    avoidance: m.avoidance_episodes,
  }));

  return (
    <div className="px-4 pt-6">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-xl font-semibold">Прогресс</h1>
        <button
          onClick={() => setShowLog(!showLog)}
          className="btn-primary flex items-center gap-1.5 text-sm"
        >
          <Plus size={16} />
          Записать
        </button>
      </div>

      {/* Log form */}
      {showLog && (
        <LogForm
          onSubmit={(data) => logMutation.mutate({ user_id: userId, ...data })}
          isPending={logMutation.isPending}
        />
      )}

      {/* Summary cards */}
      {summary && (
        <div className="grid grid-cols-2 gap-3 mb-6">
          <SummaryCard
            icon={<TrendingUp size={18} className="text-meridian-500" />}
            label="Мотивация (средняя)"
            value={String(summary.avg_motivation)}
          />
          <SummaryCard
            icon={<DollarSign size={18} className="text-green-500" />}
            label="Доход (всего)"
            value={`${summary.total_revenue.toFixed(0)}₽`}
          />
          <SummaryCard
            icon={<Brain size={18} className="text-warmth-500" />}
            label="Действий"
            value={String(summary.total_monetization_actions)}
          />
          <SummaryCard
            icon={<AlertTriangle size={18} className="text-red-400" />}
            label="Избеганий"
            value={String(summary.total_avoidance_episodes)}
          />
        </div>
      )}

      {/* Chart */}
      {chartData.length > 1 && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="card p-4 mb-4"
        >
          <h3 className="font-medium text-sm mb-3">Мотивация и действия</h3>
          <ResponsiveContainer width="100%" height={200}>
            <LineChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#ebeef5" />
              <XAxis dataKey="date" tick={{ fontSize: 11 }} />
              <YAxis tick={{ fontSize: 11 }} domain={[0, 10]} />
              <Tooltip />
              <Line
                type="monotone"
                dataKey="motivation"
                stroke="#0c7deb"
                strokeWidth={2}
                dot={{ r: 3 }}
                name="Мотивация"
              />
              <Line
                type="monotone"
                dataKey="actions"
                stroke="#df7a26"
                strokeWidth={2}
                dot={{ r: 3 }}
                name="Действия"
              />
            </LineChart>
          </ResponsiveContainer>
        </motion.div>
      )}

      {chartData.length <= 1 && (
        <div className="text-center py-12 text-ink-muted">
          <TrendingUp size={48} className="mx-auto mb-4 opacity-30" />
          <p>Недостаточно данных для графика</p>
          <p className="text-sm mt-1">Записывайте метрики каждый день</p>
        </div>
      )}
    </div>
  );
}

function SummaryCard({
  icon,
  label,
  value,
}: {
  icon: React.ReactNode;
  label: string;
  value: string;
}) {
  return (
    <div className="card p-3">
      <div className="mb-1">{icon}</div>
      <p className="text-lg font-semibold">{value}</p>
      <p className="text-[11px] text-ink-muted">{label}</p>
    </div>
  );
}

function LogForm({
  onSubmit,
  isPending,
}: {
  onSubmit: (data: Partial<LogMetricData>) => void;
  isPending: boolean;
}) {
  const [form, setForm] = useState({
    motivation_level: 5,
    monetization_actions: 0,
    revenue_today: 0,
    avoidance_episodes: 0,
    journal_entry: "",
  });

  const set = (key: string, value: number | string) =>
    setForm((f) => ({ ...f, [key]: value }));

  return (
    <motion.div
      initial={{ opacity: 0, height: 0 }}
      animate={{ opacity: 1, height: "auto" }}
      className="card p-4 mb-4 overflow-hidden"
    >
      <h3 className="font-medium text-sm mb-3">Записать за сегодня</h3>

      <div className="space-y-3">
        <div>
          <label className="text-xs text-ink-muted block mb-1">
            Мотивация (1-10): {form.motivation_level}
          </label>
          <input
            type="range"
            min={1}
            max={10}
            value={form.motivation_level}
            onChange={(e) => set("motivation_level", Number(e.target.value))}
            className="w-full"
          />
        </div>

        <div className="grid grid-cols-2 gap-3">
          <div>
            <label className="text-xs text-ink-muted block mb-1">
              Действий по монетизации
            </label>
            <input
              type="number"
              min={0}
              value={form.monetization_actions}
              onChange={(e) =>
                set("monetization_actions", Number(e.target.value))
              }
              className="input text-sm"
            />
          </div>
          <div>
            <label className="text-xs text-ink-muted block mb-1">
              Доход сегодня (₽)
            </label>
            <input
              type="number"
              min={0}
              value={form.revenue_today}
              onChange={(e) => set("revenue_today", Number(e.target.value))}
              className="input text-sm"
            />
          </div>
        </div>

        <div>
          <label className="text-xs text-ink-muted block mb-1">
            Эпизодов избегания
          </label>
          <input
            type="number"
            min={0}
            value={form.avoidance_episodes}
            onChange={(e) =>
              set("avoidance_episodes", Number(e.target.value))
            }
            className="input text-sm"
          />
        </div>

        <div>
          <label className="text-xs text-ink-muted block mb-1">
            Дневник (необязательно)
          </label>
          <textarea
            value={form.journal_entry}
            onChange={(e) => set("journal_entry", e.target.value)}
            className="input text-sm"
            rows={2}
            placeholder="Как прошёл день?"
          />
        </div>

        <button
          onClick={() => onSubmit(form)}
          disabled={isPending}
          className="btn-primary w-full text-sm"
        >
          {isPending ? "Сохраняю..." : "Сохранить"}
        </button>
      </div>
    </motion.div>
  );
}
