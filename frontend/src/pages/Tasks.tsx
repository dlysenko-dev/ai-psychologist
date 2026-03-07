import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { motion, AnimatePresence } from "framer-motion";
import { Check, X, ChevronDown, Star } from "lucide-react";
import { tasksApi, type Task } from "@/lib/api";
import { useAuthStore } from "@/stores/authStore";

export default function Tasks() {
  const userId = useAuthStore((s) => s.userId!);
  const queryClient = useQueryClient();
  const [filter, setFilter] = useState<string | undefined>(undefined);
  const [expandedId, setExpandedId] = useState<number | null>(null);
  const [reflection, setReflection] = useState("");

  const { data: tasks, isLoading } = useQuery({
    queryKey: ["tasks", userId, filter],
    queryFn: () => tasksApi.list(userId, filter),
  });

  const completeMutation = useMutation({
    mutationFn: ({ id, reflection }: { id: number; reflection: string }) =>
      tasksApi.complete(id, reflection),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["tasks"] });
      setExpandedId(null);
      setReflection("");
    },
  });

  const skipMutation = useMutation({
    mutationFn: (id: number) => tasksApi.skip(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["tasks"] }),
  });

  const filters = [
    { value: undefined, label: "Все" },
    { value: "pending", label: "Ожидают" },
    { value: "completed", label: "Выполнены" },
    { value: "skipped", label: "Пропущены" },
  ];

  const difficultyStars = (n: number) =>
    Array.from({ length: 5 }, (_, i) => (
      <Star
        key={i}
        size={12}
        className={i < n ? "text-warmth-400 fill-warmth-400" : "text-ink-light"}
      />
    ));

  return (
    <div className="px-4 pt-6">
      <h1 className="text-xl font-semibold mb-4">Задания</h1>

      {/* Filter chips */}
      <div className="flex gap-2 mb-5 overflow-x-auto">
        {filters.map((f) => (
          <button
            key={f.label}
            onClick={() => setFilter(f.value)}
            className={`px-3 py-1.5 rounded-full text-sm font-medium whitespace-nowrap transition-colors ${
              filter === f.value
                ? "bg-meridian-600 text-white"
                : "bg-surface-tertiary text-ink-secondary hover:bg-meridian-100"
            }`}
          >
            {f.label}
          </button>
        ))}
      </div>

      {isLoading && (
        <div className="flex justify-center py-12">
          <div className="w-6 h-6 border-2 border-meridian-400 border-t-transparent rounded-full animate-spin" />
        </div>
      )}

      {tasks && tasks.length === 0 && (
        <div className="text-center py-16 text-ink-muted">
          <p>Нет заданий</p>
          <p className="text-sm mt-1">Задания появятся после терапевтических сессий</p>
        </div>
      )}

      <div className="space-y-3">
        <AnimatePresence>
          {tasks?.map((task) => (
            <motion.div
              key={task.id}
              layout
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, height: 0 }}
              className="card overflow-hidden"
            >
              <div
                className="p-4 cursor-pointer"
                onClick={() =>
                  setExpandedId(expandedId === task.id ? null : task.id)
                }
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-2">
                      <StatusBadge status={task.status} />
                      <h3 className="font-medium text-sm">{task.title}</h3>
                    </div>
                    <p className="text-xs text-ink-muted mt-1">{task.task_type}</p>
                  </div>
                  <div className="flex items-center gap-1 ml-2">
                    {difficultyStars(task.difficulty)}
                  </div>
                </div>
                <ChevronDown
                  size={16}
                  className={`text-ink-light mt-1 transition-transform ${
                    expandedId === task.id ? "rotate-180" : ""
                  }`}
                />
              </div>

              <AnimatePresence>
                {expandedId === task.id && (
                  <motion.div
                    initial={{ height: 0 }}
                    animate={{ height: "auto" }}
                    exit={{ height: 0 }}
                    className="overflow-hidden"
                  >
                    <div className="px-4 pb-4 border-t border-surface-tertiary pt-3">
                      <p className="text-sm text-ink-secondary mb-3">
                        {task.description}
                      </p>

                      {task.status === "pending" && (
                        <>
                          <textarea
                            value={reflection}
                            onChange={(e) => setReflection(e.target.value)}
                            placeholder="Как прошло? Что заметили? (рефлексия)"
                            className="input text-sm mb-3"
                            rows={2}
                          />
                          <div className="flex gap-2">
                            <button
                              onClick={() =>
                                completeMutation.mutate({
                                  id: task.id,
                                  reflection,
                                })
                              }
                              disabled={completeMutation.isPending}
                              className="btn-primary flex-1 flex items-center justify-center gap-1.5 text-sm"
                            >
                              <Check size={16} />
                              Выполнено
                            </button>
                            <button
                              onClick={() => skipMutation.mutate(task.id)}
                              disabled={skipMutation.isPending}
                              className="btn-secondary px-4 text-sm"
                            >
                              <X size={16} />
                            </button>
                          </div>
                        </>
                      )}

                      {task.reflection && (
                        <div className="mt-2 p-3 bg-meridian-50 rounded-xl">
                          <p className="text-xs font-medium text-meridian-700 mb-1">
                            Рефлексия:
                          </p>
                          <p className="text-sm text-meridian-800">
                            {task.reflection}
                          </p>
                        </div>
                      )}
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>
            </motion.div>
          ))}
        </AnimatePresence>
      </div>
    </div>
  );
}

function StatusBadge({ status }: { status: string }) {
  const styles: Record<string, string> = {
    pending: "bg-warmth-100 text-warmth-700",
    completed: "bg-green-100 text-green-700",
    skipped: "bg-gray-100 text-gray-500",
  };
  const labels: Record<string, string> = {
    pending: "Ожидает",
    completed: "Выполнено",
    skipped: "Пропущено",
  };
  return (
    <span className={`text-[10px] px-2 py-0.5 rounded-full font-medium ${styles[status] || ""}`}>
      {labels[status] || status}
    </span>
  );
}
