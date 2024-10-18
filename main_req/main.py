import random
import asyncio
import os
import re
import time
import json
import configparser
from telethon.tl.functions.channels import JoinChannelRequest
import openai
from telethon import TelegramClient, events

# Read the config.ini file for OpenAI API key and assistant_id
config = configparser.ConfigParser()
config.read('config.ini')

openai_api_key = config.get('Config', 'openai_api_key')
assistant_id = config.get('Config', 'assistant_id')
text = config.get('Config', 'text')
Assistant_ID = assistant_id

# Search for the .json file in the current directory to get api_id and api_hash
json_files = [f for f in os.listdir('.') if f.endswith('.json')]
if not json_files:
    raise FileNotFoundError("No .json file found in the current directory.")
json_file = json_files[0]  # Assuming there is only one .json file

with open(json_file, 'r', encoding='utf-8') as f:
    data = json.load(f)
api_id = data['app_id']
api_hash = data['app_hash']

# Initialize OpenAI
openai.api_key = openai_api_key
openai_client = openai.OpenAI(api_key=openai_api_key)

price_sent = {}
chat_sessions = {}
initiated_users = set()
ready_clients = []

# Search for the .session file in the current directory
session_files = [f for f in os.listdir('.') if f.endswith('.session')]
if not session_files:
    raise FileNotFoundError("No .session file found in the current directory.")
session_file = session_files[0]  # Use the first .session file found

# Proxy configuration
proxy = ('185.162.130.86', 10000, 'QPZVilhv6aR2014xtUIJ', 'RNW78Fm5')

# Initialize Telethon Client using the existing .session file and proxy
client = TelegramClient(session_file, api_id, api_hash, proxy=('socks5', proxy[0], proxy[1], True, proxy[2], proxy[3]))
async def handle_chat_with_gpt(event, messageText):
    print('Generating response')
    message = event.message
    print(message.text)
    sender = await event.get_sender()
    username = sender.username
    thread_id = chat_sessions.get(username)
    if not thread_id:
        thread = openai_client.beta.threads.create()
        chat_sessions[username] = thread.id
        thread_id = thread.id

    openai_client.beta.threads.messages.create(
        thread_id=thread_id,
        role="user",
        content=messageText
    )
    run = openai_client.beta.threads.runs.create(
        thread_id=thread_id,
        assistant_id=Assistant_ID,
    )

    time.sleep(10)
    run_status = openai_client.beta.threads.runs.retrieve(
        thread_id=thread_id,
        run_id=run.id
    )

    print(run_status.status)
    while run_status.status == 'in_progress':
        time.sleep(5)
        run_status = openai_client.beta.threads.runs.retrieve(
            thread_id=thread_id,
            run_id=run.id
        )
    print(run_status.status)
    if run_status.status == 'completed':
        messages = openai_client.beta.threads.messages.list(
            thread_id=thread_id
        )

        msg = messages.data[0]
        role = msg.role
        content = msg.content[0].text.value
        print(f"{role.capitalize()}: {content}")
        print(chat_sessions)
        if username not in ready_clients:
            if 'send' in content.lower():
                ready_clients.append(username)
                await client.send_message(-1002196552733,
                                       f"Клиент с ником @{username} готов к завершению сделки: {content}")
                await client.send_message(event.chat_id,
                                       'Я передал ваш контакт нашему менеджеру, скоро он с вами свяжется')
            else:
                await client.send_message(event.chat_id, content)

async def send_initial_message(user_id):
    messages = [
        "Привет! Вы искали фулфилмент? Давайте сделаем расчет, какой у Вас товар и какое количество планируете в поставке?",
        # ... (other messages)
    ]
    selected_message = random.choice(messages)

    await client.send_message(user_id, selected_message)

    thread = openai_client.beta.threads.create()
    chat_sessions[user_id] = thread.id
    price_sent[user_id] = False
    print('Message sent to user')
    initiated_users.add(user_id)

def add_user(chat_id):
    thread = openai_client.beta.threads.create()
    chat_sessions[chat_id] = thread.id
    price_sent[chat_id] = False

keywords_pattern = re.compile(r'\b(фулфилмент|прайс|расценки|доставка)\b', re.IGNORECASE)

@client.on(events.NewMessage(pattern=keywords_pattern, incoming=True))
async def detect_keywords_in_group(event):
    sender = await event.get_sender()
    user_id = sender.username

    if sender.bot:
        return

    if event.is_private:
        # Handle private messages
        if user_id not in initiated_users:
            await send_initial_message(user_id)
    else:
        # Handle group messages
        print(event.message.text)
        if user_id not in initiated_users:
            await client.forward_messages(-1002196552733, event.message)
            group = await event.get_chat()
            group_title = group.title
            group_username = group.username
            group_link = f"https://t.me/{group_username}" if group_username else "Ссылка недоступна"
            message_link = f"https://t.me/c/{abs(event.chat_id)}/{event.message.id}" if event.chat_id else "Ссылка на сообщение недоступна"
            sender_username = user_id if user_id else "Анонимный пользователь"

            match = keywords_pattern.search(event.message.text)
            detected_keyword = match.group(0) if match else "Неопределенное слово"
            await client.send_message(-1002196552733,
                                      f"Сообщение из группы: {group_title}\nСсылка на группу: {group_link}\nСсылка на сообщение: {message_link}\nОтправитель: @{sender_username}\nОбнаруженное слово: {detected_keyword}")
            await send_initial_message(user_id)
            print(f"Сообщение из группы: {group_title}")
            print(f"Ссылка на группу: {group_link}")
            print(f"Ссылка на сообщение: {message_link}")
            print(f"Отправитель: @{sender_username}")
            print(f"Обнаруженное слово: {detected_keyword}")

@client.on(events.NewMessage(pattern='/stopchat'))
async def stop_chat(event):
    sender = await event.get_sender()
    user_id = sender.username
    if user_id in initiated_users:
        initiated_users.remove(user_id)
        await event.reply("Общение с виртуальным помощником прекращено.")

@client.on(events.NewMessage(pattern='/startchat'))
async def start_chat(event):
    sender = await event.get_sender()
    user_id = sender.username
    if user_id not in initiated_users:
        initiated_users.add(user_id)
        await event.reply("Общение с виртуальным помощником возобновлено.")

@client.on(events.NewMessage(incoming=True))
async def private_message_handler(event):
    if not event.is_private:
        return
    if event.text.startswith('/start'):
        return
    sender = await event.get_sender()
    user_id = sender.username
    if user_id in initiated_users:
        await handle_chat_with_gpt(event, event.message.text)
    else:
        add_user(user_id)
        await handle_chat_with_gpt(event, event.message.text)

async def main():
    await client.start()
    try:
        await client(JoinChannelRequest('@FFsellerrs'))
        print("Successfully joined the group @FFsellerrs.")
    except Exception as e:
        print(f"Failed to join the group @FFsellerrs: {e}")
    print("Bot is running...")
    await client.run_until_disconnected()

if __name__ == '__main__':
    asyncio.run(main())
