BOT_TOKEN = "8755629057:AAGOC5xOJjWKnZJI6AsT u_OJ09yIe3nI8Z0"
import traceback

async def main():
    # ... ваш существующий код функции main() ...
    print("Бот начинает запуск...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        print("!!! ПРОИЗОШЛА ОШИБКА ПРИ ЗАПУСКЕ !!!")
        print(f"Тип ошибки: {type(e).__name__}")
        print(f"Текст ошибки: {e}")
        traceback.print_exc()
