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
@app.on_message()
async def forward_to_channel(client, message: Message):
    # Проверяем, есть ли текст в сообщении и содержит ли оно ключевые слова
    if message.text and any(keyword.lower() in message.text.lower() for keyword in keywords):
        await message.forward(target_channel_id)

# Запуск бота
app.run()
