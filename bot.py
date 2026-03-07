"""AI Psychologist — Telegram Bot (aiogram 3)

Основной чат с терапевтом прямо в Telegram.
Mini App — для дашборда, прогресса, тестов.
"""
import asyncio

from aiogram import Bot, Dispatcher, Router, F
from aiogram.enums import ParseMode, ChatAction
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    MenuButtonWebApp,
    WebAppInfo,
)
from aiogram.client.default import DefaultBotProperties
from loguru import logger
from sqlalchemy import select, func

from backend.config import settings
from backend.database import AsyncSessionLocal, init_db
from backend.models.user import User
from backend.models.session import TherapySession
from backend.models.task import TherapyTask
from backend.services.session_manager import (
    get_or_create_user,
    start_session,
    send_message,
    complete_session,
)

# --- Bot setup ---

bot = Bot(
    token=settings.telegram_bot_token,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML),
)
dp = Dispatcher()
router = Router()


# --- FSM States ---

class TaskReflection(StatesGroup):
    waiting_reflection = State()


# --- /start ---

@router.message(CommandStart())
async def cmd_start(message: Message):
    """Приветствие + создание юзера."""
    async with AsyncSessionLocal() as db:
        user = await get_or_create_user(
            db, message.from_user.id, message.from_user.first_name
        )
        await db.commit()

    # Кнопки
    buttons = []
    if settings.mini_app_url:
        buttons.append([InlineKeyboardButton(
            text="Дашборд",
            web_app=WebAppInfo(url=settings.mini_app_url),
        )])
    buttons.append([InlineKeyboardButton(text="Начать сессию", callback_data="start_session")])

    await message.answer(
        f"Привет, {message.from_user.first_name}!\n\n"
        "Я — твой AI-терапевт. Помогу разобраться с финансовыми блоками, "
        "паттернами саботажа и найти путь к монетизации.\n\n"
        "<b>Важно:</b> я — AI, не лицензированный психолог. "
        "При серьёзных проблемах обратись к специалисту.\n\n"
        "Жми <b>«Начать сессию»</b> — и поговорим.",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons),
    )


# --- /session — начать или продолжить сессию ---

@router.message(Command("session"))
async def cmd_session(message: Message):
    """Начать новую или продолжить активную сессию."""
    async with AsyncSessionLocal() as db:
        user = await get_or_create_user(db, message.from_user.id, message.from_user.first_name)

        # Проверяем активную сессию
        result = await db.execute(
            select(TherapySession).where(
                TherapySession.user_id == user.id,
                TherapySession.status == "active",
            )
        )
        active = result.scalar_one_or_none()

        if active:
            await message.answer(
                f"У тебя уже есть активная сессия #{active.session_number}.\n"
                "Просто пиши — я слушаю.\n\n"
                "Чтобы завершить: /end"
            )
        else:
            session = await start_session(db, user.id)
            await db.commit()
            await message.answer(
                f"<b>Сессия #{session.session_number} начата.</b>\n\n"
                "Расскажи, что тебя сейчас больше всего беспокоит?\n\n"
                "<i>Чтобы завершить сессию: /end</i>"
            )


@router.callback_query(F.data == "start_session")
async def cb_start_session(callback: CallbackQuery):
    """Callback кнопки «Начать сессию»."""
    async with AsyncSessionLocal() as db:
        user = await get_or_create_user(db, callback.from_user.id, callback.from_user.first_name)

        result = await db.execute(
            select(TherapySession).where(
                TherapySession.user_id == user.id,
                TherapySession.status == "active",
            )
        )
        active = result.scalar_one_or_none()

        if active:
            await callback.message.answer(
                f"Сессия #{active.session_number} уже активна. Просто пиши!"
            )
        else:
            session = await start_session(db, user.id)
            await db.commit()
            await callback.message.answer(
                f"<b>Сессия #{session.session_number} начата.</b>\n\n"
                "Расскажи, что тебя сейчас беспокоит?"
            )

    await callback.answer()


# --- /end — завершить сессию ---

@router.message(Command("end"))
async def cmd_end(message: Message):
    """Завершить активную сессию, получить summary."""
    async with AsyncSessionLocal() as db:
        user = await get_or_create_user(db, message.from_user.id, message.from_user.first_name)

        result = await db.execute(
            select(TherapySession).where(
                TherapySession.user_id == user.id,
                TherapySession.status == "active",
            )
        )
        active = result.scalar_one_or_none()

        if not active:
            await message.answer("Нет активной сессии. Начни новую: /session")
            return

        await message.bot.send_chat_action(message.chat.id, ChatAction.TYPING)
        result = await complete_session(db, active.id)
        await db.commit()

    summary = result.get("summary", "")
    duration = result.get("duration_minutes", 0)

    text = f"<b>Сессия завершена.</b>\n"
    if duration:
        text += f"Длительность: {duration} мин.\n"
    text += f"\n{summary[:3000]}"  # Telegram limit safety

    buttons = []
    if settings.mini_app_url:
        buttons.append([InlineKeyboardButton(
            text="Открыть дашборд",
            web_app=WebAppInfo(url=settings.mini_app_url),
        )])
    buttons.append([InlineKeyboardButton(text="Новая сессия", callback_data="start_session")])

    await message.answer(
        text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons) if buttons else None,
    )


