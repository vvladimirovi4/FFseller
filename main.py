# coding=utf-8

import asyncio
import os
import re
import sqlite3
import time
import random

from pyrogram.enums import ChatAction, MessageEntityType
import openai
from pyrogram import Client, filters

import configparser

from pyrogram.types import MessageEntity

# Создание объекта ConfigParser
config = configparser.ConfigParser()

# Чтение файла config.ini
config.read('config.ini')

openai_api_key = config.get('Config', 'openai_api_key')
api_id = config.get('Config', 'api_id')
api_hash = config.get('Config', 'api_hash')
assistant_id = config.get('Config', 'assistant_id')
text = config.get('Config', 'text')
client = openai.OpenAI(api_key=openai_api_key)
Assistant_ID = assistant_id

# Инициализация Pyrogram Client
app = Client(name="garmvs", api_id=api_id, api_hash=api_hash)
# Инициализация OpenAI
openai.api_key = openai_api_key
price_sent = {}
chat_sessions = {}
initiated_users = set()

initial_messages = [
    "Привет! Вы ищете фулфилмент? Расскажите о вашем товаре и объеме поставки!",
    "Здравствуйте! Давайте поможем вам с фулфилментом. Какой у вас товар?",
    "Добрый день! Интересуетесь фулфилментом? Уточните количество товара для расчета.",
    "Приветствую! Нужно рассчитать фулфилмент? Какой тип и объем товара?",
    "Здравствуйте! Вы искали фулфилмент? Подскажите, какой объем товара у вас планируется?",
    "Добрый день! Готов помочь с фулфилментом. Укажите тип и количество вашего товара.",
    "Привет! Фулфилмент интересует? Давайте обсудим объем и детали по товару.",
    "Здравствуйте! Готов рассчитать фулфилмент. Подскажите, какой у вас товар?",
    "Приветствую! Какой товар и объем вы планируете? Помогу с фулфилментом.",
    "Добрый день! Интересует фулфилмент? Укажите, какой тип товара и объем поставки."
]

async def send_initial_message(user_id):
    # Set a random delay between 1 and 2 minutes
    delay = random.randint(60, 120)
    typing_start_delay = delay // 2  # Typing starts halfway through the delay

    await asyncio.sleep(typing_start_delay)  # Wait before starting typing status
    await app.send_chat_action(user_id, ChatAction.TYPING)

    await asyncio.sleep(typing_start_delay)  # Complete the remaining delay

    message_text = initial_messages[user_id % len(initial_messages)]
    await app.send_message(user_id, text=message_text)

    thread = client.beta.threads.create()
    chat_sessions[user_id] = thread.id
    price_sent[user_id] = False
    print('dfjn')
    initiated_users.add(user_id)


def transcript(file):
    audio_file = open(file, "rb")
    transcription = client.audio.transcriptions.create(
        model="whisper-1",
        file=audio_file
    )
    return transcription.text


def add_user(chat_id):
    thread = client.beta.threads.create()
    chat_sessions[chat_id] = thread.id
    price_sent[chat_id] = False


async def handle_chat_with_gpt(message, messageText):
    print('генерация началась')
    thread_id = chat_sessions[message.from_user.username]
    price = price_sent[message.from_user.username]
    await app.send_chat_action(message.from_user.username, ChatAction.TYPING)
    message_answer = client.beta.threads.messages.create(
        thread_id=thread_id,
        role="user",
        content=messageText
    )
    run = client.beta.threads.runs.create(
        thread_id=thread_id,
        assistant_id=assistant_id,
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
        print(chat_sessions)
        if 'send' in content:
            await app.send_message(chat_id=-1002196552733,
                                   text=f"Клиент с ником @{message.from_user.username} готов к завершению сделки")
            await app.send_message(chat_id=-1002196552733, text=content)
            await app.send_message(chat_id=message.from_user.username,
                                   text='Передал ваш контакт менеджеру, скоро с вами свяжутся')
        else:
            await app.send_message(chat_id=message.from_user.username, text=content)


keywords_pattern = re.compile(r'\b(фулфилмент|прайс|расценки|доставка|услуги|договор|товары)\b', re.IGNORECASE)


@app.on_message(filters.text & filters.regex(keywords_pattern) & ~filters.private)
async def detect_keywords_in_group(client, message):
    # Проверяем, что сообщение не от бота (если в username есть "bot")
    user_id = message.from_user.username
    if user_id and "bot" not in user_id.lower():
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
    # Проверяем, что сообщение не от бота (если в username есть "bot")
    user_id = message.from_user.username
    if user_id and "bot" not in user_id.lower():
        if user_id in initiated_users:
            await handle_chat_with_gpt(message, message.text)
        else:
            add_user(user_id)
            await handle_chat_with_gpt(message, message.text)


app.run()
