import { useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { motion, AnimatePresence } from "framer-motion";
import { useMutation } from "@tanstack/react-query";
import { ArrowLeft, ArrowRight, Check } from "lucide-react";
import { assessmentsApi } from "@/lib/api";
import { useAuthStore } from "@/stores/authStore";

// KMSI-R simplified questions (Russian)
const KMSI_QUESTIONS = [
  "Деньги — это зло",
  "Богатые люди жадные",
  "Я не заслуживаю денег",
  "Деньги развращают людей",
  "Лучше не иметь лишних денег",
  "Деньги решат все мои проблемы",
  "Чем больше денег, тем лучше жизнь",
  "Никогда не бывает достаточно денег",
  "Богатство — главная жизненная цель",
  "Деньги дают свободу делать что хочешь",
  "Мой доход определяет мою ценность",
  "Люди уважают тех, у кого больше денег",
  "Я стыжусь своего финансового положения",
  "Успех измеряется деньгами",
  "Мне стыдно просить деньги за свою работу",
  "Нужно всегда знать, сколько у тебя денег",
  "Нельзя доверять другим в вопросах денег",
  "Важно иметь финансовую подушку",
  "Я тревожусь, когда трачу деньги",
  "О деньгах лучше не говорить с другими",
];

const SELF_SABOTAGE_QUESTIONS = [
  { text: "Перфекционизм: \"Это ещё не достаточно хорошо\"", label: "Перфекционизм" },
  { text: "Shiny Object: постоянно начинаю новые проекты", label: "Переключение" },
  { text: "Синдром самозванца: \"Кто я такой, чтобы...\"", label: "Самозванец" },
  { text: "Страх успеха: саботирую когда близок к результату", label: "Страх успеха" },
  { text: "Паралич анализа: бесконечно исследую вместо действий", label: "Паралич" },
  { text: "Прокрастинация: откладываю важные задачи", label: "Прокрастинация" },
  { text: "Sunk Cost: не могу бросить проекты, в которые вложил время", label: "Sunk Cost" },
];

export default function AssessmentPage() {
  const { type } = useParams<{ type: string }>();
  const navigate = useNavigate();
  const userId = useAuthStore((s) => s.userId!);

  const [currentQ, setCurrentQ] = useState(0);
  const [answers, setAnswers] = useState<Record<string, number>>({});
  const [assessmentId, setAssessmentId] = useState<number | null>(null);
  const [result, setResult] = useState<any>(null);

  const isKmsi = type === "kmsi";
  const questions = isKmsi ? KMSI_QUESTIONS : SELF_SABOTAGE_QUESTIONS.map((q) => q.text);
  const totalQ = questions.length;

  const startMutation = useMutation({
    mutationFn: () => assessmentsApi.start(userId, type || "kmsi"),
    onSuccess: (data) => setAssessmentId(data.id),
  });

  const submitMutation = useMutation({
    mutationFn: () => assessmentsApi.submit(assessmentId!, answers),
    onSuccess: (data) => setResult(data),
  });

  // Start assessment on first render
  if (!assessmentId && !startMutation.isPending) {
    startMutation.mutate();
  }

  const handleAnswer = (value: number) => {
    setAnswers((prev) => ({ ...prev, [String(currentQ + 1)]: value }));
    if (currentQ < totalQ - 1) {
      setCurrentQ(currentQ + 1);
    }
  };

  const isComplete = Object.keys(answers).length === totalQ;
  const progress = (Object.keys(answers).length / totalQ) * 100;

  // Result screen
  if (result) {
    return (
      <div className="px-4 pt-6">
        <button
          onClick={() => navigate("/")}
          className="flex items-center gap-1 text-ink-muted hover:text-ink-primary mb-4"
        >
          <ArrowLeft size={18} />
          На главную
        </button>

        <h1 className="text-xl font-semibold mb-4">Результаты</h1>

        {result.interpretation && (
          <div className="card p-4 mb-4">
            <pre className="text-sm text-ink-secondary whitespace-pre-wrap font-sans">
              {result.interpretation}
            </pre>
          </div>
        )}

        {result.scores && (
          <div className="card p-4">
            <h3 className="font-medium text-sm mb-3">Баллы</h3>
            <div className="space-y-2">
              {Object.entries(result.scores).map(([key, val]) => (
                <div key={key} className="flex justify-between text-sm">
                  <span className="text-ink-muted">{key}</span>
                  <span className="font-medium">{String(val)}</span>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    );
  }

  return (
    <div className="px-4 pt-6">
      <button
        onClick={() => navigate(-1)}
        className="flex items-center gap-1 text-ink-muted hover:text-ink-primary mb-4"
      >
        <ArrowLeft size={18} />
        Назад
      </button>

      <h1 className="text-xl font-semibold mb-2">
        {isKmsi ? "Денежные скрипты (KMSI)" : "Самосаботаж"}
      </h1>

      {/* Progress bar */}
      <div className="h-1.5 bg-surface-tertiary rounded-full mb-6 overflow-hidden">
        <motion.div
          className="h-full bg-meridian-500 rounded-full"
          animate={{ width: `${progress}%` }}
          transition={{ duration: 0.3 }}
        />
      </div>

      {/* Question */}
      <AnimatePresence mode="wait">
        <motion.div
          key={currentQ}
          initial={{ opacity: 0, x: 30 }}
          animate={{ opacity: 1, x: 0 }}
          exit={{ opacity: 0, x: -30 }}
          className="mb-6"
        >
          <p className="text-xs text-ink-muted mb-2">
            Вопрос {currentQ + 1} из {totalQ}
          </p>
          <p className="text-lg font-medium leading-snug">
            {questions[currentQ]}
          </p>
        </motion.div>
      </AnimatePresence>

      {/* Answer buttons */}
      {isKmsi ? (
        <div className="space-y-2">
          {[1, 2, 3, 4, 5].map((val) => (
            <button
              key={val}
              onClick={() => handleAnswer(val)}
              className={`w-full text-left px-4 py-3 rounded-xl border transition-colors ${
                answers[String(currentQ + 1)] === val
                  ? "border-meridian-500 bg-meridian-50 text-meridian-700"
                  : "border-surface-tertiary hover:border-meridian-300"
              }`}
            >
              <span className="font-medium mr-2">{val}.</span>
              {["Совсем не согласен", "Не согласен", "Нейтрально", "Согласен", "Полностью согласен"][val - 1]}
            </button>
          ))}
        </div>
      ) : (
        <div className="space-y-2">
          {[1, 2, 3, 4, 5, 6, 7, 8, 9, 10].map((val) => (
            <button
              key={val}
              onClick={() => handleAnswer(val)}
              className={`inline-block w-[calc(20%-0.4rem)] m-0.5 text-center py-3 rounded-xl border transition-colors ${
                answers[String(currentQ + 1)] === val
                  ? "border-meridian-500 bg-meridian-50 text-meridian-700"
                  : "border-surface-tertiary hover:border-meridian-300"
              }`}
            >
              {val}
            </button>
          ))}
        </div>
      )}

      {/* Navigation */}
      <div className="flex justify-between mt-6">
        <button
          onClick={() => setCurrentQ(Math.max(0, currentQ - 1))}
          disabled={currentQ === 0}
          className="btn-secondary flex items-center gap-1 text-sm disabled:opacity-30"
        >
          <ArrowLeft size={16} />
          Назад
        </button>

        {isComplete ? (
          <button
            onClick={() => submitMutation.mutate()}
            disabled={submitMutation.isPending}
            className="btn-primary flex items-center gap-1.5 text-sm"
          >
            <Check size={16} />
            {submitMutation.isPending ? "Обработка..." : "Завершить"}
          </button>
        ) : (
          <button
            onClick={() => setCurrentQ(Math.min(totalQ - 1, currentQ + 1))}
            disabled={!answers[String(currentQ + 1)]}
            className="btn-secondary flex items-center gap-1 text-sm disabled:opacity-30"
          >
            Далее
            <ArrowRight size={16} />
          </button>
        )}
      </div>
    </div>
  );
}
