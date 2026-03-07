"""AI Therapist — Core engine via OpenClaw gateway (OpenAI-compatible)"""
from typing import Optional

import httpx
from loguru import logger

from backend.ai.system_prompt import build_system_prompt
from backend.config import settings
from backend.services.crisis_detector import check_crisis, get_crisis_response

GATEWAY_URL = settings.openclaw_gateway_url.rstrip("/")
TIMEOUT = httpx.Timeout(120.0, connect=10.0)


async def _chat(
    messages: list[dict],
    system: str = "",
    model: str | None = None,
    max_tokens: int = 2048,
) -> dict:
    """Send chat completion request to OpenClaw gateway."""
    model = model or settings.ai_model

    # OpenAI format: system goes as first message
    api_messages = []
    if system:
        api_messages.append({"role": "system", "content": system})
    api_messages.extend(messages)

    payload = {
        "model": model,
        "messages": api_messages,
        "max_tokens": max_tokens,
        "temperature": 0.7,
    }

    headers = {"Content-Type": "application/json"}
    if settings.openclaw_gateway_token:
        headers["Authorization"] = f"Bearer {settings.openclaw_gateway_token}"

    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        resp = await client.post(
            f"{GATEWAY_URL}/chat/completions",
            json=payload,
            headers=headers,
        )
        resp.raise_for_status()
        data = resp.json()

    content = data["choices"][0]["message"]["content"].strip()
    usage = data.get("usage", {})

    return {
        "content": content,
        "model_used": model,
        "tokens_input": usage.get("prompt_tokens", 0),
        "tokens_output": usage.get("completion_tokens", 0),
    }


class AITherapist:
    """Core AI therapy engine. Routes requests through OpenClaw gateway."""

    async def generate_response(
        self,
        user_message: str,
        conversation_history: list[dict],
        session_number: int = 1,
        therapy_phase: str = "assessment",
        total_sessions: int = 0,
        money_scripts_summary: str = "Не определены",
        active_tasks: str = "Нет",
        patterns: str = "Не выявлены",
        last_session_summary: str = "Первая сессия",
        session_focus: str = "Intake и первичная оценка",
        methodology: str | None = None,
        rag_context: str = "",
    ) -> dict:
        """Generate a therapist response.

        Returns dict with:
            content: str — the response text
            crisis_detected: bool — whether crisis was detected
            model_used: str — which model was used
            tokens_input: int
            tokens_output: int
        """
        # Step 1: Crisis pre-screening
        if check_crisis(user_message):
            logger.warning("Crisis detected in message (keyword match)")
            return {
                "content": get_crisis_response(),
                "crisis_detected": True,
                "model_used": "crisis_detector",
                "tokens_input": 0,
                "tokens_output": 0,
            }

        # Step 2: Build system prompt
        system_prompt = build_system_prompt(
            session_number=session_number,
            therapy_phase=therapy_phase,
            total_sessions=total_sessions,
            money_scripts_summary=money_scripts_summary,
            active_tasks=active_tasks,
            patterns=patterns,
            last_session_summary=last_session_summary,
            session_focus=session_focus,
            methodology=methodology,
            rag_context=rag_context,
        )

        # Step 3: Build messages
        messages = []
        for msg in conversation_history:
            messages.append({"role": msg["role"], "content": msg["content"]})
        messages.append({"role": "user", "content": user_message})

        # Step 4: Call via gateway (primary → fallback)
        try:
            result = await _chat(
                messages=messages,
                system=system_prompt,
                model=settings.ai_model,
            )
            result["crisis_detected"] = False
            return result
        except Exception as e:
            logger.warning(f"Primary model failed: {e}. Trying fallback.")

        try:
            result = await _chat(
                messages=messages,
                system=system_prompt,
                model=settings.ai_fallback_model,
            )
            result["crisis_detected"] = False
            return result
        except Exception as e2:
            logger.error(f"Fallback model also failed: {e2}")
            return {
                "content": "Произошла техническая ошибка. Попробуй ещё раз через минуту.",
                "crisis_detected": False,
                "model_used": "error",
                "tokens_input": 0,
                "tokens_output": 0,
            }

    async def generate_session_summary(
        self,
        conversation_history: list[dict],
    ) -> dict:
        """Generate a session summary at session close."""
        summary_prompt = """Проанализируй эту терапевтическую сессию и создай структурированное резюме.

Верни ответ в следующем формате:

РЕЗЮМЕ:
[2-3 предложения о том, что обсуждалось и какой прогресс был]

КЛЮЧЕВЫЕ ИНСАЙТЫ:
- [инсайт 1]
- [инсайт 2]

ВЫЯВЛЕННЫЕ ПАТТЕРНЫ:
- [паттерн 1]
- [паттерн 2]

РЕКОМЕНДУЕМЫЕ ЗАДАНИЯ:
- [задание 1: конкретное, маленькое, с дедлайном]
- [задание 2]

ЭМОЦИОНАЛЬНОЕ СОСТОЯНИЕ:
- Начало сессии (1-10): [оценка]
- Конец сессии (1-10): [оценка]
- Уровень вовлечённости (1-10): [оценка]
- Уровень сопротивления (1-10): [оценка]"""

        messages = []
        for msg in conversation_history:
            messages.append({"role": msg["role"], "content": msg["content"]})
        messages.append({"role": "user", "content": summary_prompt})

        try:
            result = await _chat(
                messages=messages,
                system="Ты — ассистент терапевта. Анализируй сессии и создавай структурированные заметки.",
                model=settings.ai_fallback_model,
                max_tokens=1500,
            )
            return {"summary": result["content"], "success": True}
        except Exception as e:
            logger.error(f"Failed to generate summary: {e}")
            return {"summary": "Не удалось сгенерировать резюме", "success": False}
