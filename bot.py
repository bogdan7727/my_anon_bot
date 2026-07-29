import os
import asyncio
import logging
import traceback

from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove

BOT_TOKEN = os.getenv("BOT_TOKEN")

logging.basicConfig(level=logging.INFO)

if not BOT_TOKEN:
    raise ValueError("Переменная BOT_TOKEN не найдена в Environment variables!")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# ==================== КЛАВИАТУРЫ ==================== #

# 1. Главное меню (когда пользователь не в поиске и не в чате)
main_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🔍 Найти собеседника")],
        [KeyboardButton(text="ℹ️ О боте")]
    ],
    resize_keyboard=True,
    persistent=True
)

# 2. Клавиатура во время поиска
searching_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🛑 Остановить поиск")]
    ],
    resize_keyboard=True
)

# 3. Клавиатура во время активного диалога
in_chat_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="❌ Завершить диалог")]
    ],
    resize_keyboard=True
)

# ==================== ХЭНДЛЕРЫ ==================== #

# Команда /start
@dp.message(CommandStart())
async def cmd_start(message: Message):
    await message.answer(
        "👋 **Добро пожаловать в Анонимный Чат!**\n\n"
        "Здесь вы можете общаться абсолютно анонимно.\n"
        "Нажмите кнопку ниже, чтобы начать поиск собеседника.",
        reply_markup=main_kb,
        parse_mode="Markdown"
    )

# Кнопка "О боте"
@dp.message(F.text == "ℹ️ О боте")
async def about_bot(message: Message):
    await message.answer(
        "🤖 Это безопасный анонимный чат.\n"
        "Ваши личные данные и профиль Telegram никому не передаются.",
        reply_markup=main_kb
    )

# Кнопка "Найти собеседника"
@dp.message(F.text == "🔍 Найти собеседника")
async def start_search(message: Message):
    # Здесь позже подсоединим добавление пользователя в очередь/Redis
    await message.answer(
        "🔎 **Ищем свободного собеседника...**\nПожалуйста, подождите.",
        reply_markup=searching_kb,
        parse_mode="Markdown"
    )

# Кнопка "Остановить поиск"
@dp.message(F.text == "🛑 Остановить поиск")
async def stop_search(message: Message):
    # Здесь позже добавим удаление из очереди
    await message.answer(
        "Поиск остановлен. Вы вернулись в главное меню.",
        reply_markup=main_kb
    )

# Кнопка "Завершить диалог"
@dp.message(F.text == "❌ Завершить диалог")
async def stop_dialog(message: Message):
    # Здесь позже добавим логику разрыва комнаты для обоих собеседников
    await message.answer(
        "Диалог завершен.",
        reply_markup=main_kb
    )

# ==================== ЗАПУСК ==================== #

async def main():
    print("Бот с меню успешно запущен...")
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        print("!!! ОШИБКА ПРИ ЗАПУСКЕ !!!")
        traceback.print_exc()
