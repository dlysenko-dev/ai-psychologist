# AI Psychologist

Персональный AI-психолог. Веб-приложение для работы с финансовыми блоками, паттернами самосаботажа и когнитивными искажениями у предпринимателей.

Однопользовательский инструмент, не SaaS.

## Стек
- **Backend:** FastAPI + PostgreSQL + pgvector + SQLAlchemy async
- **Frontend:** React 18 + TypeScript + Vite + TailwindCSS + Zustand + React Query
- **AI:** Claude Opus 4.6 (primary), Sonnet 4.5 (fallback)
- **RAG:** sentence-transformers MiniLM + pgvector (384 dimensions)

## Структура
```
backend/        — FastAPI API (порт 8010)
frontend/       — React SPA (порт 3010)
knowledge_base/ — Базы знаний для RAG
bot.py          — Telegram бот
scripts/        — Утилиты
```

## Запуск
```bash
pip install -r requirements.txt

# Backend
cd backend && python -m uvicorn main:app --port 8010 --reload

# Frontend
cd frontend && npm install && npm run dev
```

## Статус
Active
