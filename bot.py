import os
import asyncio
import logging
import traceback

from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton

BOT_TOKEN = os.getenv("BOT_TOKEN")

logging.basicConfig(level=logging.INFO)

if not BOT_TOKEN:
    raise ValueError("Переменная BOT_TOKEN не найдена в Environment variables!")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Хранилища в памяти приложения
queue = []        # Очередь пользователей, ищущих собеседника: [user_id_1, user_id_2, ...]
chats = {}        # Активные комнаты: {user_id_1: user_id_2, user_id_2: user_id_1}

# ==================== КЛАВИАТУРЫ ==================== #

# 1. Главное меню
main_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🔍 Найти собеседника")],
        [KeyboardButton(text="ℹ️ О боте")]
    ],
    resize_keyboard=True
)

# 2. Меню во время поиска
searching_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🛑 Остановить поиск")]
    ],
    resize_keyboard=True
)

# 3. Меню во время общения
in_chat_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="❌ Завершить диалог")]
    ],
    resize_keyboard=True
)

# ==================== ХЭНДЛЕРЫ ==================== #

@dp.message(CommandStart())
async def cmd_start(message: Message):
    user_id = message.from_user.id
    
    # Если пользователь уже в чате или поиске — сбрасываем состояние
    if user_id in queue:
        queue.remove(user_id)
    elif user_id in chats:
        partner_id = chats.pop(user_id, None)
        if partner_id:
            chats.pop(partner_id, None)
            await bot.send_message(partner_id, "Собеседник перезапустил бота. Диалог завершен.", reply_markup=main_kb)

    await message.answer(
        "👋 **Добро пожаловать в Анонимный Чат!**\n\n"
        "Нажмите кнопку ниже, чтобы начать поиск собеседника.",
        reply_markup=main_kb,
        parse_mode="Markdown"
    )

@dp.message(F.text == "ℹ️ О боте")
async def about_bot(message: Message):
    await message.answer(
        "🤖 Это анонимный чат.\nНикто из собеседников не увидит ваше имя или ссылку на профиль.",
        reply_markup=main_kb
    )

# --- ПОИСК СОБЕСЕДНИКА ---
@dp.message(F.text == "🔍 Найти собеседника")
async def start_search(message: Message):
    user_id = message.from_user.id

    if user_id in chats:
        await message.answer("Вы уже находитесь в диалоге!", reply_markup=in_chat_kb)
        return

    if user_id in queue:
        await message.answer("Вы уже ищете собеседника...", reply_markup=searching_kb)
        return

    # Проверяем, есть ли кто-то в очереди
    if queue:
        partner_id = queue.pop(0)
        
        # Соединяем пользователей в парную структуру
        chats[user_id] = partner_id
        chats[partner_id] = user_id

        # Оповещаем обоих
        await message.answer("🎉 **Собеседник найден!** Приятного общения.", reply_markup=in_chat_kb, parse_mode="Markdown")
        await bot.send_message(partner_id, "🎉 **Собеседник найден!** Приятного общения.", reply_markup=in_chat_kb, parse_mode="Markdown")
    else:
        queue.append(user_id)
        await message.answer("🔎 **Ищем свободного собеседника...**", reply_markup=searching_kb, parse_mode="Markdown")

# --- ОСТАНОВКА ПОИСКА ---
@dp.message(F.text == "🛑 Остановить поиск")
async def stop_search(message: Message):
    user_id = message.from_user.id

    if user_id in queue:
        queue.remove(user_id)
        await message.answer("Поиск остановлен.", reply_markup=main_kb)
    else:
        await message.answer("Вы не находились в поиске.", reply_markup=main_kb)

# --- ЗАВЕРШЕНИЕ ДИАЛОГА ---
@dp.message(F.text == "❌ Завершить диалог")
async def stop_dialog(message: Message):
    user_id = message.from_user.id

    if user_id in chats:
        partner_id = chats.pop(user_id)
        chats.pop(partner_id, None)

        await message.answer("Вы завершили диалог.", reply_markup=main_kb)
        await bot.send_message(partner_id, "Собеседник завершил диалог.", reply_markup=main_kb)
    else:
        await message.answer("У вас нет активного диалога.", reply_markup=main_kb)

# --- ПЕРЕСЫЛКА СООБЩЕНИЙ В ЧАТЕ ---
@dp.message()
async def relay_message(message: Message):
    user_id = message.from_user.id

    if user_id in chats:
        partner_id = chats[user_id]
        try:
            # Пересылаем копию сообщения собеседнику (текст, фото, голос и т.д.)
            await message.copy_to(chat_id=partner_id)
        except Exception as e:
            await message.answer("Не удалось отправить сообщение собеседнику.")
    else:
        await message.answer("Чтобы начать общаться, нажмите «🔍 Найти собеседника».", reply_markup=main_kb)

# ==================== ЗАПУСК ==================== #

async def main():
    print("Анонимный чат-бот успешно запущен...")
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        traceback.print_exc()
