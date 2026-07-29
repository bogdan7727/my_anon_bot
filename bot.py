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

# --- ХРАНИЛИЩА В ПАМЯТИ ---
users_gender = {}    # {user_id: "M" или "F"}
search_pref = {}     # {user_id: "M", "F" или "ANY"}
queue = []           # Список пользователей в поиске: [{"user_id": int, "gender": str, "pref": str}]
chats = {}           # Активные комнаты: {user_id: partner_id}

# ==================== КЛАВИАТУРЫ ==================== #

# Выбор собственного пола
gender_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="👨 Я парень"), KeyboardButton(text="👩 Я девушка")]
    ],
    resize_keyboard=True
)

# Выбор предпочитаемого пола собеседника
pref_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="👨 Искать парня"), KeyboardButton(text="👩 Искать девушку")],
        [KeyboardButton(text="🎲 Все равно")]
    ],
    resize_keyboard=True
)

# Главное меню
main_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🔍 Найти собеседника")],
        [KeyboardButton(text="⚙️ Изменить мой пол"), KeyboardButton(text="ℹ️ О боте")]
    ],
    resize_keyboard=True
)

# Меню поиска
searching_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🛑 Остановить поиск")]
    ],
    resize_keyboard=True
)

# Меню в диалоге
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
    
    # Сброс поиска или активного чата при перезапуске
    clear_user_state(user_id)

    if user_id not in users_gender:
        await message.answer(
            "👋 **Добро пожаловать в Анонимный Чат!**\n\nДля начала укажите ваш пол:",
            reply_markup=gender_kb,
            parse_mode="Markdown"
        )
    else:
        await message.answer(
            "👋 Вы вернулись в главное меню!",
            reply_markup=main_kb
        )

# Выбор своего пола
@dp.message(F.text.in_({"👨 Я парень", "👩 Я девушка"}))
async def set_gender(message: Message):
    user_id = message.from_user.id
    gender = "M" if message.text == "👨 Я парень" else "F"
    users_gender[user_id] = gender
    
    await message.answer(
        "Отлично! Ваш пол сохранен.\nТеперь можно искать собеседников.",
        reply_markup=main_kb
    )

# Смена своего пола
@dp.message(F.text == "⚙️ Изменить мой пол")
async def change_gender(message: Message):
    await message.answer("Укажите ваш пол:", reply_markup=gender_kb)

@dp.message(F.text == "ℹ️ О боте")
async def about_bot(message: Message):
    await message.answer("🤖 Анонимный чат с фильтрами по полу.", reply_markup=main_kb)

# --- НАЧАЛО ПОИСКА (ВЫБОР КРИТЕРИЕВ) ---
@dp.message(F.text == "🔍 Найти собеседника")
async def start_search_menu(message: Message):
    user_id = message.from_user.id

    if user_id not in users_gender:
        await message.answer("Сначала укажите ваш пол!", reply_markup=gender_kb)
        return

    if user_id in chats:
        await message.answer("Вы уже в диалоге!", reply_markup=in_chat_kb)
        return

    await message.answer("Кого вы хотите найти?", reply_markup=pref_kb)

# --- ОБРАБОТКА ПОИСКА С ФИЛЬТРАМИ ---
@dp.message(F.text.in_({"👨 Искать парня", "👩 Искать девушку", "🎲 Все равно"}))
async def process_search(message: Message):
    user_id = message.from_user.id

    if user_id not in users_gender:
        await message.answer("Сначала укажите ваш пол!", reply_markup=gender_kb)
        return

    # Определяем предпочтение
    if message.text == "👨 Искать парня":
        pref = "M"
    elif message.text == "👩 Искать девушку":
        pref = "F"
    else:
        pref = "ANY"

    user_gender = users_gender[user_id]

    # Ищем совпадение в очереди
    found_partner_id = None
    for item in queue:
        partner_id = item["user_id"]
        partner_gender = item["gender"]
        partner_pref = item["pref"]

        # Проверка совместимости по обоим направлениям
        match_for_user = (pref == "ANY" or pref == partner_gender)
        match_for_partner = (partner_pref == "ANY" or partner_pref == user_gender)

        if match_for_user and match_for_partner:
            found_partner_id = partner_id
            queue.remove(item)
            break

    if found_partner_id:
        # Соединяем
        chats[user_id] = found_partner_id
        chats[found_partner_id] = user_id

        await message.answer("🎉 **Собеседник найден!** Приятного общения.", reply_markup=in_chat_kb, parse_mode="Markdown")
        await bot.send_message(found_partner_id, "🎉 **Собеседник найден!** Приятного общения.", reply_markup=in_chat_kb, parse_mode="Markdown")
    else:
        # Добавляем пользователя в очередь
        # Если уже был в очереди — обновляем
        queue_user = [q for q in queue if q["user_id"] == user_id]
        if queue_user:
            queue.remove(queue_user[0])

        queue.append({"user_id": user_id, "gender": user_gender, "pref": pref})
        await message.answer("🔎 **Ищем подходящего собеседника...**", reply_markup=searching_kb, parse_mode="Markdown")

# --- СЛЕДУЮЩИЙ СОБЕСЕДНИК ---
@dp.message(F.text == "➡️ Следующий")
async def next_partner(message: Message):
    user_id = message.from_user.id

    if user_id in chats:
        partner_id = chats.pop(user_id)
        chats.pop(partner_id, None)
        await bot.send_message(partner_id, "Собеседник перешел к новому поиску.", reply_markup=main_kb)
    
    await start_search_menu(message)

# --- ЖАЛОБА ---
@dp.message(F.text == "⚠️ Пожаловаться")
async def report_partner(message: Message):
    user_id = message.from_user.id

    if user_id in chats:
        partner_id = chats.pop(user_id)
        chats.pop(partner_id, None)

        await message.answer("Жалоба принята. Поиск нового собеседника...", reply_markup=main_kb)
        await bot.send_message(partner_id, "На вас поступила жалоба. Диалог завершен.", reply_markup=main_kb)
        await start_search_menu(message)

# --- ОСТАНОВКА ПОИСКА И ЗАВЕРШЕНИЕ ---
@dp.message(F.text == "🛑 Остановить поиск")
async def stop_search(message: Message):
    user_id = message.from_user.id
    clear_user_state(user_id)
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

# --- ВСПОМОГАТЕЛЬНАЯ ФУНКЦИЯ ОЧИСТКИ ---
def clear_user_state(user_id: int):
    # Удаление из очереди
    for item in list(queue):
        if item["user_id"] == user_id:
            queue.remove(item)
    # Завершение чата
    if user_id in chats:
        partner_id = chats.pop(user_id, None)
        if partner_id:
            chats.pop(partner_id, None)

# --- ПЕРЕСЫЛКА СООБЩЕНИЙ ---
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
        await message.answer("Воспользуйтесь меню ниже для управления ботом.", reply_markup=main_kb)

# ==================== ЗАПУСК ==================== #

async def main():
    print("Бот с фильтрами по полу запущен...")
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        traceback.print_exc()
