import os
import asyncio
import logging
import traceback
from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.types import Message

# Указан ваш актуальный токен
BOT_TOKEN = "8755629057:AAGOC5xOJjWKnZJI6AsTu_OJO9yIe3nI8Z0"

# Включаем логирование, чтобы видеть события в консоли
logging.basicConfig(level=logging.INFO)

# Инициализируем бота и диспетчер
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()


# ==================== ХЭНДЛЕРЫ (ОБРАБОТЧИКИ) ==================== #

# Реакция на команду /start
@dp.message(Command("start"))
async def cmd_start(message: Message):
    print(f"Получена команда /start от id: {message.from_user.id}")
    await message.answer("Привет! Бот успешно запущен и готов к работе! 🚀")

# Реакция на любое текстовое сообщение
@dp.message()
async def echo_message(message: Message):
    await message.answer(f"Вы написали: {message.text}")

# ================================================================= #


async def main():
    print("Бот начинает запуск...")
    # Удаляем скопившиеся за время оффлайна обновления и запускаем поллинг
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
