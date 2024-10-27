import os
import json
import asyncio
import re
from telethon import TelegramClient, events
from telethon.tl.functions.channels import JoinChannelRequest

# Automatically find the .json file
json_files = [f for f in os.listdir('.') if f.endswith('.json')]

if json_files:
    with open(json_files[0], 'r') as f:
        config_data = json.load(f)
else:
    print("No .json file found in the current directory.")
    exit()

# Automatically find the .session file
session_files = [f for f in os.listdir('.') if f.endswith('.session')]

if session_files:
    session_name = session_files[0].replace('.session', '')
else:
    print("No .session file found in the current directory.")
    exit()

# Extract data from the .json file
api_id = int(config_data['app_id'])
api_hash = config_data['app_hash']

# Proxy configuration
proxy_string = '185.162.130.86:10001:iIdwRjvyHuUDWFJAkRNV:RNW78Fm5'

# Parse the proxy string
proxy_parts = proxy_string.split(':')

if len(proxy_parts) == 4:
    proxy_ip = proxy_parts[0]
    proxy_port = int(proxy_parts[1])
    proxy_username = proxy_parts[2]
    proxy_password = proxy_parts[3]
else:
    raise ValueError('Invalid proxy string format. Expected format is ip:port:username:password')

# Initialize the Telegram client with proxy
client = TelegramClient(
    session_name,
    api_id,
    api_hash,
    proxy=('socks5', proxy_ip, proxy_port, True, proxy_username, proxy_password)
)

# The chat ID where notifications will be sent
notification_chat_id = -1002196552733  # Replace with your actual group/chat ID

# Regular expression for detecting keywords (if needed)
keywords_pattern = re.compile(r'\b(фулфилмент|прайс|расценки|доставка)\b', re.IGNORECASE)

@client.on(events.NewMessage())
async def message_handler(event):
    # Forward the message to the notification group
    await client.forward_messages(notification_chat_id, event.message)

    # Optionally, send a notification message in the group
    sender = await event.get_sender()
    sender_username = f"@{sender.username}" if sender.username else "Анонимный пользователь"
    message_text = event.message.message

    # Get information about the chat where the message came from
    if event.is_group or event.is_channel:
        chat = await event.get_chat()
        chat_title = chat.title
        chat_username = chat.username
        chat_link = f"https://t.me/{chat_username}" if chat_username else "Ссылка недоступна"
    else:
        chat_title = "Личное сообщение"
        chat_link = "Ссылка недоступна"

    notification_text = (
        f"Сообщение из чата: {chat_title}\n"
        f"Ссылка на чат: {chat_link}\n"
        f"Отправитель: {sender_username}\n"
        f"Текст сообщения: {message_text}"
    )

    await client.send_message(notification_chat_id, notification_text)

async def main():
    # Join the group @FFsellerrs at startup
    try:
        await client(JoinChannelRequest('@FFsellerrs'))
        print("Successfully joined the group @FFsellerrs.")
    except Exception as e:
        print(f"Failed to join the group @FFsellerrs: {e}")

    # Keep the client running
    await client.run_until_disconnected()

if __name__ == '__main__':
    with client:
        client.loop.run_until_complete(main())
