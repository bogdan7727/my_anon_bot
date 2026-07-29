import os
import asyncio
import logging
import traceback
from aiogram import Bot, Dispatcher

# Вставьте ваш новый токен или используйте переменную окружения
BOT_TOKEN = os.getenv("BOT_TOKEN", "8755629057:AAGOC5xOJjWKnZJI6AsT_u_OJ09yIe3nI8Z0")

# Настройка логирования
logging.basicConfig(level=logging.INFO)

# Инициализация бота и диспетчера
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Здесь подключайте ваши роутеры/хэндлеры, если они в отдельных файлах
# например: dp.include_router(router)

async def main():
    print("Бот начинает запуск...")
    # Удаляем вебхуки, если они были, и запускаем поллинг
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
