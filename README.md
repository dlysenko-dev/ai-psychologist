# AI Psychologist — RAG-powered Cognitive Therapy App

Full-stack веб-приложение: AI-психолог для работы с когнитивными искажениями, финансовыми блоками и паттернами самосаботажа.

**RAG на pgvector + Claude. React + FastAPI. Telegram Mini App.**

## Что делает

- Ведёт терапевтические диалоги на основе КПТ (когнитивно-поведенческая терапия)
- RAG: ищет релевантные знания из базы (pgvector, 384-мерные эмбеддинги)
- Отслеживает прогресс, инсайты и паттерны пользователя
- Telegram Mini App для мобильного доступа

## Стек

| Компонент | Технология |
|-----------|-----------|
| Backend | FastAPI, SQLAlchemy 2.0 (async), asyncpg |
| Frontend | React 18, TypeScript, Vite, Tailwind CSS, Zustand |
| AI | Claude Opus 4.6 (primary), Sonnet 4.5 (fallback) |
| RAG | pgvector + sentence-transformers MiniLM (384 dims) |
| БД | PostgreSQL + pgvector extension |
| Auth | JWT (python-jose), bcrypt |
| Миграции | Alembic |
| Telegram | Telegram Bot API + Mini App |

## Архитектура

```
backend/
├── main.py          — FastAPI app (порт 8010)
├── config.py        — Pydantic Settings (.env)
├── models.py        — SQLAlchemy модели (Users, Sessions, Insights)
├── api/             — REST endpoints
├── services/        — AI, RAG, session management
└── knowledge/       — Knowledge base для RAG

frontend/
├── src/
│   ├── components/  — React компоненты
│   ├── stores/      — Zustand state management
│   ├── api/         — React Query + axios
│   └── pages/       — Роутинг
└── vite.config.ts

bot.py               — Telegram бот
knowledge_base/      — Markdown-документы для RAG индексации
```

## Запуск

```bash
# Backend
cd backend
pip install -r requirements.txt
cp .env.example .env  # заполнить переменные
python -m uvicorn main:app --port 8010 --reload

# Frontend
cd frontend
npm install
npm run dev  # порт 3010
```

## Автор

Данил Лысенко — [@Daniel_Lysenko33](https://t.me/Daniel_Lysenko33)
