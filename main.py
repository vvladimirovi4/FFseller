# coding=utf-8

import asyncio
import re
import sqlite3
import time

from pyrogram.enums import ChatAction, MessageEntityType
import openai
from pyrogram import Client, filters
Assistant_ID = 'asst_WV5VRUEFAMd7EdQ811ju4NDc'
import configparser

from pyrogram.types import MessageEntity
client = openai.OpenAI(api_key="")
# Создание объекта ConfigParser
config = configparser.ConfigParser()

# Чтение файла config.ini
config.read('config.ini')

# Получение значений переменных из секции 'Config'
openai_api_key = config.get('Config', 'openai_api_key')
api_id = config.get('Config', 'api_id')
api_hash = config.get('Config', 'api_hash')

# Инициализация Pyrogram Client
app = Client(name="garmvs", api_id=api_id, api_hash=api_hash)

# Инициализация OpenAI
openai.api_key = openai_api_key

# Словарь для отслеживания чат-сессий пользователей
chat_sessions = {}
# Список пользователей, которым бот уже отправлял сообщения
initiated_users = set()



async def send_initial_message(user_id):
    await app.send_message(user_id,text='''Вопрос с Фулфилментом еще актуален?\n\nМы работаем с разными маркетплейсами.\nГотовы сопроводить вас на любом этапе, начиная от бесплатных консультаций,забора товара до упаковки и отправки на склад маркетплейса. \n\nНаша компания состоит из слаженной команды, которая со всей заботой и вниманием относится к каждому клиенту. \n\nОбратившись к нам вы получите: \n\n🔝Индивидуальный подход на каждом этапе \n\n🔝Грамотная упаковка, проверка на брак и внимание к вашим требованиям. \n\n🔝Соблюдение сроков на каждом этапе работы \n\n🔝Гарантия качества и ответственность за нашу работу\n\nНаш тг канал:\nhttps://t.me/filsender\n\nФулфилмент FilSender 🛒😁🛒👏\n📞 +7(965)406-46-00 Дамир''', entities=[MessageEntity(type=MessageEntityType.BOLD, offset=0, length=35),
MessageEntity(type=MessageEntityType.CUSTOM_EMOJI, offset=355, length=2, custom_emoji_id=5463071033256848094),
MessageEntity(type=MessageEntityType.CUSTOM_EMOJI, offset=397, length=2, custom_emoji_id=5463071033256848094),
MessageEntity(type=MessageEntityType.CUSTOM_EMOJI, offset=470, length=2, custom_emoji_id=5463071033256848094),
MessageEntity(type=MessageEntityType.CUSTOM_EMOJI, offset=515, length=2, custom_emoji_id=5463071033256848094),
MessageEntity(type=MessageEntityType.URL, offset=583, length=22),
MessageEntity(type=MessageEntityType.BOLD, offset=607, length=10),
MessageEntity(type=MessageEntityType.CUSTOM_EMOJI, offset=628, length=2, custom_emoji_id=5472351783273637250),
MessageEntity(type=MessageEntityType.CUSTOM_EMOJI, offset=630, length=2, custom_emoji_id=5343787039689027387),
MessageEntity(type=MessageEntityType.CUSTOM_EMOJI, offset=632, length=2, custom_emoji_id=5440742314328728853),
MessageEntity(type=MessageEntityType.CUSTOM_EMOJI, offset=634, length=2, custom_emoji_id=5343671578083209613),
MessageEntity(type=MessageEntityType.PHONE_NUMBER, offset=640, length=16),
MessageEntity(type=MessageEntityType.BOLD, offset=640, length=16),
MessageEntity(type=MessageEntityType.BOLD, offset=656, length=6),
])


    thread = client.beta.threads.create()

    chat_sessions[user_id] = thread.id
    print('dfjn')
    initiated_users.add(user_id)




def add_user(chat_id):

    thread = client.beta.threads.create()
    chat_sessions[chat_id] = thread.id

async def handle_chat_with_gpt(message, chat_id):
    print('генерация началась')

    thread_id = chat_sessions[chat_id]
    message_answer = client.beta.threads.messages.create(
        thread_id=thread_id,
        role="user",
        content=message.text

    )
    run = client.beta.threads.runs.create(
        thread_id=thread_id,
        assistant_id=Assistant_ID,

    )

    time.sleep(10)
    run_status = client.beta.threads.runs.retrieve(
        thread_id=thread_id,
        run_id=run.id
    )

    print(run_status.status)
    while run_status.status == 'in_progress':
        time.sleep(5)
        run_status = client.beta.threads.runs.retrieve(
            thread_id=thread_id,
            run_id=run.id
        )
    print(run_status.status)
    if run_status.status == 'completed':
        messages = client.beta.threads.messages.list(
            thread_id=thread_id
        )

        msg = messages.data[0]
        role = msg.role
        content = msg.content[0].text.value
        print(f"{role.capitalize()}: {content}")
        await app.send_message(chat_id=message.chat.id, text=content)


# Регулярное выражение для определения ключевых слов
keywords_pattern = re.compile(r'\b(фулфилмент|прайс|расценки|доставка|услуги|договор|товары)\b',
                              re.IGNORECASE)


@app.on_message(filters.text & filters.regex(keywords_pattern) & ~filters.private)
async def detect_keywords_in_group(client, message):
    user_id = message.from_user.username
    if user_id not in initiated_users:
        await send_initial_message(user_id)


@app.on_message(filters.command("stopchat"))
async def stop_chat(client, message):
    user_id = message.from_user.username
    if user_id in initiated_users:
        initiated_users.remove(user_id)
        await message.reply_text("Общение с виртуальным помощником прекращено.")


@app.on_message(filters.command("startchat"))
async def start_chat(client, message):
    user_id = message.from_user.username
    if user_id not in initiated_users:
        initiated_users.add(user_id)
        await message.reply_text("Общение с виртуальным помощником возобновлено.")


@app.on_message(filters.private & ~filters.command("start"))
async def private_message_handler(client, message):
    user_id = message.from_user.username
    if user_id in initiated_users:
        await handle_chat_with_gpt(message, user_id)


# Запуск бота
app.run()