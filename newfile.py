import telebot
import sqlite3
import threading
from telebot.types import ReplyKeyboardMarkup, KeyboardButton, BotCommand

TOKEN = "8978367040:AAGQ6pSo6ZD2yAjZDB20UgEfTOksxyZx4ik"
ADMIN_ID = 5453755061  # <- поставь свой ID

bot = telebot.TeleBot(TOKEN)

db_lock = threading.Lock()
DB_NAME = "bot.db"


# ---------- МЕНЮ КОМАНД (//start /admin /ref) ----------
bot.set_my_commands([
    BotCommand("start", "Запустить бота"),
    BotCommand("admin", "Админ панель"),
    BotCommand("ref", "Реферальная система"),
])


# ---------- БАЗА ----------
def init_db():
    conn = sqlite3.connect(DB_NAME, timeout=10)
    conn.execute("PRAGMA journal_mode=WAL;")

    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            ref_id INTEGER
        )
    """)

    conn.commit()
    conn.close()


def get_conn():
    conn = sqlite3.connect(DB_NAME, timeout=10, check_same_thread=False)
    conn.execute("PRAGMA journal_mode=WAL;")
    return conn


def add_user(user_id, ref_id=None):
    with db_lock:
        conn = get_conn()
        cur = conn.cursor()

        cur.execute(
            "INSERT OR IGNORE INTO users (user_id, ref_id) VALUES (?, ?)",
            (user_id, ref_id)
        )

        conn.commit()
        conn.close()


def count_users():
    with db_lock:
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM users")
        count = cur.fetchone()[0]
        conn.close()
        return count


def get_ref_count(user_id):
    with db_lock:
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM users WHERE ref_id = ?", (user_id,))
        count = cur.fetchone()[0]
        conn.close()
        return count


# ---------- UI ----------
def main_menu():
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(
        KeyboardButton("👤 Профиль"),
        KeyboardButton("📊 Статистика")
    )
    markup.add(
        KeyboardButton("🔗 Рефералка"),
        KeyboardButton("⚙️ Админ")
    )
    return markup


# ---------- /START ----------
@bot.message_handler(commands=['start'])
def start(message):
    args = message.text.split()

    ref_id = None
    if len(args) > 1:
        ref_id = args[1]

    add_user(message.from_user.id, ref_id)

    bot.send_message(
        message.chat.id,
        "👋 <b>Добро пожаловать!</b>\n\n"
        "Я — твой бот 🤖\n"
        "Выбери действие ниже 👇",
        parse_mode="HTML",
        reply_markup=main_menu()
    )


# ---------- /REF ----------
@bot.message_handler(commands=['ref'])
def ref(message):
    bot.send_message(
        message.chat.id,
        f"🔗 <b>Твоя реферальная ссылка:</b>\n\n"
        f"https://t.me/YourBot?start={message.from_user.id}\n\n"
        f"👥 Приглашено: {get_ref_count(message.from_user.id)}",
        parse_mode="HTML"
    )


# ---------- /ADMIN ----------
@bot.message_handler(commands=['admin'])
def admin_cmd(message):
    if message.from_user.id != ADMIN_ID:
        bot.send_message(message.chat.id, "⛔ Нет доступа")
        return

    bot.send_message(
        message.chat.id,
        f"⚙️ <b>Админ панель</b>\n\n"
        f"👥 Пользователей: {count_users()}",
        parse_mode="HTML"
    )


# ---------- КНОПКИ ----------
@bot.message_handler(func=lambda m: m.text == "👤 Профиль")
def profile(message):
    bot.send_message(
        message.chat.id,
        f"👤 <b>Профиль</b>\n\n"
        f"🆔 ID: <code>{message.from_user.id}</code>\n"
        f"👤 Имя: {message.from_user.first_name}\n"
        f"🔗 Рефералов: {get_ref_count(message.from_user.id)}",
        parse_mode="HTML"
    )


@bot.message_handler(func=lambda m: m.text == "📊 Статистика")
def stats(message):
    bot.send_message(
        message.chat.id,
        f"📊 <b>Статистика</b>\n\n"
        f"👥 Всего пользователей: <b>{count_users()}</b>",
        parse_mode="HTML"
    )


@bot.message_handler(func=lambda m: m.text == "🔗 Рефералка")
def ref_btn(message):
    bot.send_message(
        message.chat.id,
        f"🔗 <b>Реферальная система</b>\n\n"
        f"https://t.me/YourBot?start={message.from_user.id}\n\n"
        f"👥 Ты пригласил: {get_ref_count(message.from_user.id)}",
        parse_mode="HTML"
    )


@bot.message_handler(func=lambda m: m.text == "⚙️ Админ")
def admin_btn(message):
    if message.from_user.id != ADMIN_ID:
        bot.send_message(message.chat.id, "⛔ Нет доступа")
        return

    bot.send_message(
        message.chat.id,
        "⚙️ Админ панель активна\n\n"
        f"👥 Пользователей: {count_users()}",
        parse_mode="HTML"
    )


# ---------- ЗАПУСК ----------
init_db()

print("Bot started...")
bot.infinity_polling()