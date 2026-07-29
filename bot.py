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

# Хранилища в памяти
queue = []        # Очередь поиска
chats = {}        # Активные диалоги: {user_id: partner_id}

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

# 3. Меню во время диалога (добавлена кнопка "Следующий" и "Жалоба")
in_chat_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="➡️ Следующий"), KeyboardButton(text="❌ Завершить")],
        [KeyboardButton(text="⚠️ Пожаловаться")]
    ],
    resize_keyboard=True
)

# ==================== ХЭНДЛЕРЫ ==================== #

@dp.message(CommandStart())
async def cmd_start(message: Message):
    user_id = message.from_user.id
    
    # Очищаем состояния при старте
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
        "🤖 Это анонимный чат.\nВсе сообщения и медиафайлы передаются напрямую без раскрытия аккаунта.",
        reply_markup=main_kb
    )

# --- ФУНКЦИЯ ПОИСКА ---
async def search_partner(user_id: int, message: Message):
    if queue:
        partner_id = queue.pop(0)
        
        # Связываем пару
        chats[user_id] = partner_id
        chats[partner_id] = user_id

        await message.answer("🎉 **Собеседник найден!** Приятного общения.", reply_markup=in_chat_kb, parse_mode="Markdown")
        await bot.send_message(partner_id, "🎉 **Собеседник найден!** Приятного общения.", reply_markup=in_chat_kb, parse_mode="Markdown")
    else:
        queue.append(user_id)
        await message.answer("🔎 **Ищем свободного собеседника...**", reply_markup=searching_kb, parse_mode="Markdown")

@dp.message(F.text == "🔍 Найти собеседника")
async def start_search_handler(message: Message):
    user_id = message.from_user.id
    if user_id in chats:
        await message.answer("Вы уже находитесь в диалоге!", reply_markup=in_chat_kb)
        return
    if user_id in queue:
        await message.answer("Вы уже ищете собеседника...", reply_markup=searching_kb)
        return

    await search_partner(user_id, message)

# --- КНОПКА "СЛЕДУЮЩИЙ СОБЕСЕДНИК" ---
@dp.message(F.text == "➡️ Следующий")
async def next_partner(message: Message):
    user_id = message.from_user.id

    if user_id in chats:
        partner_id = chats.pop(user_id)
        chats.pop(partner_id, None)
        await bot.send_message(partner_id, "Собеседник перешел к новому поиску.", reply_markup=main_kb)
    elif user_id in queue:
        queue.remove(user_id)

    await search_partner(user_id, message)

# --- КНОПКА "ПОЖАЛОВАТЬСЯ" ---
@dp.message(F.text == "⚠️ Пожаловаться")
async def report_partner(message: Message):
    user_id = message.from_user.id

    if user_id in chats:
        partner_id = chats.pop(user_id)
        chats.pop(partner_id, None)

        await message.answer("Ваша жалоба принята. Диалог завершен.", reply_markup=main_kb)
        await bot.send_message(partner_id, "На вас поступила жалоба. Диалог принудительно завершен.", reply_markup=main_kb)
        
        # Автоматически запускаем поиск нового собеседника для пожаловавшегося
        await search_partner(user_id, message)
    else:
        await message.answer("У вас нет активного диалога.", reply_markup=main_kb)

# --- ОСТАНОВКА ПОИСКА И ЗАВЕРШЕНИЕ ---
@dp.message(F.text == "🛑 Остановить поиск")
async def stop_search(message: Message):
    user_id = message.from_user.id
    if user_id in queue:
        queue.remove(user_id)
        await message.answer("Поиск остановлен.", reply_markup=main_kb)

@dp.message(F.text == "❌ Завершить")
async def stop_dialog(message: Message):
    user_id = message.from_user.id
    if user_id in chats:
        partner_id = chats.pop(user_id)
        chats.pop(partner_id, None)

        await message.answer("Вы завершили диалог.", reply_markup=main_kb)
        await bot.send_message(partner_id, "Собеседник завершил диалог.", reply_markup=main_kb)
    else:
        await message.answer("У вас нет активного диалога.", reply_markup=main_kb)

# --- ПЕРЕСЫЛКА ЛЮБЫХ СООБЩЕНИЙ ---
@dp.message()
async def relay_message(message: Message):
    user_id = message.from_user.id

    if user_id in chats:
        partner_id = chats[user_id]
        try:
            await message.copy_to(chat_id=partner_id)
        except Exception:
            await message.answer("Не удалось доставить сообщение.")
    else:
        await message.answer("Чтобы начать общаться, нажмите «🔍 Найти собеседника».", reply_markup=main_kb)

# ==================== ЗАПУСК ==================== #

async def main():
    print("Бот обновлен и запущен...")
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        traceback.print_exc()