# --- /tasks — показать задания ---

@router.message(Command("tasks"))
async def cmd_tasks(message: Message):
    """Показать текущие задания."""
    async with AsyncSessionLocal() as db:
        user = await get_or_create_user(db, message.from_user.id, message.from_user.first_name)

        result = await db.execute(
            select(TherapyTask).where(
                TherapyTask.user_id == user.id,
                TherapyTask.status == "pending",
            ).order_by(TherapyTask.created_at.desc()).limit(10)
        )
        tasks = result.scalars().all()
        await db.commit()

    if not tasks:
        await message.answer(
            "У тебя нет активных заданий.\n"
            "Задания появятся после терапевтических сессий."
        )
        return

    text = "<b>Твои задания:</b>\n\n"
    buttons = []
    for i, task in enumerate(tasks, 1):
        stars = "★" * task.difficulty + "☆" * (5 - task.difficulty)
        text += f"{i}. <b>{task.title}</b> {stars}\n{task.description}\n\n"
        buttons.append([
            InlineKeyboardButton(text=f"✅ {i}. Выполнено", callback_data=f"task_done:{task.id}"),
            InlineKeyboardButton(text=f"⏭ Пропустить", callback_data=f"task_skip:{task.id}"),
        ])

    await message.answer(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))


@router.callback_query(F.data.startswith("task_done:"))
async def cb_task_done(callback: CallbackQuery, state: FSMContext):
    """Отметить задание выполненным — спросить рефлексию."""
    task_id = int(callback.data.split(":")[1])
    await state.update_data(completing_task_id=task_id)
    await state.set_state(TaskReflection.waiting_reflection)
    await callback.message.answer(
        "Как прошло? Что заметил? Напиши коротко (или отправь «—» чтобы пропустить)."
    )
    await callback.answer()


@router.message(TaskReflection.waiting_reflection)
async def process_reflection(message: Message, state: FSMContext):
    """Сохранить рефлексию и завершить задание."""
    data = await state.get_data()
    task_id = data.get("completing_task_id")
    reflection = message.text if message.text != "—" else ""

    async with AsyncSessionLocal() as db:
        result = await db.execute(select(TherapyTask).where(TherapyTask.id == task_id))
        task = result.scalar_one_or_none()
        if task:
            from datetime import datetime, timezone
            task.status = "completed"
            task.completed_at = datetime.now(timezone.utc)
            task.reflection = reflection
            await db.commit()
            await message.answer(f"✅ <b>{task.title}</b> — выполнено!\n\nМолодец. Продолжай.")
        else:
            await message.answer("Задание не найдено.")

    await state.clear()


@router.callback_query(F.data.startswith("task_skip:"))
async def cb_task_skip(callback: CallbackQuery):
    """Пропустить задание."""
    task_id = int(callback.data.split(":")[1])

    async with AsyncSessionLocal() as db:
        result = await db.execute(select(TherapyTask).where(TherapyTask.id == task_id))
        task = result.scalar_one_or_none()
        if task:
            task.status = "skipped"
            await db.commit()
            await callback.message.answer(f"⏭ <b>{task.title}</b> — пропущено.")
        else:
            await callback.message.answer("Задание не найдено.")

    await callback.answer()


# --- /progress — краткая сводка ---

