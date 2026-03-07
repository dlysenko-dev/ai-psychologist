# AI Psychologist — Инструкции для Claude Code

## О проекте

Персональный AI-психолог. Веб-приложение для работы с финансовыми блоками,
паттернами самосаботажа и когнитивными искажениями у предпринимателей.

Однопользовательский инструмент. Не SaaS.

## Стек

- **Backend:** FastAPI + PostgreSQL + pgvector + SQLAlchemy async
- **Frontend:** React 18 + TypeScript + Vite + TailwindCSS + Zustand + React Query
- **AI:** Claude Opus 4.6 (primary), Sonnet 4.5 (fallback)
- **RAG:** sentence-transformers MiniLM + pgvector (384 dimensions)

## Порты

- Backend: 8010
- Frontend: 3010

## Запуск

```bash
# Backend
cd backend && python -m uvicorn main:app --port 8010 --reload

# Frontend
cd frontend && npm run dev
```

## Безопасность

- НЕ показывай API ключи, токены, пароли
- .env — НИКОГДА не коммить
- Данные терапевтических сессий — чувствительные, обращаться аккуратно
