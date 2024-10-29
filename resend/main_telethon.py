from pyrogram import Client, filters
from pyrogram.types import Message

# Указываем API ID и API Hash
api_id = 21564722
api_hash = 'a37810f1f9432966784ac36e1df673bd'

# ID канала, в который будут пересылаться сообщения
target_channel_id = -1002476481274

# Список ключевых слов для фильтрации сообщений
keywords = ["фулфилмент", "прайс", "расценки", "доставка"]

# Инициализируем клиент
app = Client("my_account", api_id=api_id, api_hash=api_hash)


# Обработчик сообщений для пересылки в канал при наличии ключевых слов
@app.on_message(filters.text)
async def forward_to_channel(client: Client, message: Message):
    # Проверяем, есть ли текст в сообщении и содержит ли оно ключевые слова
    if any(keyword.lower() in message.text.lower() for keyword in keywords):
        # Получаем информацию о чате, отправителе и тексте сообщения
        chat_title = message.chat.title or "Без названия"  # Название чата
        chat_link = await client.export_chat_invite_link(message.chat.id) if message.chat.type in ["supergroup",
                                                                                                   "channel"] else "Прямая ссылка не доступна"
        sender_username = f"@{message.from_user.username}" if message.from_user.username else "Без никнейма"

        # Формируем текст сообщения для пересылки
        formatted_message = (
            f"Сообщение из чата: {chat_title}\n"
            f"Ссылка на чат: {chat_link}\n"
            f"Отправитель: {sender_username}\n"
            f"Текст сообщения: {message.text}"
        )

        # Отправляем сформированное сообщение в указанный канал
        await app.send_message(target_channel_id, formatted_message)


# Запуск бота
app.run()
