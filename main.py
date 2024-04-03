# coding=utf-8

import asyncio
import os
import re
import sqlite3
import time

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


chat_sessions = {}
# Список пользователей, которым бот уже отправлял сообщения
initiated_users = set()
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
async def handle_chat_with_gpt(message, messageText):
    print('генерация началась')
    thread_id = chat_sessions[message.from_user.username]
    message_answer = client.beta.threads.messages.create(
        thread_id=thread_id,
        role="user",
        content=messageText

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
        if content == '.':
            initiated_users.remove(message.from_user.username)
        if message.from_user.username in initiated_users:
            await app.send_message(chat_id=message.from_user.username, text=content)


keywords_pattern = re.compile(r'\b(фулфилмент|прайс|расценки|доставка|услуги|договор|товары)\b',
                              re.IGNORECASE)
@app.on_message(filters.text & filters.regex(keywords_pattern) & ~filters.private)
async def detect_keywords_in_group(client, message):
    user_id = message.from_user.username
    messageText = message.text
    if user_id not in initiated_users:
        add_user(user_id)
        await handle_chat_with_gpt(message, messageText)

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
    if message.voice:
        # Если сообщение является голосовым сообщением
        # Скачиваем голосовое сообщение
        file_path = await message.download()
        print(f"Скачано голосовое сообщение: {file_path}")
        messageText = transcript(file_path)
        print('Завершена транскрибация')
        os.remove(file_path)
    else:
        messageText = message.text

    if user_id in initiated_users:
        await handle_chat_with_gpt(message, messageText)
    else:
        add_user(user_id)
        await handle_chat_with_gpt(message, messageText)

app.run()