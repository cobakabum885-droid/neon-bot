import telebot
from telebot import types
import time
import os
import threading

# ==========================================
# ⚙️ ГЛОБАЛЬНАЯ КОНФИГУРАЦИЯ
# ==========================================
TOKEN = "8784321725:AAFM683nr7crIQq_CqW_YOp0mh_AMxbyAkA"
bot = telebot.TeleBot(TOKEN)
MY_ID = 6073576320
BOMB_STICKER = "CAACAgIAAxkBAAOqaa1k40iolM-CTEaa6yjSgFsfaAADnSsAAvOcIEuI0tVhzCmjyDoE"

# Списки данных
all_users = {}
admins = set()
banned_users = set()
msg_buffer = {}
user_settings = {}
state_data = {} # Хранение состояний для каждого юзера

# Параметры атаки
attack_config = {
    "target_id": None,
    "type": None,
    "amount": 0,
    "delay": 0.1
}

# ==========================================
# 🖥 МОДУЛЬ ПРОФЕССИОНАЛЬНОГО ЛОГИРОВАНИЯ
# ==========================================
def log_event(level, message):
    timestamp = time.strftime('%H:%M:%S')
    print(f"[{timestamp}] [{level.upper()}] >>> {message}")

def log_action(action, target):
    log_event("ACTION", f"Выполнено: {action} | Цель: {target}")

# ==========================================
# 🗄 МОДУЛЬ УПРАВЛЕНИЯ БАЗОЙ (FILE SYSTEM)
# ==========================================
def load_db():
    log_event("SYSTEM", "Синхронизация баз данных...")
    # Загрузка пользователей
    if os.path.exists("users_v2.txt"):
        with open("users_v2.txt", "r", encoding="utf-8") as f:
            for line in f:
                if " : " in line:
                    uid, name = line.strip().split(" : ", 1)
                    all_users[int(uid)] = name
    # Загрузка админов
    if os.path.exists("admins.txt"):
        with open("admins.txt", "r") as f:
            for line in f:
                if line.strip().isdigit(): admins.add(int(line.strip()))
    # Загрузка банов
    if os.path.exists("bans.txt"):
        with open("bans.txt", "r") as f:
            for line in f:
                if line.strip().isdigit(): banned_users.add(int(line.strip()))
    log_event("SYSTEM", f"База готова. Юзеров: {len(all_users)}")

def save_data(filename, data_set):
    with open(filename, "w", encoding="utf-8") as f:
        if isinstance(data_set, dict):
            for k, v in data_set.items(): f.write(f"{k} : {v}\n")
        else:
            for item in data_set: f.write(f"{item}\n")

# ==========================================
# 🎛 ИНТЕРФЕЙС УПРАВЛЕНИЯ (KEYBOARD)
# ==========================================
def main_menu(uid):
    if uid in banned_users: return types.ReplyKeyboardRemove()
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    
    if uid == MY_ID:
        # Секция Атаки и Рассылки
        markup.row(types.KeyboardButton("🚀 СНОС УДАР"), types.KeyboardButton("📢 РАССЫЛКА"))
        # Секция Наблюдения
        markup.row(types.KeyboardButton("🎯 ЦЕЛИ"), types.KeyboardButton("👤 ЮЗЕРЫ"))
        # Секция Модерации чатов
        markup.row(types.KeyboardButton("🧹 ОЧИСТКА"), types.KeyboardButton("🏃 ВЫХОД"))
        # Секция Управления доступом
        markup.row(types.KeyboardButton("➕ АДМИН"), types.KeyboardButton("🚫 БАН"))
        markup.row(types.KeyboardButton("🔓 РАЗБАН"), types.KeyboardButton("📋 СПИСОК БАН"))
        # Секция Системы
        markup.row(types.KeyboardButton("📊 СТАТУС"), types.KeyboardButton("👥 АДМИНЫ"))
        
        sound = "🔔 ВКЛ ЗВУК" if user_settings.get(uid, False) else "🔕 ЗАГЛУШИТЬ"
        markup.row(types.KeyboardButton(sound))
    elif uid in admins:
        markup.row(types.KeyboardButton("📊 СТАТУС"), types.KeyboardButton("🔕 ЗАГЛУШИТЬ"))
    else:
        markup.row(types.KeyboardButton("👋 ПРИВЕТ"))
    return markup

