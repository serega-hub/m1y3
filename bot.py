import telebot # библиотека telebot
import json
import os
from datetime import datetime
from config import token # импорт токена
import requests
import time
import random
bot = telebot.TeleBot(token) 

BANS_FILE = "banned_users.json"

def load_bans():
    if not os.path.exists(BANS_FILE):
        return []
    with open(BANS_FILE, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return []

def save_bans(bans):
    with open(BANS_FILE, "w", encoding="utf-8") as f:
        json.dump(bans, f, ensure_ascii=False, indent=2)

def record_ban(info):
    bans = load_bans()
    bans.append(info)
    save_bans(bans)

@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, "Привет! Я бот для управления чатом.")

@bot.message_handler(commands=['poll'])
def send_poll(message):
    question = "Какая соцсеть тебе нравится больше?"
    options = ["Telegram", "Instagram", "TikTok", "ВКонтакте"]

    bot.send_poll(
        chat_id=message.chat.id,
        question=question,
        options=options,
        is_anonymous=True,
        allows_multiple_answers=False
    )


@bot.message_handler(commands=['ban'])
def ban_user(message):
    if message.reply_to_message: #проверка на то, что эта команда была вызвана в ответ на сообщение 
        chat_id = message.chat.id # сохранение id чата
         # сохранение id и статуса пользователя, отправившего сообщение
        user_id = message.reply_to_message.from_user.id
        user_status = bot.get_chat_member(chat_id, user_id).status 
         # проверка пользователя
        if user_status == 'administrator' or user_status == 'creator':
            bot.reply_to(message, "Невозможно забанить администратора.")
        else:
            bot.ban_chat_member(chat_id, user_id) # пользователь с user_id будет забанен в чате с chat_id
            bot.reply_to(message, f"Пользователь @{message.reply_to_message.from_user.username} был забанен.")
    else:
        bot.reply_to(message, "Эта команда должна быть использована в ответ на сообщение пользователя, которого вы хотите забанить.")


@bot.message_handler(content_types=['new_chat_members'])
def make_some(message):
    bot.send_message(message.chat.id, 'I accepted a new user!')
    bot.approve_chat_join_request(message.chat.id, message.from_user.id)

@bot.message_handler(func=lambda message: True)
def catch_all(message):
    # Получаем текст (если нет текста — пустая строка)
    text = message.text or ""
    # Ищем подстроку "https://"
    if "https://" in text:
        user = message.from_user
        chat_id = message.chat.id
        msg_id = message.message_id

        # Собираем информацию для логирования
        user_info = {
            "date_utc": datetime.utcnow().isoformat() + "Z",
            "chat_id": chat_id,
            "message_id": msg_id,
            "user_id": user.id,
            "username": user.username,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "message_text": text
        }

        # Записываем в файл
        try:
            record_ban(user_info)
            print(f"[BAN LOGGED] {user_info}")
        except Exception as e:
            print(f"Ошибка при записи в файл ban log: {e}")

        # Удаляем сообщение, если можем
        try:
            bot.delete_message(chat_id, msg_id)
        except Exception as e:
            print(f"Не удалось удалить сообщение: {e}")

        # Пытаемся забанить (kick/ban)
        try:
            # В разных версиях pyTelegramBotAPI метод называется kick_chat_member
            # или ban_chat_member; kick_chat_member обычно работает.
            bot.kick_chat_member(chat_id, user.id)
            # Если хотите дополнительно отправить уведомление в чат (опционально)
            bot.send_message(chat_id, f"Пользователь @{user.username or user.first_name} был забанен за ссылку.")
        except Exception as e:
            # Логируем ошибку и сообщаем, что не удалось забанить
            print(f"Не удалось забанить пользователя {user.id}: {e}")
            try:
                bot.send_message(chat_id, f"Не удалось забанить пользователя (нужны права): {e}")
            except:
                pass



bot.infinity_polling(none_stop=True)





