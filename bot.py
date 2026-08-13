import json
import logging
import os
import random
from dataclasses import dataclass
from pathlib import Path

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.constants import ParseMode
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)


BASE_DIR = Path(__file__).resolve().parent
CONTENT_DIR = BASE_DIR / "content"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger("pref-bot")


@dataclass(frozen=True)
class Item:
    id: str
    title: str
    text: str


def load_items(filename: str) -> list[Item]:
    path = CONTENT_DIR / filename
    raw = json.loads(path.read_text(encoding="utf-8"))
    return [Item(id=str(x["id"]), title=str(x["title"]), text=str(x["text"])) for x in raw]


def main_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("Уроки", callback_data="lessons:list")],
            [InlineKeyboardButton("Ситуации (разбор)", callback_data="situations:list")],
            [
                InlineKeyboardButton("Случайная ситуация", callback_data="situations:random"),
                InlineKeyboardButton("Мини-квиз", callback_data="quiz:start"),
            ],
            [InlineKeyboardButton("Помощь", callback_data="help")],
        ]
    )


def back_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([[InlineKeyboardButton("← В меню", callback_data="menu")]])


def list_keyboard(prefix: str, items: list[Item]) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = []
    for it in items:
        rows.append([InlineKeyboardButton(it.title, callback_data=f"{prefix}:open:{it.id}")])
    rows.append([InlineKeyboardButton("← В меню", callback_data="menu")])
    return InlineKeyboardMarkup(rows)


def esc_md(text: str) -> str:
    for ch in ("_", "*", "[", "]", "(", ")", "~", "`", ">", "#", "+", "-", "=", "|", "{", "}", ".", "!"):
        text = text.replace(ch, f"\\{ch}")
    return text


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message:
        await update.message.reply_text(
            "Привет! Я бот для обучения игре в преферанс.\nВыбирай раздел ниже.",
            reply_markup=main_menu(),
        )


async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message:
        await update.message.reply_text(
            "/start - запуск\n/menu - меню\n\nИспользуй кнопки для уроков и разбора ситуаций.",
            reply_markup=main_menu(),
        )


async def menu_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message:
        await update.message.reply_text("Меню.", reply_markup=main_menu())


async def text_fallback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message:
        await update.message.reply_text("Для навигации используй кнопки.", reply_markup=main_menu())


async def callbacks(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    if not query:
        return

    await query.answer()
    data = query.data or ""

    lessons = load_items("lessons.json")
    situations = load_items("situations.json")

    if data == "menu":
        await query.edit_message_text("Меню.", reply_markup=main_menu())
        return

    if data == "help":
        await query.edit_message_text(
            "Это бот-тренер по преферансу: уроки, ситуации и квизы.\n"
            "Могу потом адаптировать под ваши домашние правила.",
            reply_markup=back_menu(),
        )
        return

    if data == "lessons:list":
        await query.edit_message_text("Выбери урок:", reply_markup=list_keyboard("lessons", lessons))
        return

    if data.startswith("lessons:open:"):
        lesson_id = data.split(":")[-1]
        item = next((x for x in lessons if x.id == lesson_id), None)
        if not item:
            await query.edit_message_text("Урок не найден.", reply_markup=back_menu())
            return
        await query.edit_message_text(
            f"*{esc_md(item.title)}*\n\n{esc_md(item.text)}",
            parse_mode=ParseMode.MARKDOWN_V2,
            reply_markup=back_menu(),
        )
        return

    if data == "situations:list":
        await query.edit_message_text("Выбери ситуацию:", reply_markup=list_keyboard("situations", situations))
        return

    if data == "situations:random":
        item = random.choice(situations)
        await query.edit_message_text(
            f"*{esc_md(item.title)}*\n\n{esc_md(item.text)}",
            parse_mode=ParseMode.MARKDOWN_V2,
            reply_markup=back_menu(),
        )
        return

    if data.startswith("situations:open:"):
        sit_id = data.split(":")[-1]
        item = next((x for x in situations if x.id == sit_id), None)
        if not item:
            await query.edit_message_text("Ситуация не найдена.", reply_markup=back_menu())
            return
        await query.edit_message_text(
            f"*{esc_md(item.title)}*\n\n{esc_md(item.text)}",
            parse_mode=ParseMode.MARKDOWN_V2,
            reply_markup=back_menu(),
        )
        return

    if data == "quiz:start":
        item = random.choice(situations)
        context.user_data["quiz_item"] = item.id
        kb = InlineKeyboardMarkup(
            [
                [InlineKeyboardButton("Показать варианты A/B/C", callback_data="quiz:choices")],
                [InlineKeyboardButton("← В меню", callback_data="menu")],
            ]
        )
        await query.edit_message_text(
            f"*Квиз*\n\n{esc_md(item.title)}\n\n{esc_md(item.text)}\n\nЧто выберешь?",
            parse_mode=ParseMode.MARKDOWN_V2,
            reply_markup=kb,
        )
        return

    if data == "quiz:choices":
        await query.edit_message_text(
            "*Варианты*\n\n"
            "A) Сразу играть максимально агрессивно.\n"
            "B) Сначала сохранить темп и собрать информацию о раскладе.\n"
            "C) Уходить в пассивную защиту в любом случае.\n\n"
            "*Почему обычно B*\n"
            "В преферансе чаще выигрывает точный план: информация и контроль темпа "
            "уменьшают шанс дорогой ошибки.",
            parse_mode=ParseMode.MARKDOWN_V2,
            reply_markup=back_menu(),
        )
        return

    await query.edit_message_text("Неизвестная команда.", reply_markup=back_menu())


def require_token() -> str:
    token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
    if not token:
        raise RuntimeError("Не задан TELEGRAM_BOT_TOKEN. Получи токен у @BotFather и задай переменную окружения.")
    return token


def run() -> None:
    token = require_token()
    app = Application.builder().token(token).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("menu", menu_cmd))
    app.add_handler(CallbackQueryHandler(callbacks))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_fallback))
    logger.info("Bot is running.")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    run()