# ==========================================
# 🚦 ОБРАБОТЧИК КОМАНД
# ==========================================
@bot.message_handler(commands=['start'])
def welcome(message):
    uid = message.from_user.id
    if uid in banned_users: return
    
    all_users[uid] = f"{message.from_user.first_name} (@{message.from_user.username or 'none'})"
    save_data("users_v2.txt", all_users)
    
    bot.send_message(uid, "🛰 **NEON SYSTEM v17.0 ONLINE**\n\nВсе системы проверены. Ожидаю команд.", 
                     reply_markup=main_menu(uid), parse_mode="Markdown")

# ==========================================
# 🕹 ЦЕНТРАЛЬНЫЙ ПРОЦЕССОР (PRIVATE MSGS)
# ==========================================
@bot.message_handler(func=lambda m: m.chat.type == 'private')
def core_logic(message):
    uid, txt = message.from_user.id, message.text
    if uid in banned_users: return
    if uid != MY_ID and uid not in admins: return

    # --- ЛОГИКА ОЖИДАНИЯ ВВОДА (STATE MACHINE) ---
    current_state = state_data.get(uid)

    if current_state == "wait_news":
        bot.send_message(MY_ID, "📡 Запуск глобальной рассылки...")
        for target in all_users.keys():
            try: bot.send_message(target, f"📢 **НОВОСТЬ:**\n\n{txt}", parse_mode="Markdown")
            except: pass
        bot.send_message(MY_ID, "✅ Рассылка завершена.", reply_markup=main_menu(uid))
        state_data[uid] = None; return

    elif current_state == "wait_clear":
        try:
            tid = int(txt)
            if tid in msg_buffer:
                last_mid = msg_buffer[tid]["last_mid"]
                bot.send_message(MY_ID, f"🧹 Запуск очистки в `{tid}`...")
                deleted = 0
                for i in range(101):
                    try: bot.delete_message(tid, last_mid - i); deleted += 1
                    except: continue
                bot.send_message(MY_ID, f"✅ Готово. Удалено: {deleted}", reply_markup=main_menu(uid))
            else: bot.send_message(MY_ID, "❌ Чат не обнаружен в базе радара.")
        except: bot.send_message(MY_ID, "❌ Ошибка ID.")
        state_data[uid] = None; return

    elif current_state == "wait_leave":
        try:
            tid = int(txt)
            chat = bot.get_chat(tid)
            bot.send_message(MY_ID, f"🏃 Покидаю чат: **{chat.title}**...", parse_mode="Markdown")
            bot.leave_chat(tid)
            bot.send_message(MY_ID, "✅ Бот вышел из чата.", reply_markup=main_menu(uid))
        except Exception as e: bot.send_message(MY_ID, f"❌ Ошибка выхода: {e}")
        state_data[uid] = None; return

    # --- ЛОГИКА СНОС УДАР (АТАКА) ---
    elif current_state == "bomb_target":
        if txt == "👥 ВСЕМ":
            attack_config["type"] = "all"
            state_data[uid] = "bomb_count"
            bot.send_message(MY_ID, "🔢 Количество стикеров на каждого?")
        elif txt == "👤 ОДНОМУ":
            attack_config["type"] = "single"
            state_data[uid] = "bomb_id"
            bot.send_message(MY_ID, "🆔 Введи ID цели:")
        return

    elif current_state == "bomb_id":
        try: attack_config["target_id"] = int(txt); state_data[uid] = "bomb_count"; bot.send_message(MY_ID, "🔢 Количество стикеров?")
        except: bot.send_message(MY_ID, "❌ Ошибка ID."); state_data[uid] = None
        return

    elif current_state == "bomb_count":
        try:
            attack_config["amount"] = int(txt)
            bot.send_message(MY_ID, "🚀 АТАКА ИНИЦИИРОВАНА!")
            targets = all_users.keys() if attack_config["type"] == "all" else [attack_config["target_id"]]
            for t in targets:
                if int(t) == MY_ID: continue
                try:
                    for _ in range(attack_config["amount"]):
                        bot.send_sticker(t, BOMB_STICKER)
                        time.sleep(0.1)
                except: pass
            bot.send_message(MY_ID, "✅ СНОС ЗАВЕРШЕН.", reply_markup=main_menu(uid))
        except: bot.send_message(MY_ID, "❌ Ошибка."); state_data[uid] = None
        return

    # --- ОБРАБОТКА НАЖАТИЙ КНОПОК ---
    if txt == "🚀 СНОС УДАР":
        state_data[uid] = "bomb_target"
        kb = types.ReplyKeyboardMarkup(resize_keyboard=True); kb.row("👥 ВСЕМ", "👤 ОДНОМУ")
        bot.send_message(MY_ID, "🎯 Выбери режим обстрела:", reply_markup=kb)
        
    elif txt == "📢 РАССЫЛКА":
        state_data[uid] = "wait_news"
        bot.send_message(MY_ID, "📝 Введи текст новости:", reply_markup=types.ReplyKeyboardRemove())
        
    elif txt == "🧹 ОЧИСТКА":
        state_data[uid] = "wait_clear"
        bot.send_message(MY_ID, "🆔 Введи ID чата для зачистки (с минусом):", reply_markup=types.ReplyKeyboardRemove())
        
    elif txt == "🏃 ВЫХОД":
        state_data[uid] = "wait_leave"
        bot.send_message(MY_ID, "🆔 Введи ID чата для выхода:", reply_markup=types.ReplyKeyboardRemove())

    elif txt == "📊 СТАТУС":
        report = (f"📈 **STATUS REPORT:**\n"
                  f"• Юзеров: `{len(all_users)}`\n"
                  f"• Целей: `{len(msg_buffer)}`\n"
                  f"• Админов: `{len(admins)}`\n"
                  f"• Банов: `{len(banned_users)}`")
        bot.send_message(MY_ID, report, parse_mode="Markdown")

    elif txt == "🎯 ЦЕЛИ":
        res = "📍 **АКТИВНЫЕ ID В БАЗЕ:**\n" + "\n".join([f"• `{c}`" for c in msg_buffer.keys()]) or "Пусто."
        bot.send_message(MY_ID, res, parse_mode="Markdown")

    elif txt == "👤 ЮЗЕРЫ":
        res = "👤 **DATABASE:**\n" + "".join([f"• `{k}` : {v}\n" for k, v in all_users.items()])[:4000]
        bot.send_message(MY_ID, res, parse_mode="Markdown")

    # (Здесь могут быть остальные админ-команды...)

