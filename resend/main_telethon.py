import re
from pyrogram import Client, filters
from pyrogram.types import Message
import asyncio

# Данные для авторизации
api_id = 21564722  # Ваш API ID
api_hash = 'a37810f1f9432966784ac36e1df673bd'  # Ваш API Hash

# ID чата для отправки уведомлений
notification_chat_id = -1002196552733  # Замените на ID вашего чата/группы
group_username = "@FFsellerrs"  # Название группы

# Регулярное выражение для поиска ключевых слов
keywords_pattern = re.compile(r'\b(фулфилмент|прайс|расценки|доставка)\b', re.IGNORECASE)

# Инициализация клиента
app = Client("my_account", api_id=api_id, api_hash=api_hash)


@app.on_message(filters.all)
async def message_handler(client, message: Message):
    # Проверка на наличие ключевого слова в сообщении
    message_text = message.text or ""
    if keywords_pattern.search(message_text):
        # Пересылка сообщения в указанный чат
        await app.forward_messages(notification_chat_id, message.chat.id, message.id)

        # Дополнительное уведомление с информацией о сообщении
        sender = message.from_user.username if message.from_user else "Анонимный пользователь"

        # Информация о чате, откуда пришло сообщение
        chat_title = message.chat.title if message.chat.title else "Личное сообщение"
        chat_link = f"https://t.me/{message.chat.username}" if message.chat.username else "Ссылка недоступна"

        notification_text = (
            f"Сообщение из чата: {chat_title}\n"
            f"Ссылка на чат: {chat_link}\n"
            f"Отправитель: @{sender}\n"
            f"Текст сообщения: {message_text}"
        )

        await app.send_message(notification_chat_id, notification_text)


async def main():
    # Присоединение к группе только если еще не являемся ее участником
    try:
        await app.start()
        chat = await app.get_chat(group_username)

        # Проверка, является ли пользователь участником
        if not chat.is_member:
            await app.join_chat(group_username)
            print(f"Успешно присоединились к группе {group_username}.")
        else:
            print(f"Уже состоим в группе {group_username}.")

    except Exception as e:
        print(f"Ошибка при присоединении к группе {group_username}: {e}")

    # Ожидание завершения
    await asyncio.Event().wait()


if __name__ == '__main__':
    app.run(main())
