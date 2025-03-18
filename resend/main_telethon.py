import os
from pyrogram import Client, filters, idle
from pyrogram.types import Message

# Файл для хранения ID канала
CHANNEL_ID_FILE = "ffseller_channel_id.txt"

def load_channel_id():
    if os.path.exists(CHANNEL_ID_FILE):
        try:
            with open(CHANNEL_ID_FILE, "r") as f:
                return int(f.read().strip())
        except Exception as e:
            print(f"Ошибка при чтении channel_id: {e}")
    return None

def save_channel_id(channel_id: int):
    with open(CHANNEL_ID_FILE, "w") as f:
        f.write(str(channel_id))

# Указываем API ID и API Hash
api_id = 21564722
api_hash = 'a37810f1f9432966784ac36e1df673bd'

# Список ключевых слов для фильтрации сообщений
keywords = ["фулфилмент", "прайс", "расценки", "доставка"]

# Глобальная переменная для хранения ID канала
target_channel_id = None

# Инициализируем клиента
app = Client("my_account", api_id=api_id, api_hash=api_hash)

@app.on_message(filters.text)
async def forward_to_channel(client: Client, message: Message):
    if any(keyword.lower() in message.text.lower() for keyword in keywords):
        chat_title = message.chat.title or "Без названия"
        if message.chat.username:
            chat_link = f"https://t.me/{message.chat.username}"
        else:
            chat_link = await client.export_chat_invite_link(message.chat.id) if message.chat.type in ["supergroup", "channel"] else "Прямая ссылка не доступна"
        sender_username = f"@{message.from_user.username}" if message.from_user and message.from_user.username else "Без никнейма"

        formatted_message = (
            f"Сообщение из чата: {chat_title}\n"
            f"Ссылка на чат: {chat_link}\n"
            f"Отправитель: {sender_username}\n"
            f"Текст сообщения: {message.text}"
        )

        if target_channel_id is not None:
            await message.forward(target_channel_id)
            await app.send_message(target_channel_id, formatted_message)
        else:
            print("Целевой канал не определён!")

async def setup_ffseller_channel():
    """
    Создаёт канал "FFseller заявки" (если его ещё нет) и добавляет в него пользователей
    с никнеймами @garmvs и @process_admins, если они еще не добавлены.
    При повторном запуске используется сохранённый ID канала.
    """
    global target_channel_id

    # Попытка загрузить сохранённый ID канала
    saved_channel_id = load_channel_id()
    if saved_channel_id:
        try:
            chat = await app.get_chat(saved_channel_id)
            if chat and chat.title == "FFseller заявки":
                target_channel_id = saved_channel_id
                print("Канал 'FFseller заявки' найден по сохранённому ID.")
        except Exception as e:
            print(f"Не удалось получить канал по сохранённому ID: {e}")

    # Если канал не найден по сохранённому ID, ищем его среди диалогов
    if target_channel_id is None:
        dialogs = [dialog async for dialog in app.get_dialogs()]
        ffseller_channel = None
        for dialog in dialogs:
            if dialog.chat.type == "channel" and dialog.chat.title == "FFseller заявки":
                ffseller_channel = dialog.chat
                break

        if ffseller_channel:
            target_channel_id = ffseller_channel.id
            print("Канал 'FFseller заявки' найден среди диалогов.")
        else:
            # Если канал не найден, создаём новый
            ffseller_channel = await app.create_channel("FFseller заявки", description="Канал для заявок FFseller")
            target_channel_id = ffseller_channel.id
            print("Создан канал 'FFseller заявки'.")
        save_channel_id(target_channel_id)

    # Добавляем пользователей в канал
    usernames = ["@garmvs", "@process_admins"]
    users = await app.get_users(usernames)
    for user in users:
        try:
            await app.add_chat_members(target_channel_id, user.id)
            print(f"Приглашён пользователь {user.username} в канал 'FFseller заявки'.")
        except Exception as e:
            print(f"Не удалось пригласить пользователя {user.username}: {e}")
        try:
            await app.promote_chat_member(
                target_channel_id,
                user.id,

            )
            print(f"Пользователь {user.username} назначен администратором в канале 'FFseller заявки'.")
        except Exception as e:
            print(f"Не удалось назначить администратора {user.username}: {e}")

async def main():
    async with app:
        await setup_ffseller_channel()
        print("Бот запущен и готов к работе.")
        await idle()

app.run(main())