# ==========================================
# 📡 МОДУЛЬ РАДАРА (GROUP INTERCEPTION)
# ==========================================
@bot.message_handler(func=lambda m: m.chat.type != 'private', content_types=['text', 'photo', 'sticker', 'video', 'voice'])
def group_radar(message):
    cid = message.chat.id
    name = message.from_user.first_name
    content = message.text if message.content_type == 'text' else f"[{message.content_type.upper()}]"
    
    # Сохраняем расширенные данные для СИСТЕМЫ ОЧИСТКИ
    msg_buffer[cid] = {
        "user": name,
        "text": content,
        "last_mid": message.message_id # Маяк для функции delete_message
    }
    
    # Уведомление владельца
    if not user_settings.get(MY_ID, False):
        report = (f"🛰 **ПЕРЕХВАТ:**\n"
                  f"📍 Чат: `{message.chat.title}`\n"
                  f"🆔 ID чата: `{cid}`\n"
                  f"👤 {name}: {content}")
        try: bot.send_message(MY_ID, report, parse_mode="Markdown")
        except: pass
    log_event("RADAR", f"Данные из чата {cid} обновлены.")

# ==========================================
# 🚀 ЗАПУСК ЯДРА NEON
# ==========================================
if __name__ == "__main__":
    os.system('clear')
    print("="*50)
    print("      🛰 NEON SYSTEM v17.0 ULTIMATUM 🛰      ")
    print("      DECRYPTING... SUCCESS. ACTIVE.        ")
    print("="*50)
    load_db()
    
    try:
        log_event("SYSTEM", "Infinity Polling запущен.")
        bot.infinity_polling(timeout=10, long_polling_timeout=5)
    except Exception as e:
        log_event("ERROR", f"Критический сбой: {e}")