@router.message(Command("progress"))
async def cmd_progress(message: Message):
    """Краткая текстовая сводка прогресса."""
    async with AsyncSessionLocal() as db:
        user = await get_or_create_user(db, message.from_user.id, message.from_user.first_name)

        # Подсчитаем статистику
        sessions_result = await db.execute(
            select(func.count(TherapySession.id)).where(
                TherapySession.user_id == user.id,
                TherapySession.status == "completed",
            )
        )
        total_sessions = sessions_result.scalar() or 0

        tasks_done_result = await db.execute(
            select(func.count(TherapyTask.id)).where(
                TherapyTask.user_id == user.id,
                TherapyTask.status == "completed",
            )
        )
        tasks_done = tasks_done_result.scalar() or 0

        tasks_pending_result = await db.execute(
            select(func.count(TherapyTask.id)).where(
                TherapyTask.user_id == user.id,
                TherapyTask.status == "pending",
            )
        )
        tasks_pending = tasks_pending_result.scalar() or 0
        await db.commit()

    text = (
        "<b>Твой прогресс:</b>\n\n"
        f"Сессий пройдено: {total_sessions}\n"
        f"Заданий выполнено: {tasks_done}\n"
        f"Заданий ожидают: {tasks_pending}\n"
        f"Фаза терапии: {user.therapy_phase}\n"
    )

    # Money scripts
    scripts = []
    if user.money_avoidance_score and user.money_avoidance_score > 2.5:
        scripts.append(f"  Избегание: {user.money_avoidance_score:.1f}/5")
    if user.money_worship_score and user.money_worship_score > 2.5:
        scripts.append(f"  Поклонение: {user.money_worship_score:.1f}/5")
    if user.money_status_score and user.money_status_score > 2.5:
        scripts.append(f"  Статус: {user.money_status_score:.1f}/5")
    if user.money_vigilance_score and user.money_vigilance_score > 2.5:
        scripts.append(f"  Бдительность: {user.money_vigilance_score:.1f}/5")

    if scripts:
        text += "\nДенежные скрипты:\n" + "\n".join(scripts)
    else:
        text += "\nДенежные скрипты: ещё не определены"

    buttons = []
    if settings.mini_app_url:
        buttons.append([InlineKeyboardButton(
            text="Подробнее в дашборде",
            web_app=WebAppInfo(url=settings.mini_app_url),
        )])

    await message.answer(
        text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons) if buttons else None,
    )


# --- /app — открыть Mini App ---

@router.message(Command("app"))
async def cmd_app(message: Message):
    """Открыть Mini App."""
    if not settings.mini_app_url:
        await message.answer("Mini App ещё не настроен.")
        return

    await message.answer(
        "Открой дашборд:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[[
            InlineKeyboardButton(
                text="Открыть дашборд",
                web_app=WebAppInfo(url=settings.mini_app_url),
            )
        ]]),
    )


# --- Основной хэндлер текстовых сообщений (чат с терапевтом) ---

@router.message(F.text)
async def handle_text(message: Message):
    """Любое текстовое сообщение → отправляем терапевту."""
    async with AsyncSessionLocal() as db:
        user = await get_or_create_user(db, message.from_user.id, message.from_user.first_name)

        # Ищем активную сессию
        result = await db.execute(
            select(TherapySession).where(
                TherapySession.user_id == user.id,
                TherapySession.status == "active",
            )
        )
        active_session = result.scalar_one_or_none()

        if not active_session:
            # Автоматически начинаем сессию
            active_session = await start_session(db, user.id)
            await db.commit()
            await message.answer(
                f"<i>Сессия #{active_session.session_number} начата автоматически.</i>"
            )

        # Показываем "печатает..."
        await message.bot.send_chat_action(message.chat.id, ChatAction.TYPING)

        # Отправляем сообщение терапевту
        response = await send_message(db, active_session.id, user.id, message.text)
        await db.commit()

    if "error" in response:
        await message.answer("Произошла ошибка. Попробуй ещё раз.")
        return

    # Отправляем ответ терапевта
    ai_text = response["content"]

    # Разбиваем на части если длинный (Telegram лимит 4096)
    while len(ai_text) > 4000:
        # Ищем последний перенос строки в пределах лимита
        split_pos = ai_text[:4000].rfind("\n")
        if split_pos < 100:
            split_pos = 4000
        await message.answer(ai_text[:split_pos])
        ai_text = ai_text[split_pos:]

    await message.answer(ai_text)

    # Если кризис — отправляем отдельное сообщение
    if response.get("crisis_detected"):
        await message.answer(
            "⚠️ <b>Если тебе нужна помощь прямо сейчас:</b>\n\n"
            "Телефон доверия: <b>8-800-2000-122</b> (бесплатно, круглосуточно)\n"
            "Экстренная психологическая помощь: <b>051</b> (с мобильного: <b>8-495-051</b>)"
        )


# --- Startup ---

dp.include_router(router)


async def main():
    logger.info("Starting AI Psychologist bot...")
    await init_db()
    logger.info("Database initialized.")

    # Устанавливаем команды бота
    from aiogram.types import BotCommand
    await bot.set_my_commands([
        BotCommand(command="session", description="Начать сессию"),
        BotCommand(command="end", description="Завершить сессию"),
        BotCommand(command="tasks", description="Мои задания"),
        BotCommand(command="progress", description="Мой прогресс"),
        BotCommand(command="app", description="Открыть дашборд"),
    ])

    # Menu button → Mini App
    if settings.mini_app_url:
        await bot.set_chat_menu_button(
            menu_button=MenuButtonWebApp(
                text="Дашборд",
                web_app=WebAppInfo(url=settings.mini_app_url),
            )
        )

    logger.info("Bot is ready. Starting polling...")
    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())


if __name__ == "__main__":
    asyncio.run(main())
