import os
import asyncio
import logging
import traceback
from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.types import Message

# Считываем токен из переменных окружения Render или вставляем напрямую
BOT_TOKEN = os.getenv("BOT_TOKEN", "8755629057:AAGOC5xOJjWKnZJI6AsT_u_OJ09yIe3nI8Z0")

logging.basicConfig(level=logging.INFO)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# ------------------- ХЭНДЛЕРЫ (ОБРАБОТЧИКИ) ------------------- #

# 1. Хэндлер для команды /start
@dp.message(Command("start"))
async def cmd_start(message: Message):
    print(f"Получена команда /start от пользователя {message.from_user.id}")
    await message.answer("Привет! Бот успешно запущен и работает! 🚀")

# 2. Хэндлер для любого другого текста
@dp.message()
async def echo_message(message: Message):
    await message.answer(f"Вы написали: {message.text}")

# ------------------------------------------------------------- #

async def main():
    print("Бот начинает запуск...")
    # Сбрасываем старые накопившиеся сообщения, если они были
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        print("!!! ПРОИЗОШЛА ОШИБКА ПРИ ЗАПУСКЕ !!!")
        print(f"Тип ошибки: {type(e).__name__}")
        print(f"Текст ошибки: {e}")
        traceback.print_exc()